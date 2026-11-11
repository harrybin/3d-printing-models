"""Create an English copy of the butterfly-knife assembly drawing.

The original image is preserved. Only its text bands and annotation boxes are
redrawn; all model geometry and other image pixels remain unchanged.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "images" / "butterfly-messer-explosion.png"
OUTPUT = ROOT / "docs" / "images" / "butterfly-messer-explosion-en.png"

TOP = (21, 24, 30)
PANEL = (30, 34, 42)
WHITE = (236, 239, 244)
BLUE = (136, 192, 208)
GREEN = (163, 190, 140)
GOLD = (235, 203, 139)
CYAN = (35, 163, 199)
RED = (240, 113, 103)


def font_path(bold: bool) -> Path:
    windows = Path(r"C:\Windows\Fonts")
    linux = Path("/usr/share/fonts/truetype/dejavu")
    candidates = (
        windows / ("arialbd.ttf" if bold else "arial.ttf"),
        linux / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("Arial or DejaVu Sans is required to render the English labels")


def fitted_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_height: int,
    *,
    bold: bool,
    largest: int,
    smallest: int = 12,
) -> ImageFont.FreeTypeFont:
    path = font_path(bold)
    for size in range(largest, smallest - 1, -1):
        font = ImageFont.truetype(str(path), size)
        box = draw.textbbox((0, 0), text, font=font)
        if box[2] - box[0] <= max_width and box[3] - box[1] <= max_height:
            return font
    raise ValueError(f"Text does not fit its drawing label: {text}")


def draw_box(
    draw: ImageDraw.ImageDraw,
    bounds: tuple[int, int, int, int],
    color: tuple[int, int, int],
    text: str,
) -> None:
    left, top, right, bottom = bounds
    draw.rectangle(bounds, fill=PANEL)
    draw.rectangle(bounds, outline=color, width=2)
    font = fitted_font(
        draw, text, right - left - 14, bottom - top - 8,
        bold=True, largest=18,
    )
    draw.text((left + 7, top + 4), text, font=font, fill=WHITE)


def draw_detail_box(
    draw: ImageDraw.ImageDraw,
    bounds: tuple[int, int, int, int],
    color: tuple[int, int, int],
    lines: tuple[str, ...],
) -> None:
    left, top, right, bottom = bounds
    draw.rectangle(bounds, fill=PANEL)
    draw.rectangle(bounds, outline=color, width=2)
    line_height = 16
    text_height = len(lines) * line_height
    if text_height > bottom - top - 8:
        raise ValueError(f"Detail text does not fit its drawing label: {lines}")
    y = top + (bottom - top - text_height) // 2
    for line in lines:
        fitted = fitted_font(
            draw, line, right - left - 14, line_height,
            bold=False, largest=14,
        )
        draw.text((left + 7, y), line, font=fitted, fill=WHITE)
        y += line_height


def render() -> None:
    image = Image.open(SOURCE).convert("RGB")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, image.width - 1, 63), fill=TOP)
    title = "EXPLODED ASSEMBLY DRAWING: Butterfly Knife (14 parts, tool- and glue-free)"
    title_font = fitted_font(draw, title, 1260, 36, bold=True, largest=25)
    draw.text((25, 22), title, font=title_font, fill=WHITE)
    detail = "DETAIL: Pivot joint, Zen pins and U-clip retention"
    detail_font = fitted_font(draw, detail, 800, 28, bold=True, largest=19)
    draw.text((1320, 27), detail, font=detail_font, fill=BLUE)

    main_labels = (
        ((37, 117, 787, 146), RED,
         "Step 5: 4x U-clips (clip-*) -> slide sideways (+/-X) into the bolt-ring grooves"),
        ((37, 257, 861, 286), BLUE,
         "Step 3: 2x upper handle scales (griff-safe-oben & griff-bite-oben) -> fit from above (-Z)"),
        ((37, 492, 824, 526), CYAN,
         "Step 2: Blade (left) & T-latch (right, Bite handle) -> place from above (-Z)"),
        ((37, 692, 776, 721), GREEN,
         "Step 1: 2x lower handle scales (griff-*-unten) with Zen pins & locating pins (base)"),
        ((37, 867, 776, 894), GOLD,
         "Step 4: 4x D-bolts (bolzen-*, Ø4.44 mm shaft) -> insert from below (+Z)"),
    )
    for bounds, color, text in main_labels:
        draw_box(draw, bounds, color, text)

    detail_labels = (
        ((1337, 108, 1620, 168), RED,
         ("U-clip (3.32 mm opening width)", "snaps sideways into the 2.30 mm", "bolt-ring groove")),
        ((1337, 277, 1573, 328), BLUE,
         ("Upper scale with recessed clip pocket", "and 45° pin seat")),
        ((1337, 482, 1560, 533), CYAN,
         ("Blade root (tang) with four", "Zen-pin stop recesses")),
        ((1337, 667, 1591, 718), GREEN,
         ("Lower scale with Zen pin (Ø4.0)", "and locating pin (Ø3.1 mm)")),
        ((1337, 857, 1633, 907), GOLD,
         ("D-bolt (Ø4.44 mm shaft, chamfer)", "in Ø5.30 mm D-hole from below (+Z)")),
    )
    for bounds, color, lines in detail_labels:
        draw_detail_box(draw, bounds, color, lines)

    footer = (20, 1047, 2140, 1175)
    draw.rectangle(footer, fill=PANEL, outline=(101, 117, 140), width=1)
    columns = (
        (36, GREEN, "Step 1: Base",
         ("Place both lower scales flat on the table",
          "with the Zen pins pointing up.")),
        (454, CYAN, "Step 2: Blade & latch",
         ("Place the blade in front between the Zen pins",
          "and the T-latch behind it in the Bite handle",
          "(-Z).")),
        (874, BLUE, "Step 3: Upper scales",
         ("Press the upper scales down from above",
          "(-Z) onto the locating pins.")),
        (1294, GOLD, "Step 4: 4x D-bolts",
         ("Push four D-bolts up (+Z) through the",
          "D-holes until their heads sit flush.")),
        (1713, RED, "Step 5: 4x U-clips",
         ("Snap U-clips sideways (+X front, -X rear)",
          "into the bolt-ring grooves.")),
    )
    heading_font = ImageFont.truetype(str(font_path(True)), 18)
    body_font = ImageFont.truetype(str(font_path(False)), 15)
    for x, color, heading, lines in columns:
        draw.text((x, 1060), heading, font=heading_font, fill=color)
        for index, line in enumerate(lines):
            draw.text((x, 1092 + index * 21), line, font=body_font, fill=WHITE)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT)
    print(f"Created {OUTPUT.relative_to(ROOT)} from the unchanged original drawing.")


if __name__ == "__main__":
    render()
