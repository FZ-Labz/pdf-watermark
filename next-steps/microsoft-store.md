# Publishing to the Microsoft Store

A working checklist for getting PDF Watermark into the Microsoft Store as an
MSIX package. Tick items off as they land.

**Owner column:** `you` needs a human (identity verification, payment, a
submission form). `claude` is repo work that can be done in a session.

---

## The decision this is built on

Package as **MSIX**, not as a direct EXE submission.

| Route | Signing | Cost |
| --- | --- | --- |
| **MSIX** (chosen) | Microsoft signs it during certification | free |
| EXE / MSI | You must Authenticode-sign it yourself first | $150-300/yr for an OV certificate |

Microsoft [does not re-sign EXE/MSI submissions](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options).
Their cheap signing service (Azure Artifact Signing, ~$9.99/mo) is restricted to
**US and Canada individuals**, so it is not available to developers elsewhere. MSIX
avoids the certificate question entirely.

**What this does not solve:** the `.exe` on the GitHub release stays unsigned
and will keep triggering SmartScreen. The Store is a second, clean distribution
channel — not a fix for the first one.

---

## Phase 1 - Partner Center account

Start here. Identity verification takes days and everything else waits on it.

| | Task | Owner |
| --- | --- | --- |
| [ ] | Register as an **individual** at [Partner Center](https://developer.microsoft.com/store/publish-apps) | you |
| [ ] | Confirm the fee at signup - historically ~$19 one-time, but [waived for individuals since Sept 2025](https://www.neowin.net/news/microsoft-store-now-lets-individual-developers-join-for-free/) | you |
| [ ] | Complete identity verification (allow several days) | you |

## Phase 2 - Reserve the name

Blocked by Phase 1.

| | Task | Owner |
| --- | --- | --- |
| [ ] | Reserve an app name. "PDF Watermark" is generic and may be taken - have fallbacks ready | you |
| [ ] | Copy the three identity values from **Product identity** (below) into this file | you |

Fill these in once reserved — Phase 3 needs them verbatim:

```
Package/Identity/Name          = ____________________
Package/Identity/Publisher     = CN=________________________________
Publisher display name         = ____________________
```

## Phase 3 - Repo changes

Can run in parallel with Phases 1-2, except the manifest needs the values above.

| | Task | Owner |
| --- | --- | --- |
| [ ] | Switch the Windows PyInstaller build from one-file to one-dir | claude |
| [ ] | Generate the Store logo asset set from `packaging/icon.png` | claude |
| [ ] | Write `packaging/AppxManifest.xml` | claude |
| [ ] | Handle a missing WebView2 runtime gracefully (see Risks) | claude |
| [ ] | Paste the Phase 2 identity values into the manifest | you |
| [ ] | Add an MSIX build job to `.github/workflows/release.yml` | claude |

**One-dir, not one-file.** `packaging/pdf-watermark.spec` currently inlines
`a.binaries, a.datas` into `EXE()` on Windows. One-file unpacks the whole app to
`%TEMP%` on every launch — slow, and a poor fit for MSIX. The macOS branch of the
same spec already does it the right way: `EXE(exclude_binaries=True)` plus
`COLLECT()`.

**Version format.** The Store requires four parts and the last must be `0`.
`VERSION` holds `1.0.0`, so the package version is `1.0.0.0`.

**Logo assets.** MSIX needs a defined set, each at several scale factors
(100/125/150/200/400%). `packaging/make_icons.py` can be extended to emit them.

| Asset | Base size | Used for |
| --- | --- | --- |
| `Square44x44Logo` | 44x44 | app list, taskbar |
| `Square150x150Logo` | 150x150 | medium Start tile |
| `StoreLogo` | 50x50 | Store listing |

## Phase 4 - Build and verify locally

| | Task | Owner |
| --- | --- | --- |
| [ ] | Install the Windows SDK (provides `makeappx.exe` and `signtool.exe`) | you |
| [ ] | Build the one-dir app with PyInstaller | claude |
| [ ] | Pack it into an `.msix` | claude |
| [ ] | Sign with a **self-signed** cert for local testing only | claude |
| [ ] | Install the package and confirm the app actually runs packaged | you |
| [ ] | Check watermarking still writes files correctly from inside the package | you |

Packing:

```
makeappx pack /d dist/PDFWatermark /p PDFWatermark.msix
```

The self-signed certificate is **only** so Windows will let you install it for
testing. Its subject must match the `Publisher` value exactly. Upload to the
Store **unsigned** — Microsoft signs during certification.

## Phase 5 - Submit

Blocked by Phases 1-4.

| | Task | Owner |
| --- | --- | --- |
| [ ] | Upload the `.msix` | you |
| [ ] | Category: Productivity | you |
| [ ] | Age rating via the IARC questionnaire | you |
| [ ] | Privacy policy URL - already written, reuse it | you |
| [ ] | Store screenshots - `docs/screenshots/` already has four | you |
| [ ] | Description and search terms | you |
| [ ] | Submit and wait (certification is typically 24-72 hours) | you |

## Phase 6 - After it is live

| | Task | Owner |
| --- | --- | --- |
| [ ] | Link the Store listing from the README | claude |
| [ ] | Submit to winget (it can source from the Store) | claude |
| [ ] | Note the listing as a third-party signal for the SignPath reapplication | you |

---

## Risks

**WebView2 is a hard dependency.** pywebview uses EdgeChromium on Windows.
Windows 11 ships the runtime; some Windows 10 machines do not. Store
certification runs on clean VMs, so if the app dies with no WebView2 it fails
certification. Either declare the dependency in the manifest or detect it and
show a real error rather than crashing.

**File writes are fine.** MSIX full-trust apps are not UWP-sandboxed, so writing
watermarked PDFs next to the source files still works. Only writes *inside the
install folder* get redirected, and the app does not do that.

**Name availability.** The reserved name is what appears in the Store. If the
obvious one is gone, decide the fallback before reserving rather than during.

---

## Open questions

- [ ] Is the individual onboarding fee currently $0 in your region? Confirm at signup.
- [ ] Which name gets reserved if "PDF Watermark" is unavailable?
- [ ] Ship the macOS build to the Store too, or Windows only for now?
