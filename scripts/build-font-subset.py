from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fontTools.merge import Merger
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont


ROOT = Path(__file__).resolve().parents[1]
FONT_PARTS = ROOT / "node_modules" / "@fontsource-variable" / "noto-sans-sc" / "files"
ASSET_DIRS = [
    ROOT / "apps" / "public-web" / "src" / "assets",
    ROOT / "apps" / "admin-web" / "src" / "assets",
]
SOURCE_SUFFIXES = {".vue", ".ts", ".css", ".html", ".py", ".md"}


def used_codepoints() -> set[int]:
    text = (
        "朗泰 LungTic 0123456789 "
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz "
        "，。；：！？、（）《》“”‘’·—…%+-/.#"
    )
    roots = [ROOT / "apps", ROOT / "server" / "app"]
    for source_root in roots:
        for path in source_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES:
                text += path.read_text(encoding="utf-8", errors="ignore")
    return {ord(character) for character in text}


def build_weight(wanted: set[int], weight: int) -> tuple[Path, int]:
    options = Options()
    options.hinting = False
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.name_languages = ["*"]

    with tempfile.TemporaryDirectory(prefix=f"lungtic-font-{weight}-") as temporary:
        selected: list[str] = []
        for index, source in enumerate(sorted(FONT_PARTS.glob("*-wght-normal.woff2"))):
            font = TTFont(source)
            instantiateVariableFont(font, {"wght": weight}, inplace=True)
            available = set(font.getBestCmap())
            keep = wanted.intersection(available)
            if not keep:
                font.close()
                continue
            subsetter = Subsetter(options=options)
            subsetter.populate(unicodes=keep)
            subsetter.subset(font)
            font.flavor = None
            target = Path(temporary) / f"{index:03d}.ttf"
            font.save(target)
            font.close()
            selected.append(str(target))

        if not selected:
            raise SystemExit("No matching font glyphs found.")
        merged = Merger().merge(selected)
        merged.flavor = "woff2"
        first = ASSET_DIRS[0] / f"noto-sans-sc-lungtic-{weight}.woff2"
        first.parent.mkdir(parents=True, exist_ok=True)
        merged.save(first)
        merged.close()
        for asset_dir in ASSET_DIRS[1:]:
            asset_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(first, asset_dir / first.name)
        return first, len(selected)


def build() -> None:
    if not FONT_PARTS.is_dir():
        raise SystemExit("Run npm install before building the font subset.")
    wanted = used_codepoints()
    for weight in (400, 700):
        output, shard_count = build_weight(wanted, weight)
        print(
            f"Wrote {output.name} with {len(wanted)} requested codepoints "
            f"from {shard_count} shards."
        )


if __name__ == "__main__":
    build()
