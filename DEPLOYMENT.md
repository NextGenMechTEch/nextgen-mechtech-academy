# Deployment Guide — Render

This project is pre-configured to deploy on Render with **zero code changes**.
Nothing about the app's logic, UI, routing, or authentication flow was
touched — only the files below were added for deployment:

| File | Purpose |
|---|---|
| `Procfile` | Tells Render how to start the app |
| `render.yaml` | Optional one-click "Blueprint" — provisions the service and lists every env var Render should ask you for |
| `.streamlit/config.toml` | Production server settings (headless mode, proxy-friendly CORS, upload size) |
| `runtime.txt` | Pins the Python version Render builds with |
| `.env.example` | Template of every environment variable the app reads (already existed — only the header comment was expanded) |

The original `.env` (which only ever held blank placeholder values, no real
secrets) was renamed to `.env.example`. **Never upload a real `.env` file to
Render.** — set real values as Environment Variables in the dashboard instead.

---

## Option A — One-click Blueprint deploy

1. Push this project to a GitHub/GitLab repo.
2. In Render: **New +** → **Blueprint** → select the repo.
3. Render reads `render.yaml` and creates the web service automatically.
4. Fill in the prompted secret values (Render shows a form for every
   `sync: false` variable in `render.yaml`).
5. Click **Apply** — Render builds and deploys.

## Option B — Manual web service

1. In Render: **New +** → **Web Service** → connect your repo.
2. Runtime: **Python 3**.
3. **Build Command:**
   ```
   pip install -r requirements.txt
   ```
4. **Start Command:**
   ```
   streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false
   ```
5. **Health Check Path:** `/_stcore/health`
6. Add the environment variables listed below under **Environment**.
7. Click **Create Web Service**.

---

## Required Environment Variables

Set these in Render Dashboard → your service → **Environment**. Names and
behavior are unchanged from the app's existing `.env` handling — Render just
supplies them as real process env vars instead of a `.env` file.

### App
| Variable | Required | Notes |
|---|---|---|
| `APP_URL` | Yes | Set to your live Render URL once known, e.g. `https://your-service.onrender.com`. Used in email links (verification, password reset). |

### Database — Supabase (PostgreSQL)
| Variable | Required | Notes |
|---|---|---|
| `DATABASE_URL` | Recommended | Supabase → Project Settings → Database → Connection string (URI). Use the **Session pooler** or **Transaction pooler** string. Leave unset to fall back to local SQLite (not persistent on Render — see note below). |
| `DATABASE_SSLMODE` | No | Defaults to `require`. |
| `DATABASE_POOL_RECYCLE` | No | Defaults to `300` seconds. |
| `DATABASE_POOL_SIZE` | No | Defaults to `5`. |
| `DATABASE_MAX_OVERFLOW` | No | Defaults to `10`. |

> ⚠️ **Persistence note:** Render's filesystem is ephemeral — anything
> written to local disk (including the fallback SQLite file in `data/`) is
> lost on every redeploy or restart. Set `DATABASE_URL` to your Supabase
> connection string for any real deployment.

### Email — Brevo (transactional API)
| Variable | Required | Notes |
|---|---|---|
| `BREVO_API_KEY` | Yes | app.brevo.com → SMTP & API → API Keys |
| `BREVO_SENDER_EMAIL` | Yes | Must be a verified sender in your Brevo account |
| `BREVO_SENDER_NAME` | No | Display name for outgoing emails |
| `ADMIN_EMAIL` | Yes | Receives admin notifications (registrations, contact messages, etc.) |
| `CAREERS_EMAIL` | No | Receives career/tutor applications; defaults to `ADMIN_EMAIL` |
| `SUPPORT_EMAIL` | No | Shown as support contact in email footers; defaults to `BREVO_SENDER_EMAIL` |

### File Storage — Cloudinary
| Variable | Required | Notes |
|---|---|---|
| `CLOUDINARY_CLOUD_NAME` | Yes* | Cloudinary Dashboard → Account Details |
| `CLOUDINARY_API_KEY` | Yes* | Cloudinary Dashboard → Account Details |
| `CLOUDINARY_API_SECRET` | Yes* | Cloudinary Dashboard → Account Details |
| `CLOUDINARY_URL` | Alternative* | Single combined variable (`cloudinary://<api_key>:<api_secret>@<cloud_name>`) — use this **instead of** the three above if you prefer |

\* Provide either the three separate variables or the single `CLOUDINARY_URL`.

---

## Post-deploy checklist

1. Confirm the service is live at your `*.onrender.com` URL.
2. Update `APP_URL` to that exact URL and redeploy (or trigger "Restart") so
   email links point to production, not `localhost`.
3. Log in with the seeded super-admin account created on first startup:
   - Email: `support.nextgenmechtech@gmail.com`
   - Password: `Admin@123`
   - **Change this password immediately after first login.**
4. Send a test contact-form or registration email to confirm Brevo delivery.
5. Upload a test image (e.g. a course thumbnail) to confirm Cloudinary is
   configured correctly.
6. If using Supabase, verify tables were created — the app runs its own
   migrations and table creation automatically on startup (`database/init_db.py`
   via `app.py`), no manual SQL needed.

---

## Notes on what was (and wasn't) changed

- **No business logic, UI, authentication flow, database models, or routing
  were modified.**
- Only deployment-facing files were added: `Procfile`, `render.yaml`,
  `.streamlit/config.toml`, `runtime.txt`, this guide, and an expanded
  comment header in `.env.example`.
- `requirements.txt` was left exactly as-is — it already contains everything
  the app imports.
- The existing `database/connection.py` already normalizes `postgres://` →
  `postgresql://` and defaults to SSL for Supabase, so no changes were
  needed there either.
