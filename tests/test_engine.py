"""The drawing engine: geometry, rotation, fonts, placeholders, saving."""

import errno
from itertools import product

import pymupdf
import pytest
from conftest import A3, A4, make_page, red_centroid, red_extent_centre, save

import watermark as wm

ROTATIONS = [0, 90, 180, 270]


def pixels(page, dpi=30):
    return page.get_pixmap(dpi=dpi, alpha=False).samples


@pytest.mark.parametrize("rotation", ROTATIONS)
@pytest.mark.parametrize("crop", [None, (0, 0, 500, 700)])
@pytest.mark.parametrize("origin", [(0, 0), (50, -30)])
def test_normalising_does_not_change_how_the_page_looks(rotation, crop, origin, review_image):
    """De-rotation must render pixel-identically - including the crop box."""
    if crop and origin != (0, 0):
        crop = (crop[0] + origin[0], crop[1] + origin[1], crop[2] + origin[0], crop[3] + origin[1])
    doc = pymupdf.open()
    page = make_page(doc, rotation=rotation, crop=crop, origin=origin)
    before = (page.rect.width, page.rect.height, pixels(page))

    wm._normalise_page(page)
    page = doc.reload_page(page)
    review_image(f"rotation {rotation} - crop {crop} - origin {origin}", page)

    assert page.rotation == 0
    assert (page.rect.width, page.rect.height) == pytest.approx(before[:2])
    assert pixels(page) == before[2]


def test_watermark_is_centred_on_mixed_size_pages(tmp_path, red_style, review_image):
    cases = list(product((A4, A3, (1191, 842)), ROTATIONS))
    with pymupdf.open() as doc:
        for size, rotation in cases:
            make_page(doc, size=size, rotation=rotation)
        src = save(doc, tmp_path / "mixed.pdf")
    out = tmp_path / "watermarked.pdf"
    wm.watermark_file(src, out, red_style)

    with pymupdf.open(out) as copy:
        assert copy.page_count == len(cases)
        for page, (size, rotation) in zip(copy, cases, strict=True):
            label = f"{size[0]}x{size[1]} - rotation {rotation}"
            review_image(label, page)
            cx, cy, count = red_centroid(page)
            assert count > 50, f"{label}: watermark not visible"
            assert (cx, cy) == pytest.approx((0.5, 0.5), abs=0.04), label


def test_watermark_is_centred_on_a_cropped_rotated_page(red_style, review_image):
    doc = pymupdf.open()
    page = make_page(doc, rotation=90, crop=(0, 100, 595, 742))
    page = wm.watermark_page(page, red_style)
    review_image("rotation 90 - symmetric crop", page)
    cx, cy, count = red_centroid(page)
    assert count > 50
    assert (cx, cy) == pytest.approx((0.5, 0.5), abs=0.04)


def test_watermark_is_centred_on_any_cropped_page(tmp_path, red_style, review_image):
    """
    The watermark must be centred in what a viewer shows - the crop box -
    wherever that box sits on the page. Checked on the saved copy, since that
    is what goes out.

    Regression: PyMuPDF's TextWriter offsets text by the crop box's distance
    from the top of the page, but PDF y runs from the bottom, so any crop that
    isn't vertically centred moved the watermark - right off the page for a
    crop on the lower half, while the run still reported success.
    """
    crops = [(10, 10, 585, 400), (10, 450, 585, 832), (200, 300, 560, 800), (50, 80, 500, 760)]
    cases = list(product(crops, ROTATIONS))
    with pymupdf.open() as doc:
        for crop, rotation in cases:
            make_page(doc, rotation=rotation, crop=crop)
        src = save(doc, tmp_path / "in.pdf")
    out = tmp_path / "out.pdf"
    wm.watermark_file(src, out, red_style)

    with pymupdf.open(out) as copy:
        assert copy.page_count == len(cases)
        for page, (crop, rotation) in zip(copy, cases, strict=True):
            label = f"crop {crop} - rotation {rotation}"
            review_image(label, page)
            cx, cy, count = red_centroid(page)
            assert count > 50, f"{label}: watermark not visible"
            assert (cx, cy) == pytest.approx((0.5, 0.5), abs=0.04), label


@pytest.mark.parametrize("rotation", [0, 90])
def test_watermark_is_centred_on_an_offset_page_with_an_off_centre_crop(tmp_path, red_style, rotation, review_image):
    """A MediaBox that doesn't start at (0, 0), as some generators write, plus a crop."""
    ox, oy = 120, 60
    doc = pymupdf.open()
    make_page(doc, rotation=rotation, origin=(ox, oy), crop=(ox + 200, oy + 300, ox + 560, oy + 800))
    src = save(doc, tmp_path / "in.pdf")
    out = tmp_path / "out.pdf"
    wm.watermark_file(src, out, red_style)
    copy = pymupdf.open(out)
    review_image(f"offset MediaBox - rotation {rotation}", copy[0])
    cx, cy, count = red_centroid(copy[0])
    assert count > 50
    assert (cx, cy) == pytest.approx((0.5, 0.5), abs=0.04)
    copy.close()


def test_cropped_away_content_stays_hidden(tmp_path, red_style, review_image):
    """Fixing the crop handling must not reveal what the author cropped away."""
    doc = pymupdf.open()
    page = doc.new_page(width=A4[0], height=A4[1])
    page.insert_text((60, 120), "HIDDEN ABOVE THE CROP", fontsize=20)
    page.insert_text((60, 700), "Visible text", fontsize=20)
    doc.xref_set_key(page.xref, "CropBox", "[0 0 595 400]")   # keep only the lower part
    src = save(doc, tmp_path / "in.pdf")
    out = tmp_path / "out.pdf"
    wm.watermark_file(src, out, red_style)

    copy = pymupdf.open(out)
    review_image("visible content after export", copy[0])
    shown = copy[0].get_text(clip=copy[0].rect)
    assert "Visible text" in shown
    assert "HIDDEN" not in shown
    assert copy[0].rect.height == pytest.approx(400)
    copy.close()


def test_unbalanced_transform_in_content_stream_is_contained(red_style, review_image):
    """CAD-style PDFs leave a bare `cm` open; the watermark must not inherit it."""
    doc = pymupdf.open()
    page = doc.new_page(width=A4[0], height=A4[1])
    xref = page.get_contents()[0] if page.get_contents() else None
    if xref is None:
        page.insert_text((40, 60), "x")
        xref = page.get_contents()[0]
    doc.update_stream(xref, b"0.12 0 0 0.12 0 0 cm\n" + page.read_contents())
    page = wm.watermark_page(doc.reload_page(page), red_style)
    review_image("CAD content transform", page)
    cx, cy, count = red_centroid(page)
    assert count > 50
    assert (cx, cy) == pytest.approx((0.5, 0.5), abs=0.04)


@pytest.mark.parametrize("text", ["CONFIDENTIAL - Иванов", "CONFIDENTIAL - 株式会社トヨタ",
                                  "Für Łukasz Wójcik"])
def test_non_latin_text_is_drawn_and_centred(text, red_style, review_image):
    doc = pymupdf.open()
    page = make_page(doc)
    style = wm.Style(**{**red_style.__dict__, "text": text, "angle": 0})
    page = wm.watermark_page(page, style)
    review_image(text, page)
    cx, cy = red_extent_centre(page)
    assert cx == pytest.approx(0.5, abs=0.02)
    assert cy == pytest.approx(0.5, abs=0.02)
    assert text in page.get_text()


def test_tiling_keeps_long_text_readable():
    doc = pymupdf.open()
    page = make_page(doc)
    long = wm.Style(text="CONFIDENTIAL - Acme Construction Holdings", tile=4)
    short = wm.Style(text="DRAFT", tile=4)
    assert wm.effective_font_size(page, long) >= 18
    assert wm.effective_font_size(page, short) > wm.effective_font_size(page, long)


def test_tiling_covers_the_page(red_style, review_image):
    doc = pymupdf.open()
    page = make_page(doc)
    style = wm.Style(**{**red_style.__dict__, "tile": 4})
    page = wm.watermark_page(page, style)
    review_image("four tiled bands", page)
    # Every quarter of the page should carry some of the mark.
    for qx in (0, 1):
        for qy in (0, 1):
            clip = pymupdf.Rect(qx * page.rect.width / 2, qy * page.rect.height / 2,
                                (qx + 1) * page.rect.width / 2, (qy + 1) * page.rect.height / 2)
            sub = page.get_pixmap(dpi=20, clip=clip, alpha=False)
            pixels = sub.samples
            reds = sum(1 for i in range(0, len(pixels), 3) if pixels[i] > 180 and pixels[i + 1] < 90)
            assert reds > 5, f"quarter {qx},{qy} has no watermark"


def test_placeholders_are_filled_per_page(tmp_path, review_image):
    doc = pymupdf.open()
    for _ in range(3):
        make_page(doc)
    src = save(doc, tmp_path / "Tender pack.pdf")
    out = tmp_path / "out.pdf"
    wm.watermark_file(src, out, wm.Style(text="{file} - page {page} of {pages} - {date}"))
    with pymupdf.open(out) as result:
        for page in result:
            number = page.number + 1
            review_image(f"page {number} of 3", page)
            assert f"Tender pack - page {number} of 3 - " in page.get_text()
    assert wm.expand_text("x {date}", date=__import__("datetime").date(2026, 1, 2)) == "x 2026-01-02"
    assert wm.expand_text("{unknown} {page}", page=4) == "{unknown} 4"


def test_file_keeps_pages_sizes_bookmarks_and_links(tmp_path, review_image):
    doc = pymupdf.open()
    make_page(doc, size=A4)
    make_page(doc, size=A3, rotation=90)
    make_page(doc, size=A4)
    doc.set_toc([[1, "Intro", 1], [2, "Drawings", 2], [1, "End", 3]])
    doc[0].insert_link({"kind": pymupdf.LINK_URI, "from": pymupdf.Rect(40, 40, 200, 70),
                        "uri": "https://example.com"})
    # Flat, because pytest.approx doesn't compare nested sequences.
    sizes = [x for p in doc for x in (p.rect.width, p.rect.height)]
    src = save(doc, tmp_path / "in.pdf")

    pages = wm.watermark_file(src, tmp_path / "out.pdf", wm.Style(text="X"))

    out = pymupdf.open(tmp_path / "out.pdf")
    assert pages == 3 == out.page_count
    assert [x for p in out for x in (p.rect.width, p.rect.height)] == pytest.approx(sizes)
    assert out.get_toc() == [[1, "Intro", 1], [2, "Drawings", 2], [1, "End", 3]]
    assert out[0].get_links()[0]["uri"] == "https://example.com"
    assert not [p for p in tmp_path.iterdir() if p.suffix == ".tmp"]
    for page in out:
        review_image(f"preserved page {page.number + 1}", page)


def test_editing_restrictions_are_kept(tmp_path):
    doc = pymupdf.open()
    make_page(doc)
    perms = pymupdf.PDF_PERM_PRINT | pymupdf.PDF_PERM_ACCESSIBILITY
    src = save(doc, tmp_path / "locked.pdf", encryption=pymupdf.PDF_ENCRYPT_AES_256,
               owner_pw="secret-owner", user_pw="", permissions=perms)

    wm.watermark_file(src, tmp_path / "out.pdf", wm.Style(text="X"))

    out = pymupdf.open(tmp_path / "out.pdf")
    assert not out.needs_pass
    assert out.metadata["encryption"]
    assert not out.permissions & pymupdf.PDF_PERM_MODIFY
    assert not out.authenticate("secret-owner") & 4  # original owner password no longer applies


def test_password_protected_pdf_gives_a_clear_error(tmp_path):
    doc = pymupdf.open()
    make_page(doc)
    src = save(doc, tmp_path / "secret.pdf", encryption=pymupdf.PDF_ENCRYPT_AES_256,
               owner_pw="o", user_pw="u")
    with pytest.raises(wm.WatermarkError, match="password-protected"):
        wm.watermark_file(src, tmp_path / "out.pdf")
    wm.watermark_file(src, tmp_path / "out.pdf", password="u")
    assert (tmp_path / "out.pdf").exists()


def test_damaged_pdf_gives_a_clear_error(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"%PDF-1.7\nthis is not really a pdf")
    with pytest.raises(wm.WatermarkError, match="damaged|no pages"):
        wm.watermark_file(bad, tmp_path / "out.pdf")
    assert not (tmp_path / "out.pdf").exists()


def test_failed_export_keeps_existing_copy_and_cleans_up(tmp_path, monkeypatch):
    with pymupdf.open() as doc:
        make_page(doc)
        src = save(doc, tmp_path / "source.pdf")
        target = save(doc, tmp_path / "issued.pdf")
    original_file = target.read_bytes()

    def reject_replace(source, destination):
        assert target.read_bytes() == original_file
        with pymupdf.open(source) as pending:
            assert "DRAFT" in pending[0].get_text()
        raise PermissionError(errno.EACCES, "destination is locked", destination)

    with monkeypatch.context() as patch:
        patch.setattr(wm.os, "replace", reject_replace)
        with pytest.raises(wm.WatermarkError, match="could not save"):
            wm.watermark_file(src, target, wm.Style(text="DRAFT"))

    assert target.read_bytes() == original_file
    assert set(tmp_path.iterdir()) == {src, target}


def test_flatten_keeps_the_visible_watermark_but_removes_selectable_text(tmp_path, review_image):
    doc = pymupdf.open()
    make_page(doc)
    make_page(doc, size=A3)
    doc.set_toc([[1, "First", 1], [1, "Second", 2]])
    src = save(doc, tmp_path / "in.pdf")
    style = wm.Style(text="SECRET", color=(1, 0, 0), opacity=1)
    wm.watermark_file(src, tmp_path / "flat.pdf", style, flatten_dpi=72)
    with pymupdf.open(tmp_path / "flat.pdf") as out:
        assert out.page_count == 2
        assert out.get_toc() == [[1, "First", 1], [1, "Second", 2]]
        for page, size in zip(out, (A4, A3), strict=True):
            label = f"page {page.number + 1} - {size[0]}x{size[1]}"
            review_image(label, page)
            assert (page.rect.width, page.rect.height) == pytest.approx(size), label
            assert page.get_text().strip() == "", label
            cx, cy, count = red_centroid(page)
            assert count > 50, f"{label}: watermark missing after flattening"
            assert (cx, cy) == pytest.approx((0.5, 0.5), abs=0.04), label


def test_preview_returns_png(tmp_path, review_image):
    doc = pymupdf.open()
    make_page(doc, rotation=90)
    src = save(doc, tmp_path / "in.pdf")
    png = wm.render_preview(src, wm.Style(text="X"), max_px=300)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    review_image("PNG preview", pymupdf.Pixmap(png))
    # Previewing must never touch the source.
    assert pymupdf.open(src)[0].rotation == 90


def _full_render(src, style, max_px):
    """The preview as it used to be made: watermark the real page, then render it."""
    doc = pymupdf.open(src)
    text = wm.expand_text(style.text, 1, doc.page_count, src.stem)
    page = wm.watermark_page(doc[0], style, text, wm.style_font(style, text))
    zoom = max_px / max(page.rect.width, page.rect.height)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    doc.close()
    return pix


def _mark_stats(pix):
    """Pixel count, centroid and bounding box of the red watermark in a render."""
    n, data, xs, ys = pix.n, pix.samples, [], []
    for y in range(pix.height):
        row = y * pix.stride
        for x in range(pix.width):
            r, g = data[row + x * n], data[row + x * n + 1]
            if r - g > 60:      # red ink, faded or not; the page's own content is blue and black
                xs.append(x)
                ys.append(y)
    if not xs:
        return 0, None, None
    return len(xs), (sum(xs) / len(xs), sum(ys) / len(ys)), (min(xs), min(ys), max(xs), max(ys))


@pytest.mark.parametrize("case", ["plain", "rot90", "rot180", "rot270", "cropped", "offset", "stamp", "tile"])
def test_cached_preview_matches_a_full_render(tmp_path, case, review_image):
    """
    The preview draws the watermark over a cached image of the page instead of
    over the page itself. It must look the same as watermarking the real page,
    including on the rotated and cropped pages that the page normalisation
    exists for.
    """
    doc = pymupdf.open()
    make_page(doc, rotation={"rot90": 90, "rot180": 180, "rot270": 270}.get(case, 0),
              crop=(50, 80, 500, 760) if case == "cropped" else None,
              origin=(120, 60) if case == "offset" else (0, 0))
    src = save(doc, tmp_path / f"{case}.pdf")
    layout = {"stamp": "position", "tile": "tile"}.get(case, "diagonal")
    style = wm.Style(text="CONFIDENTIAL - Acme", layout=layout, color=(0.85, 0.2, 0.2), opacity=0.6)

    expected = _full_render(src, style, 400)
    image = wm.render_preview(src, style, max_px=400)
    actual = pymupdf.Pixmap(image)
    review_image(f"{case} - preview", actual)
    review_image(f"{case} - full render", expected)

    assert (actual.width, actual.height) == (expected.width, expected.height)
    # Usually pixel-identical. Where the crop box starts mid-pixel, the edges
    # of the letters can shade differently by a fraction of a pixel - so what
    # is compared is where the watermark is and how big, not every pixel.
    count, centre, box = _mark_stats(actual)
    want_count, want_centre, want_box = _mark_stats(expected)
    assert want_count > 0
    assert abs(count - want_count) <= 0.03 * want_count, f"{case}: {count} vs {want_count} marked pixels"
    assert abs(centre[0] - want_centre[0]) <= 1 and abs(centre[1] - want_centre[1]) <= 1, f"{case}: centre moved"
    assert all(abs(a - b) <= 1 for a, b in zip(box, want_box, strict=True)), f"{case}: extent {box} vs {want_box}"


def test_preview_cache_notices_an_edited_file(tmp_path, review_image):
    doc = pymupdf.open()
    make_page(doc, label="First version")
    src = save(doc, tmp_path / "in.pdf")
    first = pymupdf.Pixmap(wm.render_preview(src, wm.Style(text="X"), max_px=300))

    doc = pymupdf.open()
    make_page(doc, size=(A4[1], A4[0]), label="Second version")   # now landscape
    save(doc, src)
    second = pymupdf.Pixmap(wm.render_preview(src, wm.Style(text="X"), max_px=300))
    review_image("before edit - portrait", first)
    review_image("after edit - landscape", second)
    assert first.height != second.height, "served the stale page"


def test_preview_can_be_jpeg(tmp_path, review_image):
    doc = pymupdf.open()
    make_page(doc)
    src = save(doc, tmp_path / "in.pdf")
    preview = wm.render_preview(src, wm.Style(text="X"), max_px=200, fmt="jpeg")
    assert preview[:3] == b"\xff\xd8\xff"
    review_image("JPEG preview decoded to PNG for review", pymupdf.Pixmap(preview))


@pytest.mark.parametrize("value,expected", [
    ("red", (0xd9 / 255, 0x33 / 255, 0x33 / 255)),
    ("#000", (0, 0, 0)),
    ("FFFFFF", (1, 1, 1)),
])
def test_parse_color(value, expected):
    assert wm.parse_color(value) == pytest.approx(expected)


def test_parse_color_rejects_nonsense():
    with pytest.raises(ValueError, match="not a colour"):
        wm.parse_color("blurple")


def test_default_angle_follows_the_page_diagonal():
    doc = pymupdf.open()
    make_page(doc, size=A4)
    make_page(doc, size=(842, 595))
    portrait, landscape = doc[0], doc[1]
    style = wm.Style()
    assert wm.page_angle(portrait, style) == pytest.approx(54.75, abs=0.1)
    assert wm.page_angle(landscape, style) == pytest.approx(35.25, abs=0.1)
    assert wm.page_angle(portrait, wm.Style(angle=30)) == 30


def test_stacked_layout_splits_at_the_first_dash():
    style = wm.Style(layout="stacked")
    assert (style.layout, style.stack) == ("diagonal", True)
    assert wm.text_lines(style, "CONFIDENTIAL - Acme - Ltd") == ["CONFIDENTIAL", "Acme - Ltd"]
    assert wm.text_lines(style, "DRAFT") == ["DRAFT"]
    assert wm.text_lines(wm.Style(), "CONFIDENTIAL - Acme") == ["CONFIDENTIAL - Acme"]
    assert wm.text_lines(wm.Style(), "one\ntwo") == ["one", "two"]
    # Stamps can stack too, now that they can sit in a corner.
    assert wm.text_lines(wm.Style(layout="footer", stack=True), "A - B") == ["A", "B"]


def test_stacked_layout_draws_two_centred_lines(red_style, review_image):
    doc = pymupdf.open()
    page = make_page(doc)
    # At 0 degrees: rotated, a long line over a short one has a lopsided
    # bounding box even when the block itself is centred.
    style = wm.Style(**{**red_style.__dict__, "layout": "stacked", "angle": 0,
                        "text": "CONFIDENTIAL - Acme"})
    page = wm.watermark_page(page, style)
    review_image("stacked text", page)
    assert "CONFIDENTIAL" in page.get_text() and "Acme" in page.get_text()
    cx, cy = red_extent_centre(page)
    assert (cx, cy) == pytest.approx((0.5, 0.5), abs=0.03)


@pytest.mark.parametrize("layout,lo,hi", [("header", 0.0, 0.1), ("footer", 0.9, 1.0)])
@pytest.mark.parametrize("rotation", [0, 90])
def test_header_and_footer_sit_on_the_edge(layout, lo, hi, rotation, red_style, review_image):
    doc = pymupdf.open()
    page = make_page(doc, rotation=rotation)
    style = wm.Style(**{**red_style.__dict__, "layout": layout, "text": "Prepared for Acme - page {page}"})
    page = wm.watermark_page(page, style, wm.expand_text(style.text, page=3))
    review_image(f"{layout} - rotation {rotation}", page)
    cx, cy = red_extent_centre(page)
    assert lo < cy < hi
    assert cx == pytest.approx(0.5, abs=0.02)
    assert 8 < wm.effective_font_size(page, style) < 16
    assert "page 3" in page.get_text()


def test_size_scales_the_text():
    doc = pymupdf.open()
    page = make_page(doc)
    full = wm.effective_font_size(page, wm.Style(text="DRAFT"))
    half = wm.effective_font_size(page, wm.Style(text="DRAFT", size=0.5))
    assert half == pytest.approx(full / 2)


def test_outline_draws_hollow_letters(review_image):
    doc = pymupdf.open()
    page = wm.watermark_page(make_page(doc), wm.Style(text="DRAFT", outline=True))
    review_image("hollow letters", page)
    assert b"1 Tr" in page.read_contents()


@pytest.mark.parametrize("name", list(wm.POSITIONS))
@pytest.mark.parametrize("rotation", [0, 90])
def test_every_grid_position_lands_in_its_spot(name, rotation, red_style, review_image):
    doc = pymupdf.open()
    page = make_page(doc, rotation=rotation)
    style = wm.Style(**{**red_style.__dict__, "layout": "position", "position": wm.POSITIONS[name],
                        "text": "CONFIDENTIAL - Acme", "size": 1.5})
    page = wm.watermark_page(page, style)
    review_image(f"{name} - rotation {rotation}", page)
    cx, cy = red_extent_centre(page)
    want_x, want_y = wm.POSITIONS[name]
    # The stamp's centre moves from near one edge, through the middle, to the other.
    assert abs(cx - (0.15 + 0.7 * want_x)) < 0.2, f"{name}: x {cx:.2f}"
    assert abs(cy - (0.05 + 0.9 * want_y)) < 0.06, f"{name}: y {cy:.2f}"


def test_position_box_is_reported_for_dragging(tmp_path, review_image):
    doc = pymupdf.open()
    make_page(doc)
    src = save(doc, tmp_path / "in.pdf")
    png, box = wm.render_preview(src, wm.Style(text="X", layout="position", position=(1, 0)),
                                 max_px=200, with_box=True)
    assert png[:4] == b"\x89PNG"
    review_image("top right - drag box", pymupdf.Pixmap(png))
    assert box["x1"] == pytest.approx(1 - box["mx"], abs=0.01)
    assert box["y0"] == pytest.approx(box["my"], abs=0.01)
    _, none = wm.render_preview(src, wm.Style(text="X"), max_px=200, with_box=True)
    assert none is None


def test_legacy_font_codes_still_work():
    style = wm.Style(font="tibo")
    assert (style.font, style.bold, style.italic) == ("Times", True, False)


def test_builtin_bold_and_italic_change_the_font():
    regular = wm.style_font(wm.Style(font="Helvetica", bold=False, italic=False))
    bold = wm.style_font(wm.Style(font="Helvetica", bold=True))
    italic = wm.style_font(wm.Style(font="Helvetica", bold=False, italic=True))
    assert len({regular.name, bold.name, italic.name}) == 3


@pytest.mark.skipif(not __import__("fonts").find_face("Arial", False, False),
                    reason="Arial is not installed here")
def test_installed_font_is_embedded_as_a_small_subset(tmp_path, review_image):
    doc = pymupdf.open()
    for _ in range(5):
        make_page(doc)
    src = save(doc, tmp_path / "in.pdf")
    wm.watermark_file(src, tmp_path / "out.pdf", wm.Style(text="CONFIDENTIAL - page {page}", font="Arial"))
    out = pymupdf.open(tmp_path / "out.pdf")
    assert "CONFIDENTIAL - page 3" in out[2].get_text()
    assert any("Arial" in f[3] for f in out.get_page_fonts(0))
    assert (tmp_path / "out.pdf").stat().st_size < 150_000   # the whole Arial file is ~1 MB
    review_image("embedded Arial - page 3", out[2])


def test_unknown_font_falls_back_instead_of_failing(tmp_path, review_image):
    doc = pymupdf.open()
    make_page(doc)
    src = save(doc, tmp_path / "in.pdf")
    wm.watermark_file(src, tmp_path / "out.pdf", wm.Style(text="DRAFT", font="No Such Font 123"))
    with pymupdf.open(tmp_path / "out.pdf") as out:
        review_image("fallback font", out[0])
        assert "DRAFT" in out[0].get_text()
