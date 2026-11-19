# PDF Watermark

PDF Watermark puts each recipient's name on every page of their own copy of your PDFs.

**[Download for Windows](https://github.com/FZ-Labz/pdf-watermark/releases/latest/download/PDF-Watermark-Windows.exe)**
Windows 10 and 11, free, no install, works offline.

![The Design screen: recipients on the left, a preview of the marked page on the right](docs/screenshots/design.png)

## What it does

- Makes one marked copy of your files for each recipient.
- Handles a whole folder at once, including subfolders.
- Shows a live preview before you export.
- Lets you choose the font, colour and size, and a diagonal, tiled or placed mark.
- Never changes your originals. Nothing leaves your computer.

## How to use it

1. Add your PDFs, or a whole folder.
2. Add the recipients, then pick how the mark looks.
3. Check the preview for each recipient.
4. Click Watermark. Each recipient gets a new set of PDFs.

## Requirements

Windows 10 or 11. There is nothing to install.

The app is not code-signed yet. The first time you open it, Windows may say "Windows protected your PC". Click **More info**, then **Run anyway**.

## Help

- If the app flags a PDF as damaged or password-protected, save a readable copy in a PDF editor and add that copy instead.
- If something goes wrong, open an [issue](https://github.com/FZ-Labz/pdf-watermark/issues). You can attach the log at `%APPDATA%\PDF Watermark\app.log`.
- A watermark shows who got a copy. It does not stop anyone opening the file. To restrict access, use encryption.

**Privacy:** your documents are processed on your computer. The app keeps its settings in `%APPDATA%\PDF Watermark`. To uninstall, delete the `.exe` and, if you like, that folder.

## For developers

- Run from source, project layout and release steps: [CONTRIBUTING.md](CONTRIBUTING.md).
- Command line: `python batch_watermark.py my_folder --company "Acme" "Globex"`. All options are in [CONTRIBUTING.md](CONTRIBUTING.md#command-line-options).
- Licence: MIT, see [LICENSE](LICENSE). The app bundles [PyMuPDF](https://pymupdf.readthedocs.io/) under the [GNU AGPL v3](https://www.gnu.org/licenses/agpl-3.0.html), so the app as distributed is covered by the AGPL. Its source is this repository.
- Thanks to [PyMuPDF](https://pymupdf.readthedocs.io/), [fontTools](https://github.com/fonttools/fonttools) and [pywebview](https://pywebview.flowrl.com/), and to the open-source watermark tools that gave me ideas: [bastienlc/pdf-watermark](https://github.com/bastienlc/pdf-watermark), [ajaxray/markpdf](https://github.com/ajaxray/markpdf), [oclero/pdfwm](https://github.com/oclero/pdfwm), [aanorlondo/pdf-watermark](https://github.com/aanorlondo/pdf-watermark), [TobseF/My-PDF-Watermark](https://github.com/TobseF/My-PDF-Watermark).
