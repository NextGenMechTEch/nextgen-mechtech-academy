"""
Centralized SVG icon library.

Every icon used across the app lives here as a small inline SVG (stroke-based,
24x24 viewBox, currentColor) so the whole product shares one consistent visual
language instead of mixed emoji glyphs. This mirrors the convention used by
icon sets like Feather / Lucide that most professional SaaS products use.

Usage:
    from components.icons import icon
    st.markdown(icon("book-open", size=18, color="#2563EB"), unsafe_allow_html=True)
"""

_PATHS = {
    # Navigation / general
    "home": '<path d="M3 9.5 12 3l9 6.5"/><path d="M5 10v10a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V10"/>',
    "book-open": '<path d="M12 6.5C10.5 5 8 4 4 4v15c4 0 6.5 1 8 2.5 1.5-1.5 4-2.5 8-2.5V4c-4 0-6.5 1-8 2.5z"/><path d="M12 6.5V21.5"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M3 13h18"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 16v-5"/><circle cx="12" cy="8.2" r="0.6" fill="currentColor" stroke="none"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/>',
    "user": '<circle cx="12" cy="8" r="3.6"/><path d="M5 20c0-3.6 3-6 7-6s7 2.4 7 6"/>',
    "log-in": '<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/><path d="M10 17l5-5-5-5"/><path d="M15 12H3"/>',
    "log-out": '<path d="M9 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h3"/><path d="M16 17l-5-5 5-5"/><path d="M11 12h10"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1.3"/><rect x="14" y="3" width="7" height="7" rx="1.3"/><rect x="3" y="14" width="7" height="7" rx="1.3"/><rect x="14" y="14" width="7" height="7" rx="1.3"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 13a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V19a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 17.58a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 13 1.65 1.65 0 0 0 3.17 12H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 7.09a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 2.77 1.65 1.65 0 0 0 10 1.26V1a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.32 7c.13.31.32.59.56.82.24.24.51.42.83.55.31.13.65.2.99.2H22a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',

    # Stats / academics
    "users": '<circle cx="8.5" cy="8" r="3.2"/><path d="M2 19c0-3.3 2.8-5.6 6.5-5.6S15 15.7 15 19"/><path d="M16.5 8.4a3 3 0 1 1 0-5.9"/><path d="M17.5 13.6c2.6.5 4.5 2.4 4.5 5.4"/>',
    "graduation-cap": '<path d="M2 9.5 12 5l10 4.5-10 4.5z"/><path d="M6 11.5V17c0 1.2 2.7 2.5 6 2.5s6-1.3 6-2.5v-5.5"/><path d="M21 9.5v5.7"/>',
    "award": '<circle cx="12" cy="8" r="5.5"/><path d="m8.5 13 -1.5 7 5-2.6 5 2.6-1.5-7"/>',
    "trending-up": '<path d="m3 17 6-6 4 4 7-8"/><path d="M16 6h4v4"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    "bar-chart": '<path d="M5 21V10"/><path d="M12 21V5"/><path d="M19 21v-7"/>',
    "check-circle": '<circle cx="12" cy="12" r="9"/><path d="m8.5 12.3 2.4 2.4 4.8-5.4"/>',
    "x-circle": '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6"/><path d="m15 9-6 6"/>',
    "alert-circle": '<circle cx="12" cy="12" r="9"/><path d="M12 8v5"/><circle cx="12" cy="15.8" r="0.6" fill="currentColor" stroke="none"/>',
    "help-circle": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.3a2.5 2.5 0 1 1 3.6 2.2c-.8.5-1.1 1-1.1 2"/><circle cx="12" cy="16.5" r="0.6" fill="currentColor" stroke="none"/>',

    # Subjects / categories
    "code": '<path d="m9 7-5 5 5 5"/><path d="m15 7 5 5-5 5"/>',
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="10" y="10" width="4" height="4"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
    "zap": '<path d="M12 2 4 14h6l-1 8 9-13h-6z"/>',
    "cog": '<circle cx="12" cy="12" r="2.6"/><path d="M12 4v2.2M12 17.8V20M4.9 7l1.9 1.1M17.2 15.9l1.9 1.1M4.9 17l1.9-1.1M17.2 8.1l1.9-1.1M4 12h2.2M17.8 12H20"/>',
    "tool": '<path d="M14.7 6.3a4 4 0 1 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2-1 -1-2z"/>',
    "palette": '<circle cx="12" cy="12" r="9.5"/><circle cx="8.5" cy="10.5" r="1.1" fill="currentColor" stroke="none"/><circle cx="12.5" cy="8" r="1.1" fill="currentColor" stroke="none"/><circle cx="16" cy="11" r="1.1" fill="currentColor" stroke="none"/><path d="M12 16.5c1.8 0 2.7-1 2.5-2.3-.1-.7.4-1.2 1.1-1.2H17c1.7 0 2.5-1.6 1.6-3.1A9.2 9.2 0 0 0 12 6"/>',
    "layout": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>',
    "bot": '<rect x="5" y="9" width="14" height="10" rx="2.4"/><path d="M12 5v4"/><circle cx="12" cy="3.3" r="1.1" fill="currentColor" stroke="none"/><path d="M9 14h.01M15 14h.01"/><path d="M3 13h2M19 13h2"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.1" fill="currentColor" stroke="none"/>',
    "shield": '<path d="M12 3 5 6v6c0 4.5 3 7.5 7 9 4-1.5 7-4.5 7-9V6z"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18"/><path d="M8 3v4M16 3v4"/>',
    "dollar-sign": '<path d="M12 2v20"/><path d="M16.5 6.5C16 5 14 4 12 4 9.5 4 7.5 5.4 7.5 7.6S9.6 11 12 11s4.5 1.3 4.5 3.4-2 3.6-4.5 3.6c-2 0-4-1-4.5-2.5"/>',
    "handshake": '<path d="M2 12.5 6 9l3 2.6L13 8l4 3 3-2.2"/><path d="M2 12.5 7 17l3-2 2.5 2.3a2 2 0 0 0 2.8-2.8L13 12"/><path d="M20 9.8 22 12l-2.5 2.5"/>',

    # Contact / location
    "phone": '<path d="M5 4h3.2l1.4 4.6-2 1.6a12 12 0 0 0 5.2 5.2l1.6-2 4.6 1.4V18a2 2 0 0 1-2 2C9.9 20 4 14.1 4 7a2 2 0 0 1 1-3z" fill="none"/>',
    "map-pin": '<path d="M19 10.5c0 5-7 11-7 11s-7-6-7-11a7 7 0 0 1 14 0z"/><circle cx="12" cy="10.5" r="2.4"/>',
    "send": '<path d="m4 11 16-7-7 16-2.5-6.5z"/><path d="M13 13 4 11"/>',
    "facebook": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M14.5 8.5h-1.7c-.8 0-1.3.5-1.3 1.3V11h3l-.4 3h-2.6v7" fill="none"/>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r="0.9" fill="currentColor" stroke="none"/>',
    "linkedin": '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="7.5" cy="7.5" r="1.1" fill="currentColor" stroke="none"/><path d="M7.5 11v7"/><path d="M12 18v-4.5c0-1.4 1-2.5 2.4-2.5s2.1 1.1 2.1 2.5V18M12 11v7"/>',
    "youtube": '<rect x="2.5" y="5" width="19" height="14" rx="4"/><path d="m10.5 9 5 3-5 3z" fill="currentColor" stroke="none"/>',

    # Status / misc
    "bell": '<path d="M9 18a3 3 0 0 0 6 0"/><path d="M6 17v-5.5a6 6 0 0 1 12 0V17a1.6 1.6 0 0 1 1.6 1.6H4.4A1.6 1.6 0 0 1 6 17z"/>',
    "upload": '<path d="M12 16V4"/><path d="m7 9 5-5 5 5"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>',
    "download": '<path d="M12 4v12"/><path d="m7 11 5 5 5-5"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>',
    "trash": '<path d="M4 7h16"/><path d="M9 7V4.6c0-.4.3-.6.6-.6h4.8c.3 0 .6.2.6.6V7"/><path d="M6 7l1 13c0 .6.5 1 1 1h8c.5 0 1-.4 1-1l1-13"/>',
    "edit": '<path d="M4 19.5 4.6 16.6 15 6.2a1.6 1.6 0 0 1 2.3 0l1.5 1.5a1.6 1.6 0 0 1 0 2.3L8.4 20.4 4 19.5z"/>',
    "plus-circle": '<circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m20 20-4.4-4.4"/>',
    "arrow-right": '<path d="M4 12h16"/><path d="m13 5 7 7-7 7"/>',
    "chevron-right": '<path d="m9 5 7 7-7 7"/>',
    "external-link": '<path d="M14 4h6v6"/><path d="M20 4 10 14"/><path d="M18 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5"/>',
    "lock": '<rect x="4.5" y="10.5" width="15" height="10" rx="2"/><path d="M8 10.5V7a4 4 0 0 1 8 0v3.5"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="1.6"/><path d="m4 17 5-5 3.5 3.5L17 11l3 3"/>',
    "star": '<path d="M12 3.5l2.6 5.6 6 .8-4.4 4.2 1.1 6-5.3-3-5.3 3 1.1-6L3.4 9.9l6-.8z"/>',
    "file-text": '<path d="M7 3h7l4 4v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v4h4"/><path d="M9 12h6M9 16h6"/>',
    "message-square": '<path d="M4 5h16v11H9l-5 4z"/>',

    # Course detail / miscellaneous (previously referenced but missing —
    # each silently fell back to the help-circle glyph until added here)
    "circle": '<circle cx="12" cy="12" r="8"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4.2l2 2H19a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><ellipse cx="12" cy="12" rx="4" ry="9"/>',
    "heart": '<path d="M12 20s-7-4.4-9.3-9A5.3 5.3 0 0 1 12 6.2 5.3 5.3 0 0 1 21.3 11c-2.3 4.6-9.3 9-9.3 9z"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    "list": '<path d="M9 6h12M9 12h12M9 18h12"/><path d="M4 6h.01M4 12h.01M4 18h.01"/>',
    "monitor": '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
    "package": '<path d="m21 8-9-5-9 5v8l9 5 9-5z"/><path d="m3 8 9 5 9-5M12 13v8"/>',
}


def icon_svg(name: str, size: int = 18, color: str = "currentColor", stroke_width: float = 1.9) -> str:
    """Return a raw <svg> string for the given icon name."""
    path = _PATHS.get(name, _PATHS["help-circle"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" style="display:block">{path}</svg>'
    )


def icon(name: str, size: int = 18, color: str = "currentColor", stroke_width: float = 1.9,
         style: str = "") -> str:
    """Return an inline-block wrapped icon, safe to drop into f-strings inside markdown HTML."""
    svg = icon_svg(name, size, color, stroke_width)
    return f'<span style="display:inline-flex;vertical-align:middle;{style}">{svg}</span>'
