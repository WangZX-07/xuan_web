"""Generate a deterministic, visibly synthetic thorax phantom for UI review.

This is not patient data and is not suitable for model or clinical evaluation.
The output exists only so design comps can show the real LungTic viewer without
using generated medical imagery or exposing private data.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
UI_ROOT = ROOT / "ui"
sys.path.insert(0, str(UI_ROOT))

from tici.tici_io import TiciWriter  # noqa: E402


PHASES = 10
SLICES = 36
SIZE = 256


def ellipse(x: np.ndarray, y: np.ndarray, cx: float, cy: float, rx: float, ry: float) -> np.ndarray:
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1


def make_phase(phase: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(20260921 + phase)
    yy, xx = np.mgrid[-1:1:complex(SIZE), -1:1:complex(SIZE)]
    volume = np.zeros((SLICES, SIZE, SIZE), dtype=np.float32)
    masks = np.zeros_like(volume, dtype=np.uint8)
    centers = np.zeros((SLICES, 3), dtype=np.float32)

    angle = 2 * math.pi * phase / PHASES
    respiratory_shift = 0.055 * math.sin(angle)
    lateral_shift = 0.018 * math.cos(angle)

    for z in range(SLICES):
        zn = (z - (SLICES - 1) / 2) / ((SLICES - 1) / 2)
        slice_img = np.full((SIZE, SIZE), 0.015, dtype=np.float32)

        body_rx = 0.78 * math.sqrt(max(0.22, 1 - 0.25 * zn * zn))
        body_ry = 0.87 * math.sqrt(max(0.2, 1 - 0.18 * zn * zn))
        body = ellipse(xx, yy, 0, 0.04, body_rx, body_ry)
        slice_img[body] = 0.54

        lung_scale = math.sqrt(max(0.12, 1 - 0.72 * zn * zn))
        lung_ry = 0.58 * lung_scale * (1 + respiratory_shift * 0.32)
        lung_rx = 0.29 * lung_scale
        lung_y = -0.03 - respiratory_shift
        left_lung = ellipse(xx, yy, -0.31, lung_y, lung_rx, lung_ry)
        right_lung = ellipse(xx, yy, 0.31, lung_y, lung_rx, lung_ry)
        lungs = (left_lung | right_lung) & body
        slice_img[lungs] = 0.13

        mediastinum = ellipse(xx, yy, 0, 0.08, 0.18, 0.52 * lung_scale)
        slice_img[mediastinum & body] = 0.6

        heart = ellipse(xx, yy, -0.08, 0.27, 0.22, 0.23 * max(0.55, lung_scale))
        slice_img[heart & body] = 0.64

        spine = ellipse(xx, yy, 0.0, 0.68, 0.105, 0.105)
        canal = ellipse(xx, yy, 0.0, 0.68, 0.036, 0.036)
        slice_img[spine & body] = 0.88
        slice_img[canal & body] = 0.35

        # Simplified ribs: deterministic, symmetric high-density arcs.
        radial = np.sqrt((xx / 0.72) ** 2 + ((yy - 0.03) / 0.8) ** 2)
        rib_band = body & (radial > 0.91) & (radial < 0.955)
        rib_gate = (np.cos(np.arctan2(yy, xx) * 8 + z * 0.14) > 0.36)
        slice_img[rib_band & rib_gate] = 0.84

        # A moving synthetic target in the right lung.
        tumor_z = 0.1 + 0.08 * math.sin(angle)
        tumor_visible = abs(zn - tumor_z) < 0.24
        tumor_x = 0.34 + lateral_shift
        tumor_y = 0.03 + respiratory_shift * 1.4
        tumor_r = 0.063 * math.sqrt(max(0.05, 1 - ((zn - tumor_z) / 0.24) ** 2))
        if tumor_visible and tumor_r > 0.012:
            target = ellipse(xx, yy, tumor_x, tumor_y, tumor_r, tumor_r * 0.86) & right_lung
            slice_img[target] = 0.72
            masks[z, target] = 1

        # Texture is deliberately mild so the phantom remains visibly synthetic.
        texture = rng.normal(0, 0.014, (SIZE, SIZE)).astype(np.float32)
        slice_img[body] += texture[body]
        slice_img = np.clip(slice_img, 0, 1)
        volume[z] = slice_img

        centers[z] = [z, (tumor_y + 1) * 0.5 * (SIZE - 1), (tumor_x + 1) * 0.5 * (SIZE - 1)]

    return volume, masks, centers


def to_preview(image: np.ndarray, mask: np.ndarray, phase: int) -> Image.Image:
    base = np.clip(image * 255, 0, 255).astype(np.uint8)
    rgb = np.stack([base, base, base], axis=-1)
    overlay = mask.astype(bool)
    rgb[overlay, 0] = 239
    rgb[overlay, 1] = (rgb[overlay, 1] * 0.35).astype(np.uint8)
    rgb[overlay, 2] = (rgb[overlay, 2] * 0.35).astype(np.uint8)
    panel = Image.fromarray(rgb, "RGB").resize((512, 512), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (512, 566), "#07111f")
    canvas.paste(panel, (0, 54))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((18, 16), f"SYNTHETIC THORAX PHANTOM / PHASE {phase:02d}", fill="#dcecff", font=font)
    draw.text((18, 34), "UI REVIEW ONLY - NOT PATIENT DATA", fill="#65b4f2", font=font)
    return canvas


def main() -> None:
    runtime = ROOT / "lungtic-website" / ".review-runtime"
    asset_dir = ROOT / "lungtic-website" / "design-review" / "assets"
    runtime.mkdir(parents=True, exist_ok=True)
    asset_dir.mkdir(parents=True, exist_ok=True)

    output_tici = runtime / "synthetic-lung-demo.tici"
    union_mask = np.zeros((SLICES, SIZE, SIZE), dtype=np.uint8)
    phase_centroids: list[np.ndarray] = []
    preview_frames: list[Image.Image] = []

    with TiciWriter(str(output_tici), "w") as writer:
        writer.write_metadata(
            {
                "patient_id": "SYNTHETIC-ONLY",
                "patient_name": "UI^PHANTOM",
                "patient_sex": "",
                "patient_age": "",
            },
            {
                "study_uid": "LUNGTIC.SYNTHETIC.UI.REVIEW",
                "study_date": "20260921",
                "modality": "CT-PHANTOM",
                "phase_count": PHASES,
                "rows": SIZE,
                "cols": SIZE,
                "slice_count": SLICES,
                "pixel_spacing": [1.25, 1.25],
                "slice_thickness": 2.5,
                "slice_locations": [float(i * 2.5) for i in range(SLICES)],
            },
        )

        for phase in range(PHASES):
            volume, masks, centers = make_phase(phase)
            writer.write_phase_images(phase, volume, masks)
            union_mask = np.maximum(union_mask, masks)
            phase_centroids.append(centers[masks.reshape(SLICES, -1).any(axis=1)].mean(axis=0))
            if phase in (0, 3, 6, 9):
                preview_frames.append(to_preview(volume[SLICES // 2], masks[SLICES // 2], phase))

        centroids = np.stack(phase_centroids).astype(np.float32)
        writer.write_igtv(union_mask, "", float(union_mask.sum() * 1.25 * 1.25 * 2.5 / 1000), "synthetic-union")
        writer.write_trajectory(centroids, centroids[:7], centroids[7:], "synthetic-motion-path")
        writer.write_provenance(
            {
                "source_type": "deterministic_synthetic_thorax_phantom",
                "source_files_count": 0,
                "converter_version": "LungTic-UI-Review-1.0",
                "conversion_date": "2026-09-21T00:00:00+08:00",
                "model_version": "NONE-NOT-A-MODEL-OUTPUT",
            }
        )

    contact = Image.new("RGB", (1024, 1132), "#07111f")
    for index, frame in enumerate(preview_frames):
        contact.paste(frame, ((index % 2) * 512, (index // 2) * 566))
    contact.save(asset_dir / "synthetic-tici-preview.png", optimize=True)

    print(output_tici)
    print(asset_dir / "synthetic-tici-preview.png")


if __name__ == "__main__":
    main()
