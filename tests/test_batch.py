"""The batch layer: finding PDFs, naming outputs, and the command line itself."""

import os
import subprocess
import sys
from pathlib import Path

import pymupdf
import pytest
from conftest import ROOT, make_page, save

import batch_watermark as bw


def pdf(path: Path, pages=1) -> Path:
    with pymupdf.open() as doc:
        for number in range(1, pages + 1):
            make_page(doc, label=f"{path.stem} source page {number}")
        return save(doc, path)


@pytest.fixture
def pack(tmp_path):
    root = tmp_path / "Tender pack"
    pdf(root / "Cover.pdf")
    pdf(root / "UPPER.PDF")
    pdf(root / "drawings" / "Plan.pdf", pages=3)
    (root / "notes.docx").write_text("not a pdf")
    (root / "._Cover.pdf").write_bytes(b"\x00\x05\x16\x07 AppleDouble")
    (root / ".DS_Store").write_bytes(b"\x00")
    pdf(root / "old _X_Watermarked" / "Cover_watermarked.pdf")
    return root


def test_find_pdfs_is_case_insensitive_and_skips_junk(pack):
    found = [p.relative_to(pack).as_posix() for p in bw.find_pdfs(pack, bw.FOLDER_SUFFIX)]
    assert sorted(found) == ["Cover.pdf", "UPPER.PDF", "drawings/Plan.pdf"]
    assert bw.count_ignored(pack, bw.FOLDER_SUFFIX) == 1


def test_find_pdfs_works_inside_a_folder_that_looks_like_output(tmp_path):
    """Only folders *below* the chosen one are treated as previous output."""
    inner = tmp_path / "Archive_Watermarked" / "Pack"
    pdf(inner / "a.pdf")
    assert len(bw.find_pdfs(inner, bw.FOLDER_SUFFIX)) == 1


def test_same_named_sources_never_share_an_output(tmp_path):
    a, b = tmp_path / "A" / "Docs", tmp_path / "B" / "Docs"
    fa, fb = pdf(tmp_path / "A" / "report.pdf"), pdf(tmp_path / "B" / "report.pdf")
    pdf(a / "x.pdf")
    pdf(b / "x.pdf")
    out = tmp_path / "out"
    folder_pdfs = {f: bw.find_pdfs(f, bw.FOLDER_SUFFIX) for f in (a, b)}
    jobs = bw.build_jobs("DRAFT", folder_pdfs, [fa, fb], out, bw.FOLDER_SUFFIX, False)
    destinations = [str(j[1]).casefold() for j in jobs]
    assert len(destinations) == len(set(destinations)) == 4


@pytest.mark.parametrize("text,expected", [
    ("CONFIDENTIAL - Acme", "CONFIDENTIAL - Acme"),
    ('a/b:c*d?"e"', "a-b-c-d--e"),
    ("Page {page} of {pages}", "Page of"),
    ("...", "Watermarked"),
])
def test_slugify(text, expected):
    assert bw.slugify(text) == expected


def test_slugify_caps_length():
    assert len(bw.slugify("x" * 500)) <= 80


@pytest.mark.skipif(sys.platform != "win32", reason="Windows path rules")
def test_long_path_handles_network_shares():
    assert bw.long_path(r"\\server\share\pack\a.pdf") == r"\\?\UNC\server\share\pack\a.pdf"
    assert bw.long_path(r"C:\x\a.pdf") == r"\\?\C:\x\a.pdf"


def run_cli(*args, cwd):
    # A pipe on Windows uses the legacy code page - exactly the setting that
    # used to crash on names like "Łukasz".
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    return subprocess.run([sys.executable, str(ROOT / "batch_watermark.py"), *args],
                          cwd=cwd, capture_output=True, env=env, timeout=120)


def test_cli_end_to_end_with_several_recipients(pack, tmp_path, review_image):
    recipients = ("Łukasz Wójcik", "株式会社")
    sources = (Path("Cover.pdf"), Path("UPPER.PDF"), Path("drawings/Plan.pdf"))
    original_bytes = {source: (pack / source).read_bytes() for source in sources}
    output = tmp_path / "issued"
    result = run_cli(str(pack), "--company", *recipients, "--out", str(output), cwd=tmp_path)
    assert result.returncode == 0, result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace")
    expected = {
        output / f"Tender pack _CONFIDENTIAL - {recipient}_Watermarked" / source.parent
        / f"{source.stem}_watermarked.pdf": (source, recipient)
        for source in sources
        for recipient in recipients
    }
    assert {p for p in output.rglob("*") if p.is_file()} == expected.keys()
    for path, (source, recipient) in expected.items():
        with pymupdf.open(pack / source) as original, pymupdf.open(path) as copy:
            assert copy.page_count == original.page_count, path
            for page in copy:
                text = page.get_text()
                context = f"{path.relative_to(output)}, page {page.number + 1}"
                review_image(f"{recipient} - {source.stem} - page {page.number + 1}", page)
                assert f"{source.stem} source page {page.number + 1}" in text, context
                assert f"CONFIDENTIAL - {recipient}" in text, context
                assert all(other not in text for other in recipients if other != recipient), context
    assert {source: (pack / source).read_bytes() for source in sources} == original_bytes


def test_cli_dry_run_writes_nothing(pack, tmp_path):
    before = {p: p.read_bytes() for p in pack.rglob("*") if p.is_file()}
    paths_before = set(tmp_path.rglob("*"))
    result = run_cli(str(pack), "--text", "DRAFT", "--dry-run", cwd=tmp_path)
    assert result.returncode == 0
    assert b"Dry run complete" in result.stdout
    assert set(tmp_path.rglob("*")) == paths_before
    assert {p: p.read_bytes() for p in before} == before


def test_cli_reports_bad_files_and_carries_on(pack, tmp_path):
    (pack / "broken.pdf").write_bytes(b"%PDF-1.4 broken")
    result = run_cli(str(pack), "--text", "DRAFT", cwd=tmp_path)
    out = result.stdout.decode(errors="replace")
    assert result.returncode == 1
    assert "ERR broken.pdf" in out
    assert "3 succeeded, 1 failed" in out


def test_cli_rejects_bad_colour(pack, tmp_path):
    result = run_cli(str(pack), "--text", "X", "--color", "blurple", cwd=tmp_path)
    assert result.returncode == 2
    assert b"not a colour" in result.stderr


def test_cli_custom_prefix(pack, tmp_path):
    result = run_cli(str(pack), "--company", "Acme", "--prefix", "FOR REVIEW", "--dry-run", cwd=tmp_path)
    assert result.returncode == 0
    assert b'["FOR REVIEW - Acme"]' in result.stdout
    result = run_cli(str(pack), "--company", "Acme", "--prefix", "", "--dry-run", cwd=tmp_path)
    assert b'["Acme"]' in result.stdout


def test_cli_position_and_font_flags(pack, tmp_path):
    result = run_cli(str(pack), "--text", "X", "--position", "top-right", "--no-bold", "--italic", "--dry-run", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    result = run_cli(str(pack), "--text", "X", "--position", "0.2,1.5", cwd=tmp_path)
    assert result.returncode == 2 and b"between 0 and 1" in result.stderr
    result = run_cli(str(pack), "--text", "X", "--font", "Definitely Not A Font", cwd=tmp_path)
    assert result.returncode == 2 and b"no font called" in result.stderr


def test_companies_whose_names_slug_alike_never_share_an_output(tmp_path, review_image):
    """'A/B' and 'A:B' both slug to 'A-B'; one must not overwrite the other."""
    docs = tmp_path / "Docs"
    pdf(docs / "x.pdf")
    single = pdf(tmp_path / "report.pdf")
    output = tmp_path / "issued"
    result = run_cli(str(docs), str(single), "--company", "A/B", "A:B", "--out", str(output), cwd=tmp_path)
    assert result.returncode == 0, result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace")
    contents = {"x": [], "report": []}
    for number, path in enumerate(sorted(output.rglob("*.pdf")), start=1):
        with pymupdf.open(path) as copy:
            assert copy.page_count == 1, path
            text = copy[0].get_text()
            matching_sources = [name for name in contents if f"{name} source page 1" in text]
            matching_recipients = [name for name in ("A/B", "A:B") if f"CONFIDENTIAL - {name}" in text]
            assert len(matching_sources) == len(matching_recipients) == 1, (path, text)
            source, = matching_sources
            recipient, = matching_recipients
            review_image(f"{number} - {source} - {recipient}", copy[0])
        contents[source].append(recipient)
    assert {source: sorted(names) for source, names in contents.items()} == {
        "x": ["A/B", "A:B"], "report": ["A/B", "A:B"],
    }
