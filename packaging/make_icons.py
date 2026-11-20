"""
make_icons.py - Write the app icon in the formats each platform wants.

    python packaging/make_icons.py      (needs Pillow: pip install pillow)

The logo is packaging/icon.png (1024 px), the same page-with-three-lines mark
the website uses. This writes icon.ico (Windows) and icon.icns (macOS) from it.
The results are committed, so building the app does not need Pillow - only
re-running this after changing the logo does.
"""

from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent


def main() -> None:
    img = Image.open(HERE / "icon.png").convert("RGBA")
    img.save(HERE / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    img.save(HERE / "icon.icns")
    print("wrote icon.ico, icon.icns")


if __name__ == "__main__":
    main()
