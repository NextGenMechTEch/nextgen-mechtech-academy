import streamlit as st

from components.icons import icon
from utils.helpers import (
    get_all_settings, html_block, esc,
    extract_youtube_id, build_youtube_embed_url,
)
from utils.cloudinary_service import resolve_src
from database.connection import get_db_session
from database.models import Event


def render_events():
    if "selected_event_id" in st.session_state and st.session_state.selected_event_id:
        _render_event_detail(st.session_state.selected_event_id)
        return
    _render_events_grid()


def _render_events_grid():
    settings = get_all_settings()
    banner_heading = settings.get("events_banner_heading", "Community & Events")
    banner_sub = settings.get(
        "events_banner_sub",
        "Workshops, hackathons, and community meetups we've hosted — and the students who joined us.",
    )

    st.markdown(html_block(f"""
    <div class="nmt-page-banner nmt-page-enter">
      <div class="nmt-page-banner-inner" style="text-align:center;">
        <div class="nmt-page-banner-icon">{icon("award", size=24, color="#fff")}</div>
        <h1>{banner_heading}</h1>
        <p style="text-align:center;max-width:560px;margin:0 auto;">{banner_sub}</p>
      </div>
    </div>
    """), unsafe_allow_html=True)

    st.markdown('<div class="nmt-content">', unsafe_allow_html=True)

    db = get_db_session()
    try:
        db_categories = [
            row[0] for row in
            db.query(Event.category)
              .filter(Event.is_published == True, Event.category.isnot(None), Event.category != "")
              .distinct()
              .all()
        ]
    finally:
        db.close()
    CATS = sorted(db_categories)

    filter_cols = st.columns([2, 1])
    with filter_cols[0]:
        search = st.text_input("Search events", placeholder="Search events by name…", label_visibility="collapsed")
    with filter_cols[1]:
        selected_cat = st.selectbox("Category", ["All Categories"] + CATS, label_visibility="collapsed")

    db = get_db_session()
    try:
        q = db.query(Event).filter(Event.is_published == True)
        if selected_cat != "All Categories":
            q = q.filter(Event.category == selected_cat)
        if search:
            q = q.filter(Event.title.ilike(f"%{search}%"))
        events = q.order_by(Event.is_featured.desc(), Event.display_order, Event.created_at.desc()).all()
    finally:
        db.close()

    if not events:
        st.info("No events found.")
    else:
        st.caption(f"{len(events)} event(s) found")
        cols = st.columns(3, gap="medium")
        for i, ev in enumerate(events):
            with cols[i % 3]:
                cover_src = resolve_src(ev.cover_image, width=400) if ev.cover_image else ""
                thumb = (
                    f'<img src="{esc(cover_src)}" style="width:100%;height:155px;object-fit:cover;border-radius:10px 10px 0 0;" alt="{esc(ev.title)}" onerror="this.style.display=\'none\'">'
                    if cover_src else
                    f'<div style="width:100%;height:155px;border-radius:10px 10px 0 0;background:var(--surface-soft);display:flex;align-items:center;justify-content:center;">{icon("calendar", size=26, color="var(--ink-300)")}</div>'
                )
                featured_badge = f'<div class="nmt-badge-featured">{icon("star", size=11)} Featured</div>' if ev.is_featured else ""
                date_str = ev.event_date.strftime("%b %d, %Y") if ev.event_date else ""
                meta_bits = [b for b in [date_str, ev.location] if b]
                meta_line = f'<div class="nmt-card-meta">{esc(" · ".join(meta_bits))}</div>' if meta_bits else ""
                part_html = (
                    f'<span style="font-size:10.5px;background:var(--success-bg);color:var(--success-tx);'
                    f'padding:2px 8px;border-radius:20px;font-weight:600;display:inline-flex;align-items:center;gap:4px;">'
                    f'{icon("users", size=10)} {ev.participants_count} Participants</span>'
                    if ev.participants_count else ""
                )
                desc = ev.short_description or ""
                desc_short = desc[:90].rsplit(" ", 1)[0].rstrip(",.;:") + "…" if len(desc) > 90 else desc

                card_html = (
                    f'<div class="nmt-card" style="animation-delay:{i*0.06}s;">{thumb}'
                    f'<div style="padding:18px 18px 14px;">{featured_badge}'
                    f'<div style="font-size:11px;font-weight:700;color:var(--blue-600);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">{esc(ev.category or "")}</div>'
                    f'<div class="nmt-card-title">{esc(ev.title)}</div>'
                    f'{meta_line}'
                    f'{f"<div style=\'margin:2px 0 10px;\'>{part_html}</div>" if part_html else ""}'
                    f'<div class="nmt-card-desc">{esc(desc_short)}</div></div></div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)
                if st.button("View Event Details", key=f"view_ev_{ev.id}", use_container_width=True, type="primary"):
                    st.session_state.selected_event_id = ev.id
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _render_event_detail(event_id: int):
    db = get_db_session()
    try:
        ev = db.query(Event).filter(Event.id == event_id).first()
        if not ev:
            st.error("Event not found.")
            if st.button("← Back to Events"):
                st.session_state.selected_event_id = None
                st.rerun()
            return
        # Detach plain values before closing the session so nothing here
        # touches a closed SQLAlchemy session after `finally`.
        data = {
            "id": ev.id, "title": ev.title, "category": ev.category,
            "event_date": ev.event_date, "event_time": ev.event_time,
            "location": ev.location, "participants_count": ev.participants_count,
            "host_name": ev.host_name, "short_description": ev.short_description,
            "full_description": ev.full_description, "cover_image": ev.cover_image,
            "gallery_images": ev.gallery_images or [], "youtube_url": ev.youtube_url,
        }
    finally:
        db.close()

    if st.button("← All Events", key="back_to_events"):
        st.session_state.selected_event_id = None
        st.rerun()

    banner_url = resolve_src(data["cover_image"], width=1200) if data["cover_image"] else ""
    if banner_url:
        st.markdown(
            f'<img src="{esc(banner_url)}" style="width:100%;max-height:340px;object-fit:cover;'
            f'border-radius:var(--radius-lg);margin-bottom:24px;" alt="{esc(data["title"])}">',
            unsafe_allow_html=True,
        )

    cat_html = (
        f'<div style="font-size:11.5px;font-weight:700;color:var(--blue-600);text-transform:uppercase;'
        f'letter-spacing:0.06em;margin-bottom:8px;">{esc(data["category"])}</div>'
        if data["category"] else ""
    )
    st.markdown(html_block(f"""
    <div class="nmt-page-enter">
      {cat_html}
      <h1 style="font-family:var(--font-head);font-size:28px;font-weight:800;color:var(--ink-900);margin:0 0 12px;">{esc(data["title"])}</h1>
    </div>
    """), unsafe_allow_html=True)

    # Meta tags row — only the fields that were actually filled in are shown.
    meta_items = []
    if data["event_date"]:
        meta_items.append(("calendar", data["event_date"].strftime("%b %d, %Y")))
    if data["event_time"]:
        meta_items.append(("clock", data["event_time"]))
    if data["location"]:
        meta_items.append(("map-pin", data["location"]))
    if data["participants_count"]:
        meta_items.append(("users", f'{data["participants_count"]} Participants'))
    if data["host_name"]:
        meta_items.append(("user", f'Hosted by {data["host_name"]}'))
    if meta_items:
        meta_html = "".join(
            f'<span style="display:inline-flex;align-items:center;gap:5px;background:var(--surface-soft);'
            f'border:1px solid var(--line);border-radius:20px;padding:5px 12px;font-size:12.5px;color:var(--ink-700);font-weight:500;">'
            f'{icon(ic, size=12)} {esc(val)}</span>'
            for ic, val in meta_items
        )
        st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;">{meta_html}</div>', unsafe_allow_html=True)

    if data["short_description"]:
        st.markdown(
            f'<p style="color:var(--ink-500);font-size:15px;line-height:1.75;margin-bottom:20px;">{esc(data["short_description"])}</p>',
            unsafe_allow_html=True,
        )

    if data["full_description"]:
        st.markdown(html_block(f"""
        <div style="background:var(--surface-soft);border-radius:var(--radius-md);padding:22px;border:1px solid var(--line);margin-bottom:28px;">
          <h3 style="font-family:var(--font-head);font-size:16px;font-weight:700;color:var(--ink-900);margin-bottom:10px;">{icon("info", size=15)} About This Event</h3>
          <p style="color:var(--ink-700);font-size:13.5px;line-height:1.8;white-space:pre-wrap;">{esc(data["full_description"])}</p>
        </div>
        """), unsafe_allow_html=True)

    # YouTube video — hidden entirely if no valid URL was configured.
    video_id = extract_youtube_id(data["youtube_url"]) if data["youtube_url"] else None
    if video_id:
        embed_url = build_youtube_embed_url(video_id, autoplay=False, muted=False, loop=False, controls=True)
        st.markdown(html_block(f"""
        <div style="margin-bottom:28px;">
          <h3 style="font-family:var(--font-head);font-size:16px;font-weight:700;color:var(--ink-900);margin-bottom:12px;">{icon("youtube", size=15)} Event Video</h3>
          <div style="position:relative;width:100%;padding-top:56.25%;border-radius:var(--radius-md);overflow:hidden;background:#000;">
            <iframe src="{embed_url}" style="position:absolute;inset:0;width:100%;height:100%;border:0;"
              allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture"
              allowfullscreen loading="lazy"></iframe>
          </div>
        </div>
        """), unsafe_allow_html=True)

    # Gallery — a CSS-only lightbox (no JS anywhere else in this app, so this
    # matches convention): each thumbnail links to a fixed-position overlay
    # keyed by URL fragment (:target), and the close link returns to an
    # anchor placed right above the grid so the page doesn't jump to the top.
    gallery = [u for u in data["gallery_images"] if u][:12]
    if gallery:
        anchor_id = f"event-gallery-{data['id']}"
        thumbs_html = "".join(
            f'<a href="#event-img-{data["id"]}-{i}" class="nmt-lightbox-thumb">'
            f'<img src="{esc(resolve_src(u, width=300))}" alt="{esc(data["title"])} photo {i+1}"></a>'
            for i, u in enumerate(gallery)
        )
        overlays_html = "".join(
            f'<div class="nmt-lightbox-overlay" id="event-img-{data["id"]}-{i}">'
            f'<a href="#{anchor_id}" class="nmt-lightbox-close" aria-label="Close">&times;</a>'
            f'<img src="{esc(resolve_src(u, width=1200))}" alt="{esc(data["title"])} photo {i+1}"></div>'
            for i, u in enumerate(gallery)
        )
        st.markdown(html_block(f"""
        <div style="margin-bottom:28px;">
          <span id="{anchor_id}"></span>
          <h3 style="font-family:var(--font-head);font-size:16px;font-weight:700;color:var(--ink-900);margin-bottom:12px;">{icon("image", size=15)} Gallery</h3>
          <div class="nmt-lightbox-grid">{thumbs_html}</div>
        </div>
        {overlays_html}
        """), unsafe_allow_html=True)
