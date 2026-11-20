"""Build a local sign-off gallery from the images and optional pytest XML."""

import argparse
from collections import Counter
from html import escape
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree


def image_group(directory: Path, root: Path) -> tuple[str, int]:
    images = sorted(directory.glob("*.png"))
    title = escape(directory.name.removeprefix("test_").replace("_", " ").capitalize())
    cards = []
    for image in images:
        url = quote(image.relative_to(root).as_posix())
        label = escape(image.stem.replace("-", " "))
        cards.append(f'''<article><a href="{url}" target="_blank" rel="noopener">
          <img src="{url}" alt="{label}" loading="lazy"></a>
          <label><input type="checkbox" data-image="{url}"> {label}</label></article>''')
    return f'<section><h2>{title}</h2><div class="grid">{"".join(cards)}</div></section>', len(images)


def checks_without_images(report: Path, groups: set[str]) -> str:
    if not report.is_file():
        return ""
    cases = ElementTree.parse(report).iter("testcase")  # noqa: S314 - local pytest output
    counts = Counter()
    failures = set()
    for case in cases:
        name = case.attrib["name"].split("[", 1)[0]
        if name not in groups:
            counts[name] += 1
            if len(case):
                failures.add(name)
    items = []
    for name, count in sorted(counts.items()):
        title = escape(name.removeprefix("test_").replace("_", " "))
        status = " · see pytest results for status" if name in failures else " · passed"
        items.append(f"<li>{title} ({count}){status}</li>")
    return f'''<details><summary>Automated checks without images</summary>
      <ul>{"".join(items)}</ul></details>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Image output directory")
    args = parser.parse_args()
    root = args.directory.resolve()
    groups = [directory for directory in sorted(root.iterdir()) if directory.is_dir() and any(directory.glob("*.png"))]
    if not groups:
        parser.error(f"no review images found in {root}")
    sections = [image_group(directory, root) for directory in groups]
    total = sum(size for _, size in sections)
    text_checks = checks_without_images(root / "pytest-results.xml", {directory.name for directory in groups})
    content = "".join(section for section, _ in sections)
    (root / "index.html").write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PDF Watermark test review</title>
<style>
body{{font:16px/1.5 system-ui,sans-serif;background:#f4f2ed;color:#162234;margin:0}}
main{{max-width:1400px;margin:auto;padding:clamp(16px,4vw,48px)}}
h1{{font-size:clamp(26px,4vw,44px);margin:0}} h2{{margin:32px 0 12px;font-size:20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,235px),1fr));gap:14px}}
article{{border:1px solid #d5dce6;border-radius:8px;background:white;padding:10px;display:flex;flex-direction:column}}
article a{{background:#eef1f6;display:block;border-radius:4px}} img{{width:100%;height:190px;object-fit:contain;display:block}}
label{{display:flex;align-items:start;gap:8px;font-size:14px;padding:10px 2px 2px;overflow-wrap:anywhere;cursor:pointer}}
input{{accent-color:#2556ad}} article:has(input:checked){{border-color:#2556ad}}
details{{margin-top:28px;padding:12px 16px;background:#e7ebf1;border-radius:8px}} summary{{cursor:pointer}}
#progress{{font-weight:650;margin-bottom:20px}}
</style></head>
<body><main><h1>PDF Watermark test review</h1>
<p>Open an image to inspect it at full size. Tick the box when you’ve reviewed it.</p>
<p id="progress" aria-live="polite">0 of {total} images reviewed</p>
{content}{text_checks}</main>
<script>
const boxes = [...document.querySelectorAll('input[data-image]')];
const key = 'pdf-watermark-review:' + location.href;
let checked = [];
try {{ checked = JSON.parse(localStorage.getItem(key) || '[]'); }} catch {{ /* browser storage is optional */ }}
function update() {{
  const selected = boxes.filter(box => box.checked).map(box => box.dataset.image);
  document.getElementById('progress').textContent = selected.length + ' of ' + boxes.length + ' images reviewed';
  try {{ localStorage.setItem(key, JSON.stringify(selected)); }} catch {{ /* keep the current selection */ }}
}}
for (const box of boxes) {{ box.checked = checked.includes(box.dataset.image); box.addEventListener('change', update); }}
update();
</script></body></html>
''', encoding="utf-8")
    print(f"{total} images in {len(groups)} test groups. Gallery: {root / 'index.html'}")


if __name__ == "__main__":
    main()
