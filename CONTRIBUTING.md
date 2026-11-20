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
│   └── release.yml         # releases the app when a merge to main changes it
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

Releases are automatic. When a pull request that changes the app (the top-level
Python files, `ui/`, `packaging/`, `requirements.txt` or `VERSION`) is merged
into `main`, the [release workflow](.github/workflows/release.yml) runs the
tests, builds and installs the app with Velopack, tags the commit with the next
patch version and publishes it. Installed copies then offer the update. Raise
`VERSION` in the pull request (for example to `1.3.0`) for a bigger step than a
patch. Website, README and test-only changes don't make a release.

## Update the website images and branding

The landing page is plain HTML, CSS and JavaScript in `docs/`. Replacing an image under its existing filename updates every page reference when GitHub Pages deploys.

| To change | Files and edits |
| --- | --- |
| App screenshots | Replace the original-size PNGs `files.png`, `design.png`, `export.png` and `done.png` in `docs/screenshots/`. The README uses the same `design.png`. In the **Gallery source** block of `docs/index.html`, each link holds its image path, label, caption and alt text. Edit or duplicate one link to change the gallery. Keep the initially selected preview and its fallback image in sync when renaming that file. |
| Sample drawing and recipients | Replace the three WebP files in `docs/prints/` with images of real recipient exports. The **Recipient previews** block in `docs/index.html` holds the full-size links, recipient names and drawing description. Update the initial image, its alt text and the sheet reference when changing the sample drawing. |
| Header logo and browser icon | Replace `docs/media/app-icon.png` with the square transparent product icon. The header and favicon both use this file. |
| Name, colours and typography | Edit the product name and search/social text in `docs/index.html` and the name in `README.md`. The principal colours and fonts are in the `:root` block at the top of `docs/styles.css`. Match the HTML `theme-color` to the navy background. |
| Social preview | Replace `docs/media/pdf-watermark-share.png`, currently 1280 × 640. Update `og:image:alt` to describe the new card. If its size or URL changes, update the matching `og:image` tags in the HTML head. |
| README illustrations | Update `docs/options.png` and `docs/page-sizes.png` and their descriptions in `README.md`. |

Open `docs/index.html` locally, select each screenshot and recipient, and check the full-size links. On a narrow screen, confirm the logo and gallery controls fit. The repository publishes from **Settings → Pages → Deploy from a branch → main → /docs**. Its **About** website points to [the public landing page](https://fz-labz.github.io/pdf-watermark/).

## Command line options

Run `python batch_watermark.py --help` for usage, or `python examples/make_sample.py` to make a practice document. Watermark text supports `{date}`, `{page}`, `{pages}` and `{file}` placeholders.

| Flag | Default | What it does |
| --- | --- | --- |
| `--text`, `-t` | — | Watermark text. Repeat for one set of copies per text. Placeholders: `{date}` `{page}` `{pages}` `{file}`. |
| `--company`, `-c` | — | Each name becomes `CONFIDENTIAL - <name>`. |
| `--prefix` | `CONFIDENTIAL` | What `--company` puts before each name; `""` for the name alone. |
| `--layout` | `diagonal` | `diagonal`, `tile`, or `position` for a small stamp. |
| `--position` | `bottom-center` | Where a stamp goes: `top-left` … `bottom-right`, `center`, or `X,Y` fractions like `0.8,0.1`. |
| `--stack` | off | Put the name on its own line under the prefix. |
| `--font` | `Helvetica` | `Helvetica`, `Times`, `Courier`, or any installed font such as `"Georgia"`. |
| `--bold` / `--no-bold`, `--italic` | bold | Font style. |
| `--color` | grey | A name (`red`, `blue`, `black`, `green`, `grey`) or a hex code like `#cc0000`. |
| `--opacity` | `0.4` | `0` invisible, `1` fully opaque. |
| `--size` | `100` | Percent of the automatic size (up to 400 for stamps). |
| `--angle` | `diagonal` | Degrees, or `diagonal` for corner to corner on every page. |
| `--tile N` | — | Shorthand for `--layout tile` with N bands. |
| `--outline` | off | Hollow letters. |
| `--flatten [DPI]` | off | Turn pages into images so the mark can't be removed. |
| `--out`, `-o` | next to each source | Where output is written. |
| `--suffix` | `_Watermarked` | Appended to each output folder name. |
| `--dry-run` | off | Print what would be written, write nothing. |

The exit code is `0` when every file succeeded and `1` if any failed, so it can sit in a script.

## Roadmap

- macOS desktop app
- Code-signed Windows builds
- Image and logo watermarks
- Password entry for protected PDFs
- Parallel exports
