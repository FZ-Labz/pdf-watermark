# PDF Watermark handover

This document is for whoever looks after PDF Watermark next. It covers what the app does, how it's built, how to release a new version, and what's still open.

Written November 2026 by Fahim. Up to date as of version 1.2.0.

## Still to decide

These are open and only Fahim can settle them:

- **Who is taking over?** Another developer, or the office team who use it day to day. This document is written for a developer.
- **Do they need access to the code?** Either add them as a collaborator on the repository, or transfer the repository to them or to an organisation. See "Accounts and access" below.

## What the app does

PDF Watermark is a free Windows app that stamps a watermark on every page of a batch of PDFs. You can add single files or a whole folder, including subfolders. It saves marked copies in the same folder structure and never changes the originals.

It was built for INSITE DC to mark drawing packs before sending them out. A typical use is adding `CONFIDENTIAL - <company name>`, with one separately marked set for each recipient.

Everything runs offline on the user's PC. The app keeps its settings, saved companies and log file in `%APPDATA%\PDF Watermark`.

The same engine also runs as a command-line tool (`batch_watermark.py`), so it can be scripted.

## Where things live

| What | Where |
| --- | --- |
| Code | https://github.com/FZ-Labz/pdf-watermark (public) |
| Download link to share | https://github.com/FZ-Labz/pdf-watermark/releases/latest/download/PDF-Watermark-Setup.exe (always the newest version) |
| All releases | https://github.com/FZ-Labz/pdf-watermark/releases |
| Website | https://fz-labz.github.io/pdf-watermark/ (GitHub Pages, served from the `docs/` folder on `main`) |
| Bug reports | GitHub Issues on the repository |
| Licence | MIT for this code. The app bundles PyMuPDF, which is AGPL v3, so the app as shipped is AGPL. |

## How it's built

- **Language:** Python 3.10 or later. Releases are built with Python 3.12.
- **PDF work:** [PyMuPDF](https://pymupdf.readthedocs.io/) for reading, drawing and saving, and [fontTools](https://github.com/fonttools/fonttools) for embedding just the characters a watermark needs.
- **Window:** [pywebview](https://pywebview.flowrl.com/). The interface is plain HTML, CSS and JavaScript in `ui/`, shown in a native window. `app.py` is the bridge between the page and Python.
- **Packaging:** [PyInstaller](https://pyinstaller.org/), using `packaging/pdf-watermark.spec`.
- **Installer and updates:** [Velopack](https://velopack.io/), from version 1.2.0. The release build packs the app with Velopack's `vpk` tool, which needs the .NET 8 SDK. GitHub Actions installs it for releases, and it's also installed on Fahim's PC for local builds.
- **CI:** GitHub Actions. `ci.yml` runs the linter and tests on every push and pull request. `release.yml` builds and publishes a new release by itself whenever a merge into `main` changes the app.

## The files that matter

| File or folder | What it is |
| --- | --- |
| `app.py` | The desktop app. Opens the window, handles file picking, previews, settings and running the export in the background. |
| `watermark.py` | The engine. Works out size, angle and position for each page, handles rotated pages and CAD drawings, draws the text and saves safely. |
| `fonts.py` | Finds installed fonts and embeds only what's needed. |
| `batch_watermark.py` | The command-line tool. |
| `updater.py` | Velopack install hooks and the in-app update check. |
| `ui/` | The interface: `index.html`, `styles.css`, `app.js`. Opening `ui/index.html` in a normal browser shows it with sample data, which is handy for design work. |
| `tests/` | The test suite. |
| `packaging/` | PyInstaller spec, app icons, the script that draws the icons, and Windows version info. |
| `docs/` | The website, plus screenshots and images used by the README. |
| `examples/make_sample.py` | Makes a practice PDF. |
| `next-steps/microsoft-store.md` | A checklist for publishing to the Microsoft Store. Not started. |
| `VERSION` | The lowest version the next release can have. Releases normally just add one to the patch number; raise this to `1.3.0` or `2.0.0` for a bigger step. |
| `CONTRIBUTING.md` | More detail on the code, the command-line options and the website images. |

Fahim's local copy also has some untracked files (`desktop_app.py`, `desktop_core.py`, `preview_worker.py`, `presets.py`, `test_desktop.py`, `build_exe.py` and others). These are an old PySide6 prototype from September 2026 and aren't used. They are not in the repository.

## Run it from source

You need Python 3.10 or later and Git.

```sh
git clone https://github.com/FZ-Labz/pdf-watermark.git
cd pdf-watermark
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python app.py
```

To try the command line:

```sh
python batch_watermark.py --help
python examples/make_sample.py
```

## Run the tests

```sh
python -m pytest tests
ruff check .
```

Point pytest at `tests` rather than the whole folder. If the old prototype files are lying around, `test_desktop.py` gets picked up and breaks one of the real tests.

The tests render watermarked pages and check where the ink actually lands, so they catch layout mistakes, not just crashes. CI runs them on Windows, macOS and Linux with Python 3.10 to 3.13.

## Build the app on your own PC

```sh
pip install pyinstaller
pyinstaller packaging/pdf-watermark.spec --noconfirm
```

This makes a folder, `dist\PDF Watermark\`, with `PDF Watermark.exe` inside. To turn it into an installer like the release one, install the .NET 8 SDK and `vpk` (`dotnet tool install -g vpk`), then run the `vpk pack` command from `.github/workflows/release.yml`.

You don't need to build locally to release. GitHub Actions does the release build.

## Make a change

`main` is protected. You can't push to it directly, so every change goes through a pull request:

1. Create a branch, make the change, and push the branch.
2. Open a pull request. The **Tests** workflow runs on it.
3. Fahim (or whoever owns the repository) reviews and merges it.

## Release a new version

There's nothing extra to do. Merging a pull request that changes the app into `main` releases it. "The app" means the Python files in the top folder, `ui/`, `packaging/`, `requirements.txt` and `VERSION`. Changes only to the website (`docs/`), the README, these notes or the tests don't make a release.

1. Merge the pull request.
2. The **Release** workflow starts on its own. It:
   - runs the tests
   - picks the version: the newest release with one added to the patch number (1.2.0 becomes 1.2.1), or `VERSION` if that's higher. For a bigger step, raise `VERSION` to `1.3.0` or `2.0.0` in the pull request.
   - builds the app with PyInstaller and packs it with Velopack
   - installs it with the real `PDF-Watermark-Setup.exe`, as a user would, and opens the installed app in self-test mode. If it doesn't install or its window doesn't come up working, nothing is published.
   - tags the merged commit (for example `v1.2.1`) and publishes the GitHub Release
3. Check the Actions tab on GitHub until it goes green, then check the Releases page. Everyone with the app installed sees the new version the next time they open it.

To release without an app change, open the **Release** workflow on the Actions tab and click **Run workflow** on `main`. Pushing a tag such as `v1.4.0` also still releases that exact version.

What each release contains:

- `PDF-Watermark-Setup.exe`, the file people download and run. It installs per user, with no admin rights, into `%LOCALAPPDATA%\PDFWatermark` and adds Start menu and desktop shortcuts.
- `PDFWatermark-win-Portable.zip`, a portable copy for anyone who can't run installers.
- A `.nupkg` file, `releases.win.json` and `RELEASES`. Installed copies read these to update themselves. Don't delete them from old releases, because they're used to build small delta updates.

The installed app checks for a newer release when it opens and every 2 minutes while it stays open. If there is one, a card appears in the top-right corner, on whichever step is showing, with an **Update now** button. The app downloads the update, restarts by itself, and shows "You're now on version …" once. The version is always shown next to the app name in the header, and Windows Settings → Apps shows the same number. Settings in `%APPDATA%` are kept across updates.

To keep within GitHub's limit of 60 API calls an hour per internet connection, each check first reads the small `releases.win.json` file from the latest release's downloads, which doesn't count towards that limit. It only calls the API once there's actually something new.

To test an update without publishing one, build a version into a folder with `vpk pack` and start the installed app with `PDF_WATERMARK_UPDATE_URL` set to that folder. Velopack ignores labels like `-test.1`, so `1.2.1-test.1` counts as `1.2.1`. Give test builds a real number below the next release.

If you upgrade Velopack, change the version in two places together: `velopack==…` in `requirements.txt` and `VPK_VERSION` in `.github/workflows/release.yml`.

## Release status right now

- **Latest release:** v1.2.0 (20 November 2026), the first with the Velopack installer and in-app updates.
- **The website and README** both link their Download button to `PDF-Watermark-Setup.exe`, with the Keep and Run anyway steps for the security warnings.
- **People still on 1.1.1 or earlier** have the old portable exe, which can't update itself. They need to download `PDF-Watermark-Setup.exe` once. After that, updates come through the app.
- **Pull request #2** (`codex/windows-installer`) was an earlier installer attempt. Velopack replaced it, so it can be closed.

## Update the website

The website is plain HTML and CSS in `docs/`. Once a pull request that changes `docs/` is merged into `main`, the change goes live within a minute or two through GitHub Pages. `CONTRIBUTING.md` has a table of which file controls which image or section.

Open `docs/index.html` in a browser to check changes before pushing.

## Brand rules

Fahim set these and was firm about them.

- **Logo:** only Fahim's page-with-three-diagonal-lines document icon. Never design a new one. The files are `docs/media/app-icon.png` for the site and `packaging/icon.png`, `icon.ico` and `icon.icns` for the app, all drawn by `packaging/make_icons.py`. Don't swap it for another icon or make a new one.
- **No INSITE DC logo or wordmark** on the app or the site.
- **Colours:** blue and navy, with a beige drawing-paper background on the site. No green anywhere.
- **Fonts:** one sans-serif family, in regular and bold. No serif or monospace on the site.
- **Website headline:** "Batch watermark your PDFs."

## Accounts and access

| What | Details |
| --- | --- |
| GitHub | The repository belongs to the GitHub account **FZ-Labz**. This is a personal account, not an organisation. Fahim's `gh` login for it is called Fahim8371. Pushing from another account (for example FZ-42) fails. |
| GitHub Actions | Uses the built-in `GITHUB_TOKEN`. There are no extra secrets to hand over. |
| GitHub Pages | Turned on in the repository settings: deploy from branch `main`, folder `/docs`. |
| Branch protection | `main` needs a pull request for every change. Direct pushes, force pushes and deleting the branch are blocked. |
| Code signing | None yet. The plan is to apply to SignPath Foundation, which signs open-source projects for free. |
| Microsoft Partner Center | Not set up yet. |

To let someone else maintain the project, either add them as a collaborator on the repository or transfer the repository to them or to an organisation. GitHub keeps a redirect after a transfer, but the app's update check and the website both use the `FZ-Labz/pdf-watermark` address. After a transfer, update `REPO_URL` in `updater.py`, the links in `README.md` and `docs/index.html`, and release a new version.

## Known issues

- **Security warnings on first install.** Builds aren't code-signed. The browser may warn about the download (choose **Keep**), and Windows shows "Windows protected your PC" (click **More info**, then **Run anyway**). Updates after that don't warn. The plan is a free SignPath Foundation application. A bought certificate would cost about $150 to $300 a year, and the Microsoft Store route in `next-steps/microsoft-store.md` is another option. **Don't let the README or website claim the app is signed until it really is.**
- **Slow preview on very large drawings.** Drawings with hundreds of thousands of vector paths, such as some HV services sheets, take around 3 seconds to preview. PyMuPDF holds Python's lock while rendering, so background threads would freeze the window. A fix would mean rendering previews in a separate process.
- **Exports are mostly limited by disk speed.** Running exports in parallel was tried and only gave about 1.5 times the speed, so it wasn't added.
- **Damaged or password-protected PDFs** are flagged and skipped. The user has to save a readable copy first. There's no password entry in the app yet.
- **The CI build is larger than a local build** (about 77 MB compared with 32 MB for 1.1.0). This hasn't been looked into.

## Ideas not done yet

- **Code-signed** builds, through SignPath Foundation.
- List the app on **winget** so people can install it with `winget install`. Now that the Setup.exe exists, this means submitting a manifest to the `microsoft/winget-pkgs` repository.
- Publish to the **Microsoft Store** (checklist in `next-steps/microsoft-store.md`).
- Close pull request #2.
- **Image and logo** watermarks.
- **Password entry** for protected PDFs.
- **macOS app.** The PyInstaller spec already builds a `.app`. The release workflow notes say what to add.
- **Getting it seen.** Fahim has a plan for promoting the app in a separate document called "Getting PDF Watermark seen". Ask Fahim for a copy.

## Getting help

- To uninstall, use Windows **Settings > Apps > Installed apps**. Settings stay in `%APPDATA%\PDF Watermark` until that folder is deleted.
- The app's log is at `%APPDATA%\PDF Watermark\app.log`. Ask users to attach it to any bug report.
- `CONTRIBUTING.md` has the full list of command-line options and a description of every module.
