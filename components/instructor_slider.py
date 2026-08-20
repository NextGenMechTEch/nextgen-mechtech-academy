"""
Auto-sliding instructor carousel.

Renders any number of Instructor rows (from the database) as a single,
continuously auto-scrolling row. Because the card list is built from
whatever instructors exist in the DB at render time, adding a 5th, 6th,
7th... instructor from the Admin/CMS panel makes them show up here
automatically — no code changes needed.
"""
import uuid

from components.icons import icon
from utils.cloudinary_service import resolve_src


def _initials(name: str) -> str:
    clean = name.replace("Engr. ", "").replace("Dr. ", "")
    return "".join(p[0] for p in clean.split()[:2]).upper()


def _instructor_card_html(instr, avatar_size: int = 72) -> str:
    initials = _initials(instr.name)

    if instr.photo_data:
        photo_html = (
            f'<img src="{resolve_src(instr.photo_data, width=avatar_size * 2)}" '
            f'style="width:{avatar_size}px;height:{avatar_size}px;border-radius:50%;object-fit:cover;'
            f'margin:0 auto 14px;display:block;border:3px solid var(--blue-100);" alt="{instr.name}">'
        )
    elif instr.photo_url:
        photo_html = (
            f'<img src="{instr.photo_url}" '
            f'style="width:{avatar_size}px;height:{avatar_size}px;border-radius:50%;object-fit:cover;'
            f'margin:0 auto 14px;display:block;border:3px solid var(--blue-100);" alt="{instr.name}" '
            f'onerror="this.style.display=\'none\'">'
        )
    else:
        photo_html = (
            f'<div class="nmt-profile-avatar" style="width:{avatar_size}px;height:{avatar_size}px;'
            f'font-size:{int(avatar_size*0.33)}px;margin:0 auto 14px;">{initials}</div>'
        )

    social_html = ""
    if getattr(instr, "linkedin_url", None):
        social_html += (
            f'<a href="{instr.linkedin_url}" target="_blank" style="color:var(--blue-600);margin:0 4px;">'
            f'{icon("linkedin", size=14)}</a>'
        )

    qualifications = getattr(instr, "qualifications", "") or ""
    experience = getattr(instr, "experience", "") or ""
    exp_html = (
        f'<div style="font-size:11.5px;color:var(--ink-500);margin-bottom:8px;">{experience}</div>'
        if experience else ""
    )

    return f"""
    <div class="nmt-instructor-card nmt-slider-card">
      {photo_html}
      <div style="font-weight:700;font-size:14.5px;color:var(--ink-900);margin-bottom:4px;">{instr.name}</div>
      <div style="font-size:12.5px;color:var(--blue-600);font-weight:600;margin-bottom:6px;">{instr.designation}</div>
      <div style="font-size:11.5px;color:var(--ink-500);margin-bottom:6px;">{qualifications}</div>
      {exp_html}
      {social_html}
    </div>
    """


def render_instructors_slider(instructors, avatar_size: int = 72, speed_seconds_per_card: float = 3.5) -> str:
    """Return HTML for a one-row, auto-sliding, infinite-loop instructor carousel.

    `instructors` is any list of Instructor ORM rows (any length — 1, 4, or 40).
    The row scrolls continuously to the left and pauses on hover; on small
    screens it degrades to a swipeable horizontal scroller.
    """
    if not instructors:
        return ""

    uid = uuid.uuid4().hex[:8]
    n = len(instructors)

    cards_html = "".join(_instructor_card_html(i, avatar_size) for i in instructors)

    # Duplicate the row so the marquee loop is seamless (scrolls -50% then resets).
    # Only loop-duplicate when there are enough cards that a seam wouldn't be
    # jarring; otherwise the row is short enough to just center it.
    should_loop = n >= 3
    track_content = cards_html * 2 if should_loop else cards_html
    duration = max(n * speed_seconds_per_card, 12)

    animation_css = (
        f"animation: nmt-slide-{uid} {duration}s linear infinite;"
        if should_loop else ""
    )
    keyframes_css = (
        f"""
        @keyframes nmt-slide-{uid} {{
          from {{ transform: translateX(0); }}
          to   {{ transform: translateX(-50%); }}
        }}
        """
        if should_loop else ""
    )
    justify = "flex-start" if should_loop else "center"

    return f"""
    <style>
      .nmt-instr-viewport-{uid} {{
        overflow: hidden;
        width: 100%;
        -webkit-mask-image: linear-gradient(90deg, transparent, #000 5%, #000 95%, transparent);
        mask-image: linear-gradient(90deg, transparent, #000 5%, #000 95%, transparent);
      }}
      .nmt-instr-track-{uid} {{
        display: flex;
        flex-wrap: nowrap;
        gap: 18px;
        width: max-content;
        justify-content: {justify};
        {animation_css}
      }}
      .nmt-instr-viewport-{uid}:hover .nmt-instr-track-{uid} {{
        animation-play-state: paused;
      }}
      .nmt-slider-card {{
        flex: 0 0 230px;
        width: 230px;
      }}
      {keyframes_css}
      @media (max-width: 640px) {{
        .nmt-instr-viewport-{uid} {{
          overflow-x: auto;
          -webkit-overflow-scrolling: touch;
        }}
        .nmt-instr-track-{uid} {{
          animation: none !important;
        }}
      }}
    </style>
    <div class="nmt-instr-viewport-{uid}">
      <div class="nmt-instr-track-{uid}">
        {track_content}
      </div>
    </div>
    """
