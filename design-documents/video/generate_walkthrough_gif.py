from __future__ import annotations

from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).with_name("agent-memory-ui-flow.gif")
MP4_OUT = Path(__file__).with_name("agent-memory-ui-flow.mp4")
W, H = 1280, 720
BG = (238, 242, 247)
PANEL = (255, 255, 255)
LINE = (216, 222, 233)
INK = (16, 24, 40)
MUTED = (101, 113, 133)
ACCENT = (47, 91, 234)
SOFT = (237, 242, 255)
GREEN = (5, 150, 105)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


F_TITLE = font(34, True)
F_H2 = font(22, True)
F_BODY = font(18)
F_SMALL = font(14)
F_TINY = font(12, True)


def wrap(draw: ImageDraw.ImageDraw, text: str, max_width: int, fnt: ImageFont.ImageFont) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        width = draw.textbbox((0, 0), trial, font=fnt)[2]
        if width <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, fnt: ImageFont.ImageFont, fill=INK, max_width: int | None = None, line_gap: int = 6) -> int:
    x, y = xy
    lines = wrap(draw, value, max_width, fnt) if max_width else value.splitlines()
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += draw.textbbox((0, 0), line, font=fnt)[3] + line_gap
    return y


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill=PANEL, outline=LINE, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=12, fill=fill, outline=outline, width=width)


def base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    panel(draw, (20, 20, 250, 700))
    text(draw, (40, 50), "CONFIGURATION", F_TINY, ACCENT)
    text(draw, (40, 78), "OCI Agent Memory Console", F_BODY, max_width=180)
    text(draw, (40, 140), "Main\nConfig\nKeys", F_BODY, MUTED)
    text(draw, (40, 230), "Workspace", F_H2)
    text(draw, (40, 265), "Overview\nOpenAI SDK\nLangGraph\nWayFlow", F_BODY, MUTED)
    return img, draw


def frame(title: str, body: str, highlight: str) -> Image.Image:
    img, draw = base()
    panel(draw, (280, 30, 1250, 150))
    text(draw, (310, 58), "WORKSPACE", F_TINY, ACCENT)
    text(draw, (310, 82), title, F_TITLE)
    text(draw, (310, 124), body, F_SMALL, MUTED, max_width=780)

    panel(draw, (280, 170, 1250, 240))
    metrics = [("Memory user", "ociopenai / ocigraph / ociwayflow"), ("Thread", "Pending"), ("Messages", "0"), ("Last activity", "No turns yet")]
    for idx, (label, value) in enumerate(metrics):
        x = 310 + idx * 230
        draw.line((x, 190, x, 225), fill=ACCENT, width=3)
        text(draw, (x + 14, 186), label.upper(), F_TINY, MUTED)
        text(draw, (x + 14, 208), value, F_BODY)

    panel(draw, (280, 260, 1250, 500))
    text(draw, (310, 290), "LIVE CALL AND RETRIEVAL PATH", F_TINY, ACCENT)
    text(draw, (310, 318), "Execution flow", F_H2)
    steps = [
        ("Thread", "Open or create memory thread."),
        ("Recall", "Load summary, context card, and memory hits."),
        ("API call", "Call OCI Responses."),
        ("Persist", "Store the completed turn."),
        ("Refresh", "Update chat and diagnostics."),
    ]
    for idx, (label, value) in enumerate(steps):
        x1 = 310 + idx * 180
        box = (x1, 370, x1 + 160, 470)
        active = highlight == label
        panel(draw, box, fill=SOFT if active else (248, 250, 252), outline=ACCENT if active else LINE, width=3 if active else 1)
        text(draw, (x1 + 14, 386), f"{idx + 1}. {label}", F_BODY, ACCENT if active else INK)
        text(draw, (x1 + 14, 416), value, F_SMALL, MUTED, max_width=128)

    panel(draw, (280, 525, 1250, 690))
    text(draw, (310, 555), "BOTTOM DIAGNOSTICS", F_TINY, ACCENT)
    tabs = ["Logs", "Call", "Retrieval Code", "API", "Time", "Other"]
    x = 310
    for tab in tabs:
        w = 84 if tab != "Retrieval Code" else 150
        active = highlight == "Retrieval Code" and tab == "Retrieval Code"
        panel(draw, (x, 595, x + w, 635), fill=SOFT if active else (248, 250, 252), outline=ACCENT if active else LINE, width=2 if active else 1)
        text(draw, (x + 12, 607), tab, F_SMALL, ACCENT if active else INK)
        x += w + 10
    if highlight == "Retrieval Code":
        text(draw, (310, 650), "Shows snapshot() and self._memory.search(...) scoped by SearchScope(user_id).", F_SMALL, GREEN)
    return img


slides = [
    ("OCI Agent Memory Console", "A live workspace for memory recall, OCI Responses, and persistence.", "Thread"),
    ("OpenAI SDK Workspace", "Direct SDK path: retrieve memory, call OCI Responses, persist the turn.", "Recall"),
    ("LangGraph Workspace", "The same memory backend represented as explicit graph nodes.", "API call"),
    ("WayFlow Workspace", "WayFlow Agent conversation over the same retrieved memory context.", "API call"),
    ("Memory Persistence", "Completed turns are stored back into Oracle Agent Memory for future recall.", "Persist"),
    ("Technical Diagnostics", "Use bottom tabs to explain logs, call details, API metadata, and retrieval code.", "Retrieval Code"),
]

frames: list[Image.Image] = []
for slide in slides:
    rendered = frame(*slide)
    frames.extend([rendered] * 18)

frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=120, loop=0, optimize=True)
imageio.mimsave(MP4_OUT, [np.array(item) for item in frames], fps=8, codec="libx264", quality=8)
print(OUT)
print(MP4_OUT)
