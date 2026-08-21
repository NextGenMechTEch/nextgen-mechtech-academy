"""
Single source of truth for all visual styling across the app.

Design system summary
----------------------
Palette:    deep navy/blue primary (#0F2D6B family) + amber/orange accent (#F59E0B family)
Typography: 'Sora' for display/headings, 'Inter' for body text
Surfaces:   white cards on a soft slate background, 1px hairline borders, soft shadows
Radius:     8 / 12 / 16 / 24px scale
Icons:      SVG only (components/icons.py) — no emoji is used anywhere in the UI

This file is the ONLY place page-wide CSS should live. Page modules should
reuse these classes instead of writing new inline styles or page-local
<style> blocks, so the product looks like one coherent app rather than a
collage of separately designed screens.
"""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Sora:wght@400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body { overflow-x: hidden; max-width: 100%; }

/* Tell mobile browsers (Android Chrome/Samsung Internet "force dark" /
   auto-darken-websites) that this page is light-only, so they stop
   heuristically inverting colors. Without this, elements with an explicit
   !important text color (like the tab labels below) can end up inverted
   out of sync with their background, rendering as near-invisible ghost
   text on some phones even though everything is correct on desktop. */
:root, html { color-scheme: light only; }

:root {
  /* Brand */
  --navy-950: #0A1A3F;
  --navy-900: #0F2D6B;
  --navy-800: #15399A;
  --blue-600: #2056D6;
  --blue-500: #3B6FE8;
  --blue-100: #DCE6FB;
  --blue-50:  #F1F5FD;

  --amber-600: #D97706;
  --amber-500: #F59E0B;
  --amber-400: #FBBF24;
  --amber-100: #FEF1D6;

  /* Neutrals */
  --ink-900: #0E1726;
  --ink-700: #3C4759;
  --ink-500: #67748B;
  --ink-300: #B6C0CF;
  --line:    #E3E8F0;
  --line-soft: #EEF1F6;
  --surface: #FFFFFF;
  --surface-soft: #F6F8FB;
  --surface-tint: #F8FAFD;

  /* Semantic */
  --success-bg: #E7F6EC; --success-tx: #15803D; --success-line:#BBE6C9;
  --warning-bg: #FEF3E2; --warning-tx: #B45309; --warning-line:#FBDFAE;
  --danger-bg:  #FCEAEA; --danger-tx:  #B91C1C; --danger-line:#F5C5C5;
  --info-bg:    #E9F0FE; --info-tx:    #1D4ED8; --info-line: #C9DAFB;

  /* Elevation */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 22px;
  --shadow-xs: 0 1px 2px rgba(15,23,42,0.05);
  --shadow-sm: 0 2px 8px rgba(15,23,42,0.06);
  --shadow-md: 0 8px 24px rgba(15,23,42,0.08);
  --shadow-lg: 0 18px 48px rgba(15,23,42,0.14);

  --font-body: 'Inter', -apple-system, sans-serif;
  --font-head: 'Sora', -apple-system, sans-serif;
}

/* ───────────────────── Streamlit chrome resets ───────────────────── */
html, body, .stApp { font-family: var(--font-body) !important; background-color: var(--surface) !important; color: var(--ink-900); }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
div[data-testid="stMarkdownContainer"] p { margin: 0; }
div[data-testid="column"] { padding: 6px 8px !important; }
hr { border-color: var(--line) !important; }
html { scroll-behavior: smooth; }

/* Buttons rendered by st.button / st.form_submit_button */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  font-family: var(--font-body) !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  border-radius: var(--radius-sm) !important;
  border: 1.5px solid var(--line) !important;
  color: var(--ink-700) !important;
  background: var(--surface) !important;
  transition: all .15s ease !important;
  padding: 0.5rem 1rem !important;
}
.stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--blue-500) !important; color: var(--blue-600) !important; }

.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
  background: var(--navy-900) !important;
  border-color: var(--navy-900) !important;
  color: #fff !important;
  box-shadow: var(--shadow-xs);
}
.stButton > button[kind="primary"]:hover { background: var(--blue-600) !important; border-color: var(--blue-600) !important; }

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
.stSelectbox > div > div,
div[data-baseweb="select"] > div {
  font-family: var(--font-body) !important;
  border-radius: var(--radius-sm) !important;
  border: 1.5px solid var(--line) !important;
  font-size: 14px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--blue-500) !important;
  box-shadow: 0 0 0 3px var(--blue-100) !important;
}
label[data-testid="stWidgetLabel"] p { font-weight: 600 !important; font-size: 13px !important; color: var(--ink-700) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1.5px solid var(--line); background: var(--surface) !important; }
.stTabs [data-baseweb="tab"],
.stTabs [data-baseweb="tab"] *,
.stTabs [data-baseweb="tab"] p {
  font-family: var(--font-body); font-weight: 600; font-size: 13.5px; color: var(--ink-500) !important;
  padding: 10px 16px; border-radius: 0; background: transparent !important;
}
.stTabs [aria-selected="true"],
.stTabs [aria-selected="true"] *,
.stTabs [aria-selected="true"] p { color: var(--blue-600) !important; border-bottom-color: var(--blue-600) !important; }
/* Expander */
.streamlit-expanderHeader, [data-testid="stExpander"] summary {
  font-family: var(--font-body) !important; font-weight: 600 !important;
  border-radius: var(--radius-sm) !important; border: 1.5px solid var(--line) !important;
}

/* Alerts */
div[data-testid="stAlert"] { border-radius: var(--radius-sm) !important; font-size: 13.5px !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border: 1.5px solid var(--line); border-radius: var(--radius-md); overflow: hidden; }

/* ───────────────────── Layout primitives ───────────────────── */
.nmt-shell { max-width: 1180px; margin: 0 auto; padding: 0 24px; }
.nmt-section { padding: 72px 0; }
.nmt-section.tight { padding: 48px 0; }
.nmt-section.soft { background: var(--surface-soft); }

.nmt-eyebrow {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11.5px; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase;
  color: var(--amber-600); margin-bottom: 10px; font-family: var(--font-body);
}
.nmt-h2 {
  font-family: var(--font-head); font-weight: 700;
  font-size: clamp(24px, 3vw, 34px); color: var(--ink-900); letter-spacing: -0.01em;
  margin: 0 0 10px; line-height: 1.22;
}
.nmt-sub { font-size: 15px; color: var(--ink-500); line-height: 1.7; max-width: 560px; margin: 0; }
.nmt-section-head { margin-bottom: 40px; }
.nmt-section-head.center { text-align: center; }
.nmt-section-head.center .nmt-sub { margin: 0 auto; }

/* ───────────────────── Navbar ───────────────────── */
.nmt-navbar {
  position: sticky; top: 0; z-index: 999;
  background: rgba(255,255,255,0.92); backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--line);
}
.nmt-navbar-inner {
  max-width: 1180px; margin: 0 auto; padding: 0 24px;
  display: flex; align-items: center; gap: 8px; height: 60px;
}
.nmt-brand { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.nmt-brand img { height: 32px; width: 32px; border-radius: 7px; object-fit: cover; }
.nmt-brand-mark {
  height: 32px; width: 32px; border-radius: 7px; background: linear-gradient(135deg, var(--navy-900), var(--blue-600));
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-head); font-weight: 800; font-size: 12px; color: #fff;
}
.nmt-brand-text { font-family: var(--font-head); font-weight: 700; font-size: 15px; color: var(--ink-900); line-height: 1.15; }
.nmt-brand-text small { display: block; font-size: 9.5px; font-weight: 600; letter-spacing: 0.1em; color: var(--amber-600); text-transform: uppercase; }

/* Actual classes emitted by components/navbar.py — previously had no
   matching rules above, which left the brand strip fully unstyled. */
.st-key-nmt_navbar { position: sticky; top: 0; z-index: 999; }
.st-key-nmt_navbar > div { background: rgba(255,255,255,0.94); backdrop-filter: blur(10px); border-bottom: 1px solid var(--line); }
.nmt-nav-inner {
  max-width: 1180px; margin: 0 auto; padding: 14px 24px 6px;
  display: flex; align-items: center; gap: 8px;
}
.nmt-nav-brand { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.nmt-nav-brand img { border-radius: 7px; object-fit: cover; }
.nmt-nav-brand-text { font-family: var(--font-head); font-weight: 700; font-size: 15px; color: var(--ink-900); }
.nmt-nav-links-placeholder { display: none; }

/* The st.columns() row of nav buttons rendered directly beneath the brand
   strip, inside the same sticky container/key so it reads as one navbar. */
.st-key-nmt_navbar div[data-testid="stHorizontalBlock"] {
  max-width: 1180px; margin: 0 auto; padding: 2px 24px 10px; gap: 6px !important;
}
.st-key-nmt_navbar .stButton > button {
  border: none !important; font-size: 13.5px !important; padding: 0.45rem 0.7rem !important;
  background: transparent !important; color: var(--ink-700) !important;
}
.st-key-nmt_navbar .stButton > button:hover { background: var(--blue-50) !important; color: var(--blue-600) !important; }
.st-key-nmt_navbar .stButton > button[kind="primary"] {
  background: var(--blue-50) !important; color: var(--navy-900) !important; border: none !important; box-shadow: none !important;
}
.st-key-nmt_navbar .stButton > button[kind="primary"]:hover { background: var(--blue-100) !important; }

@media (max-width: 900px) {
  .st-key-nmt_navbar div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important; overflow-x: auto; -webkit-overflow-scrolling: touch;
    justify-content: flex-start !important; padding-bottom: 10px;
    scroll-behavior: auto;
  }
  .st-key-nmt_navbar div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    flex: 0 0 auto !important; width: auto !important; min-width: fit-content;
  }
  /* First column is an unused spacer (ratio 2, no button placed in it) that only
     exists to indent the row on desktop — on mobile it becomes an empty scroll
     item that pushes every real nav button off the initial screen, so drop it.
     display:none alone isn't always enough if another rule above still hands it
     width/flex — force width and flex-basis to 0 too so no gap can survive. */
  .st-key-nmt_navbar div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child {
    display: none !important;
    width: 0 !important;
    min-width: 0 !important;
    flex-basis: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
  }
  .st-key-nmt_navbar .stButton > button { white-space: nowrap; }
  .nmt-nav-inner { padding: 12px 16px 4px; }
}

/* ───────────────────── Hero ───────────────────── */
.nmt-hero {
  background: radial-gradient(ellipse 90% 100% at 80% 0%, rgba(59,111,232,0.25) 0%, transparent 55%),
              linear-gradient(150deg, var(--navy-950) 0%, var(--navy-900) 55%, var(--blue-600) 120%);
  padding: 88px 0 0;
  position: relative;
  overflow: hidden;
}
.nmt-hero-inner { max-width: 1180px; margin: 0 auto; padding: 0 24px 64px; position: relative; z-index: 1; }
.nmt-hero-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.18);
  padding: 6px 14px 6px 10px; border-radius: 999px; font-size: 12.5px; font-weight: 600;
  color: rgba(255,255,255,0.88); margin-bottom: 26px;
}
.nmt-hero-badge .tag { background: var(--amber-500); color: var(--navy-950); font-size: 10.5px; font-weight: 800;
  letter-spacing: 0.04em; padding: 2px 8px; border-radius: 999px; text-transform: uppercase; }
.nmt-hero h1 {
  font-family: var(--font-head); font-weight: 800;
  font-size: clamp(32px, 4.6vw, 52px); color: #fff; line-height: 1.14; letter-spacing: -0.015em;
  margin: 0 0 20px; max-width: 680px;
}
.nmt-hero h1 em { color: var(--amber-400); font-style: normal; }
.nmt-hero-sub { font-size: 16.5px; line-height: 1.75; color: rgba(255,255,255,0.72); max-width: 540px; margin: 0 0 38px; }
.nmt-hero-stats { display: flex; gap: 0; margin-top: 52px; flex-wrap: wrap; }
.nmt-hero-stat { padding-right: 36px; margin-right: 36px; border-right: 1px solid rgba(255,255,255,0.16); }
.nmt-hero-stat:last-child { border-right: none; margin-right: 0; padding-right: 0; }
.nmt-hero-stat .v { font-family: var(--font-head); font-size: 30px; font-weight: 800; color: #fff; line-height: 1; }
.nmt-hero-stat .l { font-size: 11.5px; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase; color: rgba(255,255,255,0.48); margin-top: 6px; }

/* Hero promo video — fills the empty right side next to the headline when enabled */
.nmt-hero-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px 48px; align-items: center; }
.nmt-hero-content { min-width: 0; }
.nmt-hero-content .nmt-hero-sub { margin-bottom: 0; }
.nmt-hero-media { min-width: 0; transform: translateY(6px); } /* optical nudge: balances against the badge's extra top space in the text column */
.nmt-hero-video-frame {
  position: relative; width: 92%; border-radius: var(--radius-xl); overflow: hidden;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.14);
  box-shadow: 0 20px 50px rgba(0,0,0,0.35);
}
.nmt-hero-video-frame::before { content: ""; display: block; padding-top: 56.25%; } /* forces 16:9 */
.nmt-hero-video-frame iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
a.nmt-hero-video-watch {
  display: inline-flex; align-items: center; gap: 7px; margin-top: 16px;
  padding: 8px 16px; border-radius: 999px;
  background: #FF0000 !important; border: 1px solid #FF0000;
  font-size: 12.5px; font-weight: 700; color: #fff !important;
  text-decoration: none !important; box-shadow: 0 6px 16px rgba(255,0,0,0.28);
  transition: background .15s ease, transform .15s ease, box-shadow .15s ease;
}
a.nmt-hero-video-watch:hover { background: #e00000 !important; transform: translateY(-2px); box-shadow: 0 10px 22px rgba(255,0,0,0.4); }
.nmt-hero-video-watch:focus-visible { outline: 2px solid var(--amber-400); outline-offset: 3px; border-radius: 4px; }

/* ───────────────────── Buttons (custom, for marketing sections) ───────────────────── */
.nmt-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  font-family: var(--font-body); font-weight: 600; font-size: 14.5px;
  padding: 12px 24px; border-radius: var(--radius-sm); border: 1.5px solid transparent;
  cursor: pointer; text-decoration: none; transition: all .15s ease; white-space: nowrap;
}
.nmt-btn-amber { background: var(--amber-500); color: var(--navy-950); }
.nmt-btn-amber:hover { background: var(--amber-400); }
.nmt-btn-light-outline { background: rgba(255,255,255,0.06); color: #fff; border-color: rgba(255,255,255,0.3); }
.nmt-btn-light-outline:hover { background: rgba(255,255,255,0.14); border-color: rgba(255,255,255,0.5); }
.nmt-btn-navy { background: var(--navy-900); color: #fff; }
.nmt-btn-navy:hover { background: var(--blue-600); }
.nmt-btn-outline { background: var(--surface); color: var(--ink-700); border-color: var(--line); }
.nmt-btn-outline:hover { border-color: var(--blue-500); color: var(--blue-600); }

/* ───────────────────── Cards: courses ───────────────────── */
.nmt-card {
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-lg);
  overflow: hidden; transition: all .2s ease; height: 100%;
}
.nmt-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); border-color: var(--blue-100); }
.nmt-card-img { width: 100%; height: 168px; object-fit: cover; display: block; background: var(--surface-soft); }
.nmt-card-img-fallback {
  width: 100%; height: 168px; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, var(--navy-900), var(--blue-600));
}
.nmt-card-body { padding: 18px 20px 20px; }
.nmt-card-cat { font-size: 10.5px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--blue-600); margin-bottom: 8px; }
.nmt-card-title { font-family: var(--font-head); font-size: 15.5px; font-weight: 700; color: var(--ink-900); line-height: 1.35; margin-bottom: 8px; min-height: 42px; }
.nmt-card-desc { font-size: 12.5px; color: var(--ink-500); line-height: 1.6; margin-bottom: 14px; }
.nmt-card-meta { display: flex; gap: 14px; font-size: 12px; color: var(--ink-500); margin-bottom: 14px; }
.nmt-card-meta span { display: inline-flex; align-items: center; gap: 5px; }
.nmt-card-foot { display: flex; align-items: center; justify-content: space-between; padding-top: 12px; border-top: 1px solid var(--line-soft); }
.nmt-card-price { font-family: var(--font-head); font-size: 16.5px; font-weight: 700; color: var(--ink-900); }
.nmt-card-price small { font-size: 11.5px; font-weight: 500; color: var(--ink-500); }

/* ───────────────────── Category cards ───────────────────── */
.nmt-cat-card {
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-md);
  padding: 26px 18px; text-align: center; transition: all .18s ease;
}
.nmt-cat-card:hover { border-color: var(--blue-500); box-shadow: var(--shadow-sm); transform: translateY(-2px); }
.nmt-cat-icon {
  width: 44px; height: 44px; border-radius: var(--radius-sm); background: var(--blue-50);
  display: flex; align-items: center; justify-content: center; margin: 0 auto 14px; color: var(--blue-600);
}
.nmt-cat-title { font-family: var(--font-head); font-weight: 700; font-size: 13.5px; color: var(--ink-900); margin-bottom: 4px; }
.nmt-cat-sub { font-size: 11.5px; color: var(--ink-500); }

/* ───────────────────── Feature / why-us cards ───────────────────── */
.nmt-feature {
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-lg);
  padding: 28px 24px; height: 100%; transition: all .2s ease;
}
.nmt-feature:hover { box-shadow: var(--shadow-sm); border-color: var(--blue-100); }
.nmt-feature-icon {
  width: 46px; height: 46px; border-radius: var(--radius-sm); background: var(--blue-50);
  display: flex; align-items: center; justify-content: center; color: var(--blue-600); margin-bottom: 18px;
}
.nmt-feature h3 { font-family: var(--font-head); font-size: 15.5px; font-weight: 700; color: var(--ink-900); margin: 0 0 8px; }
.nmt-feature p { font-size: 13px; color: var(--ink-500); line-height: 1.65; margin: 0; }

/* ───────────────────── Stats band ───────────────────── */
.nmt-stats-band { background: linear-gradient(135deg, var(--navy-950), var(--navy-900) 60%, var(--blue-600)); padding: 52px 0; }
.nmt-stats-grid { max-width: 980px; margin: 0 auto; display: grid; grid-template-columns: repeat(4,1fr); }
.nmt-stats-item { text-align: center; padding: 0 12px; border-right: 1px solid rgba(255,255,255,0.14); }
.nmt-stats-item:last-child { border-right: none; }
.nmt-stats-item .v { font-family: var(--font-head); font-size: 36px; font-weight: 800; color: #fff; line-height: 1; }
.nmt-stats-item .l { font-size: 11px; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase; color: rgba(255,255,255,0.5); margin-top: 8px; }

/* ───────────────────── Announcements ───────────────────── */
.nmt-announce { background: var(--surface); border: 1px solid var(--line); border-left: 3px solid var(--blue-600);
  border-radius: 0 var(--radius-md) var(--radius-md) 0; padding: 16px 20px; display: flex; gap: 14px; align-items: flex-start; }
.nmt-announce-icon { color: var(--blue-600); margin-top: 2px; flex-shrink: 0; }
.nmt-announce-title { font-family: var(--font-head); font-weight: 700; font-size: 14px; color: var(--ink-900); margin-bottom: 3px; }
.nmt-announce-text { font-size: 12.5px; color: var(--ink-500); line-height: 1.6; }

/* ───────────────────── CTA banner ───────────────────── */
.nmt-cta {
  background: linear-gradient(135deg, var(--navy-900), var(--blue-600));
  border-radius: var(--radius-xl); padding: 52px 40px; text-align: center; position: relative; overflow: hidden;
}
.nmt-cta::before { content:''; position:absolute; top:-50px; right:-50px; width:220px; height:220px;
  background: rgba(245,158,11,0.16); border-radius: 50%; }
.nmt-cta-eye { color: rgba(255,255,255,0.7); font-size: 12px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 12px; }
.nmt-cta h2 { font-family: var(--font-head); font-size: 28px; font-weight: 800; color: #fff; margin: 0 0 10px; }
.nmt-cta p { color: rgba(255,255,255,0.78); margin: 0 0 4px; max-width: 480px; margin-left: auto; margin-right: auto; }

/* ───────────────────── Page banner (sub-pages) ───────────────────── */
.nmt-page-banner { background: linear-gradient(135deg, var(--navy-950), var(--navy-900) 65%, var(--blue-600)); padding: 56px 0 52px; }
.nmt-page-banner-inner { max-width: 1180px; margin: 0 auto; padding: 0 24px; text-align: center; }
.nmt-page-banner-icon {
  width: 52px; height: 52px; border-radius: 14px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.18);
  display: flex; align-items: center; justify-content: center; color: #fff; margin: 0 auto 18px;
}
.nmt-page-banner h1 { font-family: var(--font-head); font-size: clamp(26px, 3.4vw, 38px); font-weight: 800; color: #fff; margin: 0 0 10px; }
.nmt-page-banner p { color: rgba(255,255,255,0.72); font-size: 15px; max-width: 540px; margin: 0 auto; line-height: 1.7; }

/* ───────────────────── Forms (card wrapper) ───────────────────── */
.nmt-form-card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-lg); padding: 32px; box-shadow: var(--shadow-sm); }
.nmt-form-title { font-family: var(--font-head); font-size: 19px; font-weight: 700; color: var(--ink-900); margin-bottom: 4px; }
.nmt-form-subtitle { font-size: 13px; color: var(--ink-500); margin-bottom: 22px; }

/* ───────────────────── Info rows (contact details, etc.) ───────────────────── */
.nmt-info-row { display: flex; gap: 14px; align-items: flex-start; padding: 16px; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-md); margin-bottom: 14px; }
.nmt-info-icon { width: 40px; height: 40px; border-radius: var(--radius-sm); background: var(--blue-50); color: var(--blue-600); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.nmt-info-label { font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: var(--amber-600); margin-bottom: 2px; }
.nmt-info-value { font-weight: 600; color: var(--ink-900); font-size: 13.5px; }
.nmt-info-note { font-size: 11.5px; color: var(--ink-500); margin-top: 1px; }

.nmt-social-row { display: flex; gap: 10px; }
.nmt-social-btn { width: 36px; height: 36px; border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center;
  color: #fff; text-decoration: none; transition: opacity .15s; }
.nmt-social-btn:hover { opacity: 0.85; }

/* ───────────────────── Dashboard / Admin shared shell ───────────────────── */
.nmt-app-header {
  background: linear-gradient(135deg, var(--navy-950), var(--navy-900) 70%, var(--blue-600));
  padding: 30px 0;
}
.nmt-app-header-inner { max-width: 1180px; margin: 0 auto; padding: 0 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px; }
.nmt-app-header h1 { font-family: var(--font-head); font-size: 22px; font-weight: 800; color: #fff; margin: 0; display: flex; align-items: center; gap: 10px; }
.nmt-app-header .sub { color: rgba(255,255,255,0.68); font-size: 13px; margin-top: 4px; }
.nmt-app-header .meta { color: rgba(255,255,255,0.75); font-size: 12.5px; display: flex; align-items: center; gap: 8px; }

.nmt-content { max-width: 1180px; margin: 0 auto; padding: 28px 24px 56px; }
.nmt-content.bg-soft { background: var(--surface-soft); max-width: 100%; }

.nmt-stat-card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-md); padding: 18px; text-align: center; }
.nmt-stat-card .icon { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; margin: 0 auto 10px; }
.nmt-stat-card .val { font-family: var(--font-head); font-size: 26px; font-weight: 800; color: var(--ink-900); line-height: 1; }
.nmt-stat-card .lbl { font-size: 11px; color: var(--ink-500); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 6px; }

.nmt-list-card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-md); padding: 20px; margin-bottom: 12px; }
.nmt-list-row { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; }
.nmt-list-title { font-family: var(--font-head); font-weight: 700; font-size: 14.5px; color: var(--ink-900); }
.nmt-list-meta { font-size: 11.5px; color: var(--ink-500); margin-top: 3px; }

.nmt-badge { display: inline-flex; align-items: center; gap: 5px; padding: 4px 11px; border-radius: 999px; font-size: 11px; font-weight: 700; border: 1px solid transparent; }
.nmt-badge-pending { background: var(--warning-bg); color: var(--warning-tx); border-color: var(--warning-line); }
.nmt-badge-approved { background: var(--success-bg); color: var(--success-tx); border-color: var(--success-line); }
.nmt-badge-rejected { background: var(--danger-bg); color: var(--danger-tx); border-color: var(--danger-line); }
.nmt-badge-info { background: var(--info-bg); color: var(--info-tx); border-color: var(--info-line); }
.nmt-badge-neutral { background: var(--surface-soft); color: var(--ink-500); border-color: var(--line); }

.nmt-empty { text-align: center; padding: 56px 24px; color: var(--ink-500); }
.nmt-empty .icon { color: var(--ink-300); margin-bottom: 14px; display: flex; justify-content: center; }
.nmt-empty .title { font-family: var(--font-head); font-weight: 700; font-size: 16px; color: var(--ink-700); margin-bottom: 6px; }

.nmt-cert-card {
  background: linear-gradient(135deg, var(--navy-900), var(--blue-600)); border-radius: var(--radius-lg);
  padding: 26px 22px; color: #fff; position: relative; overflow: hidden;
}
.nmt-cert-card::before { content:''; position:absolute; top:-30px; right:-30px; width:120px; height:120px; background: rgba(245,158,11,0.18); border-radius: 50%; }
.nmt-cert-icon { width: 40px; height: 40px; border-radius: 10px; background: rgba(255,255,255,0.14); display: flex; align-items: center; justify-content: center; margin-bottom: 14px; }
.nmt-cert-title { font-family: var(--font-head); font-size: 15px; font-weight: 700; margin-bottom: 4px; }
.nmt-cert-sub { font-size: 11.5px; color: rgba(255,255,255,0.7); }

.nmt-profile-avatar {
  width: 108px; height: 108px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, var(--navy-900), var(--blue-600)); color: #fff;
  font-family: var(--font-head); font-size: 38px; font-weight: 800; margin: 0 auto;
}

/* Admin nav strip */
.nmt-admin-nav { background: var(--surface); border-bottom: 1.5px solid var(--line); }
.nmt-admin-nav-inner { max-width: 1180px; margin: 0 auto; padding: 0 24px; }

/* ───────────────────── Footer ───────────────────── */
.nmt-footer { background: var(--navy-950); color: #A9B6CE; padding: 48px 0 24px; }
.nmt-footer-inner { max-width: 1180px; margin: 0 auto; padding: 0 24px; }
.nmt-footer-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 40px; margin-bottom: 30px; }
.nmt-footer-brand { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.nmt-footer-brand-text { font-family: var(--font-head); font-weight: 700; font-size: 16px; color: #fff; }
.nmt-footer p.desc { font-size: 13px; line-height: 1.7; color: #8C9AB5; max-width: 260px; margin: 0 0 14px; }
.nmt-footer h4 { font-family: var(--font-head); font-weight: 600; font-size: 12.5px; color: #fff; letter-spacing: 0.04em; margin: 0 0 12px; text-transform: uppercase; }
.nmt-footer a.flink { display: block; font-size: 13.5px; color: #A9B6CE; text-decoration: none; margin-bottom: 8px; transition: color .15s; }
.nmt-footer a.flink:hover { color: var(--amber-400); }
.nmt-footer .contact-line { display: flex; gap: 8px; align-items: flex-start; font-size: 13px; color: #A9B6CE; margin-bottom: 8px; }
.nmt-footer-bottombar { padding: 0 0 22px; }
.nmt-footer-bottom { border-top: 1px solid rgba(255,255,255,0.08); padding-top: 18px; display: flex; justify-content: space-between;
  align-items: center; font-size: 12.5px; color: #6B7A98; flex-wrap: wrap; gap: 8px; }

/* Newsletter bar — a bordered strip integrated between the footer grid and
   the copyright bar, same navy background as the rest of the footer so it
   reads as one continuous block. Heading/text sit left, the subscribe form
   sits right on desktop (Streamlit's own horizontal-block layout already
   wraps these to a clean vertical stack on narrow/mobile widths). */
.st-key-footer_newsletter {
  background: var(--navy-950);
  border-top: 1px solid rgba(255,255,255,0.09);
  border-bottom: 1px solid rgba(255,255,255,0.09);
  padding: 28px 24px;
  margin: 4px 0 0;
}
.st-key-footer_newsletter > div { max-width: 1180px; margin: 0 auto; }
.st-key-footer_newsletter div[data-testid="stHorizontalBlock"]:has(div[data-testid="stForm"]) {
  align-items: center;
}
.st-key-footer_newsletter div[data-testid="stForm"] div[data-testid="stVerticalBlock"] {
  justify-content: center;
}
.st-key-footer_newsletter .nmt-footer-nl-text {
  padding-right: 12px;
  display: flex; flex-direction: column; justify-content: center;
  height: 100%;
}
.st-key-footer_newsletter .nmt-footer-nl-heading {
  display: flex; align-items: center; gap: 8px;
  font-family: var(--font-head); font-weight: 700; font-size: 15.5px;
  color: #fff; margin-bottom: 4px;
}
.st-key-footer_newsletter .nmt-footer-nl-sub { font-size: 12.5px; color: #A9B6CE; margin: 0; line-height: 1.55; }
.st-key-footer_newsletter div[data-testid="stForm"] {
  border: none; padding: 0; background: transparent; margin: 0;
  max-width: 340px; margin-left: auto;
}
.st-key-footer_newsletter div[data-testid="stForm"] div[data-testid="stHorizontalBlock"] {
  gap: 8px !important; align-items: stretch;
}
.st-key-footer_newsletter div[data-testid="stTextInput"] input {
  background: #FFFFFF;
  border: 1.5px solid rgba(255,255,255,0.16);
  color: var(--ink-900);
  padding: 9px 14px; font-size: 13px;
  border-radius: var(--radius-sm);
  box-shadow: none;
  transition: border-color .15s ease, box-shadow .15s ease;
}
.st-key-footer_newsletter div[data-testid="stTextInput"] input::placeholder { color: var(--ink-500); }
.st-key-footer_newsletter div[data-testid="stTextInput"] input:focus {
  border-color: var(--amber-500);
  box-shadow: 0 0 0 3px rgba(245,158,11,0.25);
  outline: none;
}
.st-key-footer_newsletter button[kind="secondaryFormSubmit"],
.st-key-footer_newsletter button[kind="formSubmit"] {
  background: var(--amber-500) !important;
  color: var(--navy-950) !important; border: none !important; border-radius: var(--radius-sm) !important;
  font-weight: 700 !important; font-size: 13px; padding: 9px 16px; white-space: nowrap;
  box-shadow: none !important;
  transition: background .15s ease;
}
.st-key-footer_newsletter button[kind="secondaryFormSubmit"]:hover,
.st-key-footer_newsletter button[kind="formSubmit"]:hover {
  background: var(--amber-600) !important;
  color: var(--navy-950) !important;
  box-shadow: none !important;
}

/* ───────────────────── Animations ───────────────────── */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(22px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.96); }
  to   { opacity: 1; transform: scale(1); }
}
@keyframes countUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}
@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(32,86,214,0.18); }
  50%       { box-shadow: 0 0 0 10px rgba(32,86,214,0); }
}
@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-20px); }
  to   { opacity: 1; transform: translateX(0); }
}

.nmt-fade-in     { animation: fadeInUp 0.55s ease both; }
.nmt-fade-in-d1  { animation: fadeInUp 0.55s 0.1s ease both; }
.nmt-fade-in-d2  { animation: fadeInUp 0.55s 0.2s ease both; }
.nmt-fade-in-d3  { animation: fadeInUp 0.55s 0.3s ease both; }
.nmt-scale-in    { animation: scaleIn  0.45s ease both; }

/* Hero animated stats */
.nmt-hero-stat .v { animation: countUp 0.7s 0.3s ease both; }

/* Card hover lifts */
.nmt-card {
  transition: transform 0.22s ease, box-shadow 0.22s ease;
  animation: fadeInUp 0.5s ease both;
}
.nmt-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg) !important;
}

/* Feature card hover */
.nmt-feature {
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}
.nmt-feature:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: var(--blue-100);
}

/* Button ripple / hover */
.stButton > button {
  transition: all 0.18s ease !important;
  position: relative !important;
  overflow: hidden !important;
}
.stButton > button:active { transform: scale(0.97) !important; }

/* Category card hover */
.nmt-cat-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.nmt-cat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: var(--blue-500);
}

/* Stat card pulse on hover */
.nmt-stat-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.nmt-stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

/* Announcement slide in */
.nmt-announce {
  animation: slideInLeft 0.4s ease both;
}

/* CTA shimmer button effect */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--navy-900) 0%, var(--blue-600) 50%, var(--navy-900) 100%) !important;
  background-size: 200% !important;
  animation: shimmer 3s linear infinite !important;
}

/* Page banner fade */
.nmt-page-banner {
  animation: fadeIn 0.4s ease both;
}

/* Stats band count animation */
.nmt-stats-band .v {
  animation: countUp 0.7s 0.2s ease both;
}

/* ───────────────────── Instructor Card ───────────────────── */
.nmt-instructor-card {
  text-align: center;
  padding: 26px 18px;
  background: var(--surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--line);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
  cursor: default;
}
.nmt-instructor-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
  border-color: var(--blue-100);
}
.nmt-instructor-card img {
  width: 72px; height: 72px; border-radius: 50%; object-fit: cover;
  margin: 0 auto 14px; display: block;
  border: 3px solid var(--blue-100);
  transition: border-color 0.2s ease;
}
.nmt-instructor-card:hover img {
  border-color: var(--blue-500);
}

/* ───────────────────── Scroll reveal ───────────────────── */
/* ─────────────── PREMIUM UPGRADE ANIMATIONS v2 ─────────────── */

/* Glassmorphism card */
.nmt-glass {
  background: rgba(255,255,255,0.72);
  backdrop-filter: blur(16px) saturate(1.4);
  -webkit-backdrop-filter: blur(16px) saturate(1.4);
  border: 1px solid rgba(255,255,255,0.55);
  box-shadow: 0 8px 32px rgba(15,45,107,0.10);
  border-radius: var(--radius-lg);
}

/* Smooth page transitions */
.nmt-page-enter {
  animation: fadeInUp 0.5s cubic-bezier(0.22,1,0.36,1) both;
}

/* Scroll reveal — staggered children */
.nmt-stagger > *:nth-child(1) { animation-delay: 0.05s; }
.nmt-stagger > *:nth-child(2) { animation-delay: 0.12s; }
.nmt-stagger > *:nth-child(3) { animation-delay: 0.19s; }
.nmt-stagger > *:nth-child(4) { animation-delay: 0.26s; }
.nmt-stagger > *:nth-child(5) { animation-delay: 0.33s; }
.nmt-stagger > *:nth-child(6) { animation-delay: 0.40s; }

/* Enhanced hero text gradient */
.nmt-hero h1 em {
  background: linear-gradient(135deg, var(--amber-400), var(--amber-500), #FF6B35);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 4s linear infinite;
  background-size: 200%;
}

/* Animated counter numbers */
@keyframes popIn {
  0%   { transform: scale(0.6); opacity: 0; }
  70%  { transform: scale(1.08); }
  100% { transform: scale(1); opacity: 1; }
}
.nmt-hero-stat .v {
  animation: popIn 0.65s cubic-bezier(0.22,1,0.36,1) both;
}

/* Course card premium hover */
.nmt-card {
  position: relative;
  overflow: hidden;
}
.nmt-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, transparent 60%, rgba(32,86,214,0.04));
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}
.nmt-card:hover::after { opacity: 1; }
.nmt-card:hover { transform: translateY(-8px) scale(1.012); }

/* Testimonial card */
.nmt-testimonial-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  padding: 28px 24px;
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
  animation: fadeInUp 0.55s ease both;
  position: relative;
}
.nmt-testimonial-card::before {
  content: '"';
  position: absolute;
  top: -12px;
  left: 22px;
  font-size: 72px;
  font-family: var(--font-head);
  color: var(--blue-100);
  line-height: 1;
  pointer-events: none;
}
.nmt-testimonial-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-lg);
  border-color: var(--blue-100);
}

/* FAQ accordion */
.nmt-faq-item {
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  margin-bottom: 10px;
  overflow: hidden;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.nmt-faq-item:hover { border-color: var(--blue-100); box-shadow: var(--shadow-sm); }
.nmt-faq-q {
  font-weight: 600;
  font-size: 14px;
  color: var(--ink-900);
  padding: 16px 20px;
  cursor: pointer;
}
.nmt-faq-a {
  font-size: 13.5px;
  color: var(--ink-500);
  line-height: 1.7;
  padding: 0 20px 16px;
}

/* CTA section gradient animation */
.nmt-cta-section {
  background: linear-gradient(135deg, var(--navy-950), var(--navy-900) 45%, var(--blue-600));
  background-size: 200% 200%;
  animation: gradientShift 8s ease infinite;
}
@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50%       { background-position: 100% 50%; }
}

/* Job opening card */
.nmt-job-card {
  background: var(--surface);
  border: 1.5px solid var(--line);
  border-radius: var(--radius-md);
  padding: 22px 24px;
  margin-bottom: 14px;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  animation: fadeInUp 0.45s ease both;
}
.nmt-job-card:hover {
  transform: translateX(4px);
  border-color: var(--blue-500);
  box-shadow: var(--shadow-sm);
}

/* Announcement bar */
.nmt-ann-bar {
  background: linear-gradient(90deg, var(--amber-500), var(--amber-600));
  color: var(--navy-950);
  text-align: center;
  font-size: 13.5px;
  font-weight: 600;
  padding: 10px 20px;
  letter-spacing: 0.01em;
  animation: slideInLeft 0.4s ease both;
}

/* Media Library grid */
.nmt-media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
}
.nmt-media-card {
  border: 1.5px solid var(--line);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--surface-soft);
  transition: border-color 0.18s, box-shadow 0.18s, transform 0.18s;
}
.nmt-media-card:hover {
  border-color: var(--blue-500);
  box-shadow: var(--shadow-sm);
  transform: scale(1.03);
}

/* Stars rating */
.nmt-stars { color: var(--amber-500); font-size: 14px; letter-spacing: 1px; }
.nmt-star-row { display: flex; align-items: center; gap: 2px; color: var(--amber-500); }
.nmt-star-row svg { display: block; }

/* Smooth section dividers */
.nmt-section-divider {
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--blue-100), transparent);
  border: none;
  margin: 48px 0;
}

/* Loader spinner */
@keyframes spin { to { transform: rotate(360deg); } }
.nmt-spinner {
  width: 32px; height: 32px;
  border: 3px solid var(--line);
  border-top-color: var(--blue-600);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}

/* Input focus glow */
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--blue-500) !important;
  box-shadow: 0 0 0 3px rgba(32,86,214,0.10) !important;
  outline: none !important;
}

/* Soft entry for all nmt-shell sections */
.nmt-shell .nmt-section {
  animation: fadeInUp 0.6s cubic-bezier(0.22,1,0.36,1) both;
}

/* Admin CMS section header */
.cms-section-head {
  background: linear-gradient(90deg, var(--blue-50), transparent);
  border-left: 4px solid var(--blue-600);
  padding: 12px 18px;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  margin-bottom: 20px;
}

.nmt-section > * {
  animation: fadeInUp 0.55s ease both;
}

/* ───────────────────── Loading skeleton ───────────────────── */
.nmt-skeleton {
  background: linear-gradient(90deg, var(--line) 25%, var(--line-soft) 50%, var(--line) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
  height: 16px;
}

/* ───────────────────── Verify badge ───────────────────── */
.nmt-verify-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: var(--success-bg); border: 1.5px solid var(--success-line);
  color: var(--success-tx); padding: 8px 18px; border-radius: 999px;
  font-weight: 700; font-size: 14px;
  animation: scaleIn 0.4s ease both;
}


/* Featured badge on course cards */
.nmt-badge-featured {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: linear-gradient(90deg, var(--amber-100), #FEF9EC);
  border: 1.5px solid var(--amber-400);
  color: var(--amber-600);
  font-size: 10.5px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 20px;
  margin-bottom: 8px;
  letter-spacing: 0.03em;
}

/* Admin CMS nav button active */
.nmt-cms-active {
  background: var(--navy-900) !important;
  color: #fff !important;
}

/* Job card status indicators */
.nmt-status-open  { color: var(--success-tx); font-weight: 700; }
.nmt-status-closed{ color: var(--danger-tx);  font-weight: 700; }

/* Smooth form transitions */
.stForm { animation: fadeInUp 0.35s ease both; }

/* Course detail sticky sidebar */
@media (min-width: 900px) {
  .nmt-course-side { position: sticky; top: 80px; }
}

/* Section visibility badge */
.cms-vis-on  { background: var(--success-bg); color: var(--success-tx); padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 700; }
.cms-vis-off { background: var(--danger-bg);  color: var(--danger-tx);  padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 700; }

@media (max-width: 900px) {
  .nmt-hero-stats { gap: 24px; }
  .nmt-hero-stat { border-right: none; margin-right: 0; padding-right: 0; }
  .nmt-stats-grid { grid-template-columns: repeat(2,1fr); row-gap: 24px; }
  .nmt-stats-item { border-right: none; }
  .nmt-footer-grid { grid-template-columns: 1fr 1fr; }
  /* Hero video stacks naturally below the hero text on mobile/tablet */
  .nmt-hero-grid { grid-template-columns: 1fr; gap: 28px; }
  .nmt-hero-media { order: 2; transform: none; }
  .nmt-hero-content { order: 1; }
}

@media (max-width: 640px) {
  .st-key-nmt_stat_row div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
  .st-key-nmt_stat_row div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    flex: 0 0 calc(50% - 6px) !important; width: calc(50% - 6px) !important; min-width: 0 !important;
  }
}

/* Footer — phone-width layout */
@media (max-width: 560px) {
  .nmt-footer { padding: 44px 0 24px; }
  .nmt-footer-grid { grid-template-columns: 1fr; gap: 32px; }
  .nmt-footer p.desc { max-width: 100%; }
  .nmt-footer-bottom { flex-direction: column; align-items: flex-start; gap: 6px; }
  .st-key-footer_newsletter { padding: 20px 20px; }
  .st-key-footer_newsletter .nmt-footer-nl-text { padding-right: 0; margin-bottom: 14px; text-align: left; }
  .st-key-footer_newsletter div[data-testid="stForm"] { max-width: 100%; margin-left: 0; }
}

/* ───────────────────── Mobile responsiveness pass ─────────────────────
   Additive only: reflows the handful of fixed-column inline grids and
   tightens spacing/tap targets on small screens. Desktop rules above are
   untouched, so nothing here changes anything above these breakpoints. */
@media (max-width: 900px) {
  /* Tab strips (CMS admin, course detail, login, dashboard, etc.) scroll
     instead of overflowing the page. justify-content: flex-start is required —
     without it the row can render scrolled/centered so the tabs open just off
     the initial screen until you scroll or tap blindly to find them. */
  .stTabs [data-baseweb="tab-list"] {
    flex-wrap: nowrap !important; justify-content: flex-start !important;
    overflow-x: auto; -webkit-overflow-scrolling: touch;
    mask-image: none !important; -webkit-mask-image: none !important;
  }
  .stTabs [data-baseweb="tab"] { white-space: nowrap; flex-shrink: 0; }

  .nmt-cta { padding: 40px 24px; }
  .nmt-form-card { padding: 22px; }
}

@media (max-width: 640px) {
  /* Home hero mini-stats band: 4 → 2 columns */
  .nmt-mini-stats-grid { grid-template-columns: repeat(2, 1fr) !important; gap: 18px !important; padding: 24px 16px !important; }
  /* Testimonials: always a single column on phones, regardless of count */
  .nmt-testimonials-grid { grid-template-columns: 1fr !important; }
  /* About "Quick Facts" and certificate-detail grids: single column */
  .nmt-quickfacts-grid { grid-template-columns: 1fr !important; }
  .nmt-cert-detail-card { padding: 22px !important; }
  .nmt-cert-detail-grid { grid-template-columns: 1fr !important; gap: 16px !important; }

  .nmt-page-banner { padding: 44px 0 40px; }
  .nmt-cta h2 { font-size: 22px; }

  /* Comfortable tap targets for buttons/inputs on touch screens */
  .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
    padding: 0.65rem 1rem !important; min-height: 44px !important;
  }
  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea,
  .stNumberInput > div > div > input,
  .stSelectbox > div > div { min-height: 44px !important; }
}

@media (max-width: 380px) {
  .nmt-mini-stats-grid { grid-template-columns: 1fr !important; }
}
</style>
"""


def inject_css():
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
