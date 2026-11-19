# PDF Watermark

**Free offline PDF watermark for Windows, one copy per recipient.**

Sending a tender pack, issued drawings, or a report to several companies? Put
each recipient’s name on every page of their copy. Add one PDF or a whole folder,
preview the marks, and export separate sets without changing your originals.
Everything is processed on your computer.

**[Download PDF Watermark for Windows](https://github.com/FZ-Labz/pdf-watermark/releases/latest/download/PDF-Watermark-Windows.exe)** · Windows 10 and 11 · Portable `.exe` · [Release notes and SHA-256 checksums](https://github.com/FZ-Labz/pdf-watermark/releases/latest)

[Browse all four app screenshots](https://fz-labz.github.io/pdf-watermark/#walkthrough)

[![The Design screen shows recipient settings next to a drawing with a diagonal company watermark.](docs/screenshots/design.png)](https://fz-labz.github.io/pdf-watermark/#walkthrough)

## What it does

- **One copy per recipient.** Add multiple companies and get a separately marked set for each. Save the companies you use often on your computer for the next run.
- **Whole folders at once.** Scan subfolders and preserve their structure in the output. Damaged or password-protected PDFs are flagged when you add them.
- **Live preview.** Switch recipients and pages to check the watermark before exporting. Choose diagonal, tiled, or positioned text stamps with your own font, colour, size, and opacity.
- **Mixed sizes and orientations.** The app sizes each mark to its page, from A4 reports to large CAD sheets, including rotated or cropped pages.

## Watermark your first pack

1. **Add files.** Drag a PDF or folder onto the app, or use **Select files** or **Select folder**. Check the Files step for any PDFs that were skipped.
2. **Design.** Add the recipients and choose how the marks look. Select each company in the preview to check its copy.
3. **Export.** Check the output list, choose a destination, and click **Watermark**. The app creates new PDFs and keeps the originals.

Press <kbd>?</kbd> in the app for keyboard shortcuts. Watermark text supports
`{date}`, `{page}`, `{pages}`, and `{file}` placeholders. The optional
**Extra protection** setting rasterizes pages, which makes the watermark harder
to remove and removes selectable page text.

<details>
<summary>See watermark styling examples</summary>

![A sample page with diagonal, stacked, tiled, positioned, and outlined text watermarks](docs/options.png)

The mark is sized for each page, so a single run can include different sizes.

![The same watermark on an A4 page and an A3 drawing](docs/page-sizes.png)

</details>

## Download and run

Download [`PDF-Watermark-Windows.exe`](https://github.com/FZ-Labz/pdf-watermark/releases/latest/download/PDF-Watermark-Windows.exe)
and open it on Windows 10 or 11. No installation or account is needed. Find
older versions on the [Releases page](https://github.com/FZ-Labz/pdf-watermark/releases).

The v1.1.0 Windows executable is unsigned, so Windows SmartScreen may show a
first-launch warning. The release includes `SHA256SUMS.txt` so you can compare
the download with the published checksum.

## Command line and source

The command-line tool runs on Windows, macOS, and Linux with Python 3.10 or later.
For installation, the project layout, and development instructions, see
[CONTRIBUTING.md](CONTRIBUTING.md).

```sh
# Make a separate set for each company
python batch_watermark.py my_folder --company "Acme" "Globex"

# Use placeholders in custom text
python batch_watermark.py report.pdf --text "DRAFT - {date} - page {page} of {pages}"

# Preview the output paths without writing files
python batch_watermark.py my_folder --company Acme --dry-run
```

Run `python batch_watermark.py --help` for usage or `python examples/make_sample.py`
to generate a practice document.

<details closed><summary>Every option</summary>

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

</details>

## Help

- If the app flags a PDF as damaged or password-protected, open it in a PDF editor where you have permission to access it, save a readable copy, and add that copy.
- The app logs errors to `%APPDATA%\PDF Watermark\app.log`. You can attach the log when opening an [issue](https://github.com/FZ-Labz/pdf-watermark/issues).
- Use a watermark to indicate who received a copy. If you need to restrict who can open a PDF, use encryption or a rights-management system.

## 🔏 Code signing policy

The [release workflow](.github/workflows/release.yml) builds the executable on
GitHub Actions from this repository and generates the published SHA-256 checksum.
Code signing is planned.

## 🔒 Privacy and uninstalling

**Privacy policy:** This program will not transfer any information to other
networked systems unless specifically requested by the user or the person
installing or operating it. Your documents are processed entirely on your own
computer. The only time the app goes online is if you click *Need help?*,
which opens this page in your web browser.

**What it changes on your computer:** nothing is installed. The app keeps its
settings, the companies you choose to save, a font list and a small log in one
folder: `%APPDATA%\PDF Watermark` on Windows.

**Uninstalling:** delete `PDF-Watermark-Windows.exe`, and if you want to remove
your settings and saved companies too, delete the `%APPDATA%\PDF Watermark`
folder (paste that into the File Explorer address bar to find it).

## Roadmap

- macOS desktop app
- Code-signed Windows builds
- Image and logo watermarks
- Password entry for protected PDFs
- Parallel exports

## 📄 License

The code in this repository is licensed under the `MIT` License. See the [LICENSE](LICENSE) file for additional info.

The downloadable app bundles [PyMuPDF](https://pymupdf.readthedocs.io/), which is
licensed under the [GNU AGPL v3](https://www.gnu.org/licenses/agpl-3.0.html), so the
app as distributed is covered by the AGPL's terms; its complete source is this repository.

---

## 👏 Acknowledgments

- [PyMuPDF](https://pymupdf.readthedocs.io/) — reading, drawing on and writing PDFs
- [fontTools](https://github.com/fonttools/fonttools) — reading and subsetting fonts
- [pywebview](https://pywebview.flowrl.com/) — the app window
- Ideas borrowed from other open-source watermarking tools:
  [bastienlc/pdf-watermark](https://github.com/bastienlc/pdf-watermark),
  [ajaxray/markpdf](https://github.com/ajaxray/markpdf),
  [oclero/pdfwm](https://github.com/oclero/pdfwm),
  [aanorlondo/pdf-watermark](https://github.com/aanorlondo/pdf-watermark) and
  [TobseF/My-PDF-Watermark](https://github.com/TobseF/My-PDF-Watermark)
