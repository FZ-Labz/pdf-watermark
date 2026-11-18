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


# INSITE DC brand colours.
GREIGE = (0xD7, 0xD6, 0xCC)
FOLD = (0x9A, 0xA1, 0x9F)       # a shade darker than Greige
MIDNIGHT = (0x0A, 0x24, 0x35)


def draw() -> Image.Image:
    """
    A Greige document with a folded corner, and inside it the three bars
    that form the "E" of the INSITE DC wordmark, in Midnight. No tile behind
    it, so the page shape itself is the icon. Square corners, as in the brand.
    """
    n = S * X
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    left, top, right, bottom = n * 0.17, n * 0.06, n * 0.83, n * 0.94
    fold = n * 0.20
    d.polygon([(left, top), (right - fold, top), (right, top + fold), (right, bottom), (left, bottom)],
              fill=GREIGE + (255,))
    d.polygon([(right - fold, top), (right - fold, top + fold), (right, top + fold)], fill=FOLD + (255,))

    # The E: three equal bars, centred a little below the middle of the page.
    bar_left, bar_right = n * 0.31, n * 0.69
    height, gap = n * 0.075, n * 0.07
    first = n * 0.555 - (3 * height + 2 * gap) / 2
    for i in range(3):
        y = first + i * (height + gap)
        d.rectangle([bar_left, y, bar_right, y + height], fill=MIDNIGHT + (255,))
    return img.resize((S, S), Image.LANCZOS)


def main() -> None:
    img = draw()
    img.save(HERE / "icon.png")
    img.save(HERE / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    img.save(HERE / "icon.icns")
    print("wrote icon.png, icon.ico, icon.icns")


if __name__ == "__main__":
    main()
