# NextGen MechTech Academy — v2 Upgraded

## What Was Upgraded (No Logic Broken)

### ✅ Website CMS (NEW — Highest Priority)
A full **Website CMS** module has been added to the Admin Panel under the **"Website CMS"** tab. Every website page now has its own management section:

| Page | What's Editable |
|------|----------------|
| **Home Page** | Hero headline, sub-text, badge text, buttons, stats counters & labels, announcement bar, featured courses heading/count, categories, why-choose-us cards (JSON), instructor section, testimonials (JSON), FAQ (JSON), CTA section, newsletter section |
| **About Page** | Banner, eyebrow, heading, paragraphs 1 & 2, mission/vision/values (JSON), quick facts (4 values + labels), team section heading, CTA |
| **Courses Page** | Banner, grid heading, empty state message, category labels (JSON) |
| **Career Page** | Banner, section heading/sub-text, perks/benefits (JSON), **job openings** (create/toggle/archive/delete), **internship opportunities** (create/toggle/delete), form heading/sub-text/success message |
| **Certificate Page** | Banner, form heading, placeholder, success message, error message, help text |
| **Contact Page** | Banner, section heading, contact details (email/phone/address/hours/map embed), social links, form heading/button |
| **Navigation Bar** | Add/edit/remove/reorder/show-hide nav items — no hardcoded menu items |
| **Media Library** | Upload images/PDFs/logos, browse by folder, delete — reusable across pages |
| **Footer** | Site name, tagline, description, quick links (JSON), contact info, social links, copyright |

### ✅ Individual Course Detail Pages (NEW)
Clicking "View Details" on any course now opens a full professional detail page with:
- Course banner image, meta tags (duration, level, language, category)
- Full description, "What You'll Learn" checklist
- Syllabus & modules (JSON-driven, auto-updated when admin edits)
- Skills learned (tag cloud), Prerequisites warning box
- Software used & projects included (side-by-side)
- Instructor profile card (sidebar)
- Enrollment button (login-aware)
- FAQs accordion
- Related courses section

### ✅ Roles & Permissions (NEW)
New **"Roles & Perms"** tab in Admin Panel:
- View all staff (admins, instructors, content managers)
- Change role with dropdown
- Enable/disable account
- Set custom permissions JSON per user
- Permission matrix table showing what each role can access
- Create new staff accounts directly from admin

### ✅ Premium Animations Added
- Glassmorphism cards (`.nmt-glass`)
- Staggered fade-in for grid sections (`.nmt-stagger`)
- Animated gradient on hero headline `<em>` text
- Pop-in animation for stat counters
- Testimonial cards with quote mark decoration
- Enhanced course card hover (lift + overlay glow)
- CTA section animated gradient background
- Job opening cards with slide-right hover
- Announcement bar slide-in
- Form focus glow (blue ring on inputs)
- Smooth page entry animation (`.nmt-page-enter`)
- Loading skeleton CSS class available

### ✅ New Database Tables (Auto-migrated)
- `cms_sections` — page/section content & visibility
- `media_library` — central file storage
- `job_openings` — career page jobs & internships
- `nav_items` — dynamic navigation menu

### ✅ New Course Fields (Auto-migrated)
- `language`, `enrollment_open`, `skills_learned`, `syllabus`, `software_used`, `projects_included`

### ✅ CMS-Driven Pages
All pages now read content from the database (via `WebsiteSettings` and `CmsSection`) with sensible hardcoded fallbacks. **No source code ever needs editing to update content.**

---

## Running

```bash
pip install -r requirements.txt
streamlit run app.py
```

First login: use super_admin credentials from the original database (unchanged).

## Admin Panel Quick Start

1. Go to **Admin Panel → Website CMS**
2. Pick any page tab and start editing
3. Hit "Save" — changes are live immediately
4. For navigation, go to **Navigation Bar → Seed Default Navigation** (first time only)
5. For jobs, go to **Career Page → Job Openings → Create New Job Opening**
6. For media, go to **Media Library → Upload Media**

---

## File Structure (New Files)

```
pages/
  cms_admin.py          ← NEW: Full Website CMS module
  home.py               ← UPGRADED: CMS-driven
  courses.py            ← UPGRADED: CMS-driven + course detail pages
  about.py              ← UPGRADED: CMS-driven
  contact.py            ← UPGRADED: CMS-driven
  careers.py            ← UPGRADED: CMS-driven + job openings
  verify.py             ← UPGRADED: CMS-driven
  admin.py              ← UPGRADED: +Website CMS tab, +Roles & Perms tab, +new course fields
  
components/
  navbar.py             ← UPGRADED: DB-driven nav items + dynamic footer
  styles.py             ← UPGRADED: Premium animations + glassmorphism + new CSS classes

database/
  models.py             ← UPGRADED: CmsSection, MediaLibrary, JobOpening, NavItem models
  migrate.py            ← UPGRADED: Auto-creates new tables + new course columns
```

All original logic — auth, registrations, certificates, email templates, student dashboard, email delivery (now via Brevo) — is **100% preserved**.

---

## Deploying to Render

This project ships fully configured for [Render](https://render.com). See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for the complete step-by-step guide and the full list of required environment variables.
