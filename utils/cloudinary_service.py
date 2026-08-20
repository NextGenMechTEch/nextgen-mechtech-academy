"""
Centralized Cloudinary storage service.

Every file the app previously stored as a base64 blob directly inside a
database column (profile photos, instructor photos, payment screenshots,
certificate PDFs, resumes, CMS media library items) is now uploaded to
Cloudinary instead, and only the secure HTTPS URL Cloudinary returns is
written to that same database column.

No schema changes were required: every column that used to hold base64
text (`Text`) now holds a URL string instead, which is also text.

Credentials are read from environment variables (see `.env.example`):
    CLOUDINARY_CLOUD_NAME
    CLOUDINARY_API_KEY
    CLOUDINARY_API_SECRET
Optionally a single `CLOUDINARY_URL` (cloudinary://key:secret@cloud_name)
is also honored automatically by the Cloudinary SDK if the three
variables above are not set.

This module also provides small helpers (`resolve_src`, `get_file_bytes`)
so that pages can keep rendering/downloading images and documents that
were uploaded *before* this migration (still stored as raw base64) with
zero behavior change, while anything uploaded from now on goes to
Cloudinary and is referenced by URL.
"""
import base64
import mimetypes
import os
import uuid

import cloudinary
import cloudinary.uploader

_CONFIGURED = False


def _ensure_configured():
    """Configure the Cloudinary SDK from environment variables (once)."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    cloudinary_url = os.getenv("CLOUDINARY_URL")

    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
    elif cloudinary_url:
        # cloudinary.config() reads CLOUDINARY_URL from the environment
        # automatically when called with no explicit credentials.
        cloudinary.config(secure=True)
    else:
        raise RuntimeError(
            "Cloudinary is not configured. Set CLOUDINARY_CLOUD_NAME, "
            "CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET (or CLOUDINARY_URL) "
            "as environment variables."
        )
    _CONFIGURED = True


def _resource_type_for(filename: str, default: str = "auto") -> str:
    """Pick the Cloudinary resource_type for a given filename.

    Images -> "image". PDFs/DOCX/other documents -> "raw" (Cloudinary only
    treats a handful of document formats as "image"-derivable; raw is the
    safe choice for arbitrary documents like resumes/certificates so the
    original bytes are preserved exactly).
    """
    ext = os.path.splitext(filename or "")[1].lower().lstrip(".")
    if ext in {"png", "jpg", "jpeg", "gif", "webp", "bmp", "svg"}:
        return "image"
    if ext in {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "csv"}:
        return "raw"
    return default


def upload_bytes(data: bytes, filename: str = "upload", folder: str = "nextgen_mechtech") -> str:
    """Upload raw bytes to Cloudinary and return the resulting secure URL.

    `filename` is used only to pick a resource_type and a friendly
    public_id suffix; Cloudinary does not require it to be unique.
    Raises RuntimeError if Cloudinary env vars are missing, and
    cloudinary.exceptions.Error (propagated) if the upload itself fails.
    """
    _ensure_configured()
    resource_type = _resource_type_for(filename)
    base_name = os.path.splitext(os.path.basename(filename or "upload"))[0] or "upload"
    public_id = f"{base_name}-{uuid.uuid4().hex[:12]}"

    result = cloudinary.uploader.upload(
        data,
        folder=folder,
        public_id=public_id,
        resource_type=resource_type,
        use_filename=False,
        unique_filename=False,
        overwrite=False,
    )
    return result["secure_url"]


def upload_file(uploaded_file, folder: str = "nextgen_mechtech") -> str:
    """Convenience wrapper for a Streamlit `UploadedFile` object.

    Reads its bytes and uploads them, using its reported `name` (if any)
    to infer resource type. Resets the read position first in case the
    caller already peeked at `.size`/`.read()` earlier in the same run.
    """
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    data = uploaded_file.read()
    filename = getattr(uploaded_file, "name", "upload")
    return upload_bytes(data, filename=filename, folder=folder)


def is_url(value) -> bool:
    return bool(value) and isinstance(value, str) and value.startswith(("http://", "https://"))


def resolve_src(value, mime: str = "image/jpeg", width: int = None):
    """Return something usable directly as an <img src="..."> value.

    - Already a Cloudinary (or any) URL -> returned as-is, except Cloudinary
      delivery URLs (res.cloudinary.com/<cloud>/image/upload/...) get an
      f_auto,q_auto transformation inserted automatically — Cloudinary then
      serves the smallest format the requesting browser supports (WebP/AVIF
      where possible) at an auto-tuned quality, with no visible quality loss
      and no change to what's stored in the database. Pass `width` to also
      request a specific delivery width (e.g. thumbnails), capping the
      bytes the browser has to download for a spot that's rendered small.
    - Legacy base64 blob (from before this migration) -> turned into a
      data: URI so old records keep rendering exactly as before.
    - Empty/None -> None.
    """
    if not value:
        return None
    if is_url(value):
        return _cloudinary_optimize(value, width=width)
    return f"data:{mime};base64,{value}"


def _cloudinary_optimize(url: str, width: int = None) -> str:
    """Insert an f_auto,q_auto[,w_<width>] transformation into a Cloudinary
    delivery URL. Non-Cloudinary URLs (e.g. an old externally-hosted image)
    are returned unchanged — this only touches URLs that already contain
    Cloudinary's '/upload/' delivery-path marker.
    """
    marker = "/upload/"
    idx = url.find(marker)
    if idx == -1:
        return url
    transform = "f_auto,q_auto" + (f",w_{width}" if width else "")
    insert_at = idx + len(marker)
    return url[:insert_at] + transform + "/" + url[insert_at:]


def get_file_bytes(value) -> bytes:
    """Return the raw bytes for a stored file reference, for use with
    st.download_button() etc.

    - URL (new Cloudinary uploads) -> fetched over HTTP.
    - Legacy base64 blob -> decoded directly, no network call.
    """
    if not value:
        return b""
    if is_url(value):
        import requests
        resp = requests.get(value, timeout=30)
        resp.raise_for_status()
        return resp.content
    return base64.b64decode(value)
