"""
make_icons.py - Draw the app icon and write it in the formats each platform wants.

    python packaging/make_icons.py      (needs Pillow: pip install pillow)

Writes icon.png (1024 px), icon.ico (Windows) and icon.icns (macOS) next to
this file. The results are committed, so building the app does not need
Pillow - only re-running this after changing the design does.
"""

from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
S = 1024
X = 4  # drawn at 4x, then scaled down, for smooth edges


PAPER = "#eff6ff"
FOLD = "#9bc4fb"
MARK = "#1863c6"


def draw() -> Image.Image:
    """Draw a folded PDF page with a diagonal watermark."""
    n = S * X
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    left, top, right, bottom = n * 0.17, n * 0.06, n * 0.83, n * 0.94
    fold = n * 0.20
    d.polygon([(left, top), (right - fold, top), (right, top + fold), (right, bottom), (left, bottom)],
              fill=PAPER)
    d.polygon([(right - fold, top), (right - fold, top + fold), (right, top + fold)], fill=FOLD)

    d.polygon([(n * 0.30, n * 0.63), (n * 0.67, n * 0.42),
               (n * 0.73, n * 0.53), (n * 0.36, n * 0.74)], fill=MARK)
    return img.resize((S, S), Image.LANCZOS)


def main() -> None:
    img = draw()
    img.save(HERE / "icon.png")
    img.save(HERE / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    img.save(HERE / "icon.icns")
    print("wrote icon.png, icon.ico, icon.icns")


if __name__ == "__main__":
    main()
