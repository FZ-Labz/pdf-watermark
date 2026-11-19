# Contributing to PDF Watermark

## Run from source

Use Python 3.10 or later on Windows, macOS, or Linux. Clone the repository and
install its development dependencies.

```sh
git clone https://github.com/FZ-Labz/pdf-watermark.git
cd pdf-watermark
pip install -r requirements-dev.txt
```

Run `python app.py` to open the desktop application, or run
`python batch_watermark.py --help` for the command-line options. Use
`python examples/make_sample.py` to generate a practice document.

## Make a change

1. Fork the repository and create a branch with a descriptive name.
2. Make the change and add a regression test if needed.
3. Run `python -m pytest` and `ruff check .`.
4. Open a pull request with a brief description of the change and your checks.

Generate test PDFs with the test suite instead of committing real documents.

## Project structure

```bash
pdf-watermark
├── app.py                  # the desktop app: a window around the engine
├── batch_watermark.py      # the command line
├── watermark.py            # the engine: geometry, rotation, drawing, saving
├── fonts.py                # built-in and installed fonts
├── ui
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── tests
│   ├── conftest.py
│   ├── test_engine.py
│   └── test_batch.py
├── examples
│   └── make_sample.py      # a sample document to practise on
├── docs
│   ├── make_figures.py     # generates the example figures
│   ├── screenshots
│   └── media               # product demo and social preview assets
├── packaging
│   ├── pdf-watermark.spec  # PyInstaller build
│   ├── make_icons.py
│   └── icon.png / .ico / .icns
├── .github/workflows
│   ├── ci.yml              # tests on every push
│   └── release.yml         # builds and publishes the app on a version tag
├── requirements.txt
├── requirements-dev.txt
├── VERSION
└── LICENSE
```

## Modules

<details closed><summary>Root</summary>

| File | Summary |
|:---|:---|
| [app.py](app.py) | The desktop app. Opens a window (pywebview) showing the interface in `ui/`, and gives it a bridge to Python: picking files, checking each PDF can be read, rendering previews, listing fonts, running the export on a background thread, and remembering settings and saved companies. Keeps a log for diagnosing problems on someone else's computer. |
| [watermark.py](watermark.py) | The engine. Works out the font size, angle and position for each page from its own geometry; brings rotated pages to a rotation-free state while keeping their crop boxes; fences off CAD drawings' stray transforms; draws the text; fills in placeholders; flattens pages to images on request; and saves through a temporary file so a failed run never leaves a half-written PDF. |
| [fonts.py](fonts.py) | Finds the fonts installed on Windows, macOS or Linux, groups them into families with their bold and italic styles, and embeds only the characters a watermark uses, so a copy grows by kilobytes rather than megabytes. |
| [batch_watermark.py](batch_watermark.py) | The command line. Collects PDFs from files and folders (case-insensitively, skipping macOS metadata files), names every output so nothing overwrites anything else, and applies one or many watermark texts in a run. |

</details>

<details closed><summary>ui</summary>

| File | Summary |
|:---|:---|
| [index.html](ui/index.html) | The three steps — Files, Design, Export — plus the shortcuts sheet. |
| [styles.css](ui/styles.css) | The dark theme: the spotlight step bar, cards, toolbar, menus and tooltips. |
| [app.js](ui/app.js) | Everything the interface does. Talks to `app.py`, or to a built-in mock with sample data when opened in a plain browser — handy for design work (`?demo=design`). |

</details>

<details closed><summary>tests</summary>

| File | Summary |
|:---|:---|
| [test_engine.py](tests/test_engine.py) | Renders watermarked pages and checks where the ink actually lands: centred on every page size and rotation, in the right corner for every stamp position, pixel-identical page content after de-rotation, kept bookmarks and links, restrictions, fonts, flattening. |
| [test_batch.py](tests/test_batch.py) | Finding PDFs, naming outputs, and the command line run end to end — including recipient names in Polish and Japanese. |

</details>

<details closed><summary>packaging & docs</summary>

| File | Summary |
|:---|:---|
| [pdf-watermark.spec](packaging/pdf-watermark.spec) | Builds the single-file Windows `.exe` (and a macOS `.app`, for later). |
| [make_icons.py](packaging/make_icons.py) | Draws the app icon in each platform's format. |
| [make_figures.py](docs/make_figures.py) | Draws the example images in this README with the real engine, so they always match what the tool produces. |

</details>

## Build and release

```sh
pyinstaller packaging/pdf-watermark.spec --noconfirm
```

To release a new version, update and commit `VERSION`, then push a matching
version tag. The [release workflow](.github/workflows/release.yml) runs the tests,
builds `PDF-Watermark-Windows.exe`, and publishes it with a SHA-256 checksum.

