"""Create compact QA contact sheets from design-review segment renders."""

from __future__ import annotations

from pathlib import Path
from shutil import copyfile

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SEGMENTS = ROOT / "design-review" / "renders" / "segments"
OUTPUT = ROOT / "design-review" / "renders" / "final"
OUTPUT.mkdir(parents=True, exist_ok=True)
FONT = ImageFont.load_default()


def sheet(name: str, files: list[str], columns: int, thumb_width: int) -> None:
    cards: list[Image.Image] = []
    for filename in files:
        source = Image.open(SEGMENTS / filename).convert("RGB")
        ratio = thumb_width / source.width
        preview = source.resize((thumb_width, round(source.height * ratio)), Image.Resampling.LANCZOS)
        card = Image.new("RGB", (thumb_width, preview.height + 28), "#ffffff")
        card.paste(preview, (0, 28))
        draw = ImageDraw.Draw(card)
        draw.text((8, 9), filename.replace(".png", ""), fill="#1e293b", font=FONT)
        cards.append(card)

    rows = (len(cards) + columns - 1) // columns
    row_height = max(card.height for card in cards)
    canvas = Image.new("RGB", (columns * thumb_width, rows * row_height), "#dce5ee")
    for index, card in enumerate(cards):
        x = (index % columns) * thumb_width
        y = (index // columns) * row_height
        canvas.paste(card, (x, y))
    canvas.save(OUTPUT / f"{name}.jpg", quality=84, optimize=True)


sheet(
    "public-desktop-review",
    [
        "public-desktop-hero.png",
        "public-desktop-problem.png",
        "public-desktop-capabilities.png",
        "public-desktop-workflow.png",
        "public-desktop-tici.png",
        "public-desktop-progress.png",
        "public-desktop-safety.png",
        "public-desktop-download.png",
    ],
    columns=2,
    thumb_width=520,
)

sheet(
    "public-mobile-review",
    [
        "public-mobile-hero.png",
        "public-mobile-problem.png",
        "public-mobile-capabilities.png",
        "public-mobile-workflow.png",
        "public-mobile-tici.png",
        "public-mobile-progress.png",
        "public-mobile-safety.png",
        "public-mobile-download.png",
    ],
    columns=4,
    thumb_width=240,
)

sheet(
    "admin-all-review",
    [
        "admin-overview-screen.png",
        "admin-upload-screen.png",
        "admin-releases-screen.png",
        "admin-cms-screen.png",
        "admin-history-screen.png",
    ],
    columns=2,
    thumb_width=600,
)

for source_name, target_name in {
    "admin-overview-screen.png": "admin-overview.png",
    "admin-upload-screen.png": "admin-upload.png",
    "admin-releases-screen.png": "admin-releases.png",
    "admin-cms-screen.png": "admin-cms.png",
    "admin-history-screen.png": "admin-history.png",
}.items():
    copyfile(SEGMENTS / source_name, OUTPUT / target_name)
