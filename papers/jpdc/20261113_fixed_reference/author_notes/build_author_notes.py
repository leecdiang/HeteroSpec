#!/usr/bin/env python3
"""Build the Chinese author-review notes as an embedded-font PDF.

Dependencies: reportlab, fontTools (with cu2qu), and Noto Sans CJK SC.
Usage: python author_notes/build_author_notes.py
Optional: --source FILE --output FILE --font-regular FILE --font-bold FILE.
The input Markdown is never modified. Figures and manuscript sources are not read.
"""
from __future__ import annotations

import argparse
import hashlib
import html
from pathlib import Path
import re
import subprocess
import tempfile

from fontTools import subset
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont as FontToolsFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import textsplit as rl_textsplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph,
    Spacer, Table, TableStyle,
)
from reportlab.platypus import paragraph as rl_paragraph

# ReportLab's default hanging-punctuation list is oriented toward Japanese.
# Include the Chinese full-width punctuation used in the unchanged source.
for _module in (rl_textsplit, rl_paragraph):
    _module.ALL_CANNOT_START += "，；：？！\u201d\u2019"


INK = colors.HexColor("#173047")
TEXT = colors.HexColor("#243746")
MUTED = colors.HexColor("#637581")
TEAL = colors.HexColor("#126A73")
RULE = colors.HexColor("#C9D7DC")
PALE = colors.HexColor("#EDF3F4")
FONT = "AuthorNotesSC"
BOLD = "AuthorNotesSCBold"
PAGE_W, PAGE_H = A4
LEFT = RIGHT = 43
TOP = 49
BOTTOM = 45
WIDTH = PAGE_W - LEFT - RIGHT


def find_font(explicit: str | None, bold: bool) -> Path:
    if explicit:
        path = Path(explicit)
    else:
        pattern = "Noto Sans CJK SC:style=" + ("Bold" if bold else "Regular")
        path = Path(subprocess.check_output(
            ["fc-match", "-f", "%{file}", pattern], text=True
        ).strip())
    if not path.is_file():
        raise FileNotFoundError("Noto Sans CJK SC was not found; supply the font path.")
    return path


def embedded_subset(source: Path, output: Path, text: str, bold: bool) -> None:
    # Noto's TTC is CFF-based. Convert the used outlines to quadratic TrueType
    # outlines so ReportLab can embed them; no glyph image rasterization occurs.
    font = FontToolsFont(source, fontNumber=2 if source.suffix.lower() == ".ttc" else 0)
    options = subset.Options()
    options.desubroutinize = True
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6, 13, 14]
    worker = subset.Subsetter(options=options)
    worker.populate(text=text)
    worker.subset(font)
    if "glyf" in font:
        font.save(output)
        return
    glyph_order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()
    glyphs = {}
    for name in glyph_order:
        target = TTGlyphPen(None)
        converter = Cu2QuPen(target, max_err=1.0, reverse_direction=True)
        glyph_set[name].draw(converter)
        glyphs[name] = target.glyph()
    builder = FontBuilder(font["head"].unitsPerEm, isTTF=True)
    builder.setupGlyphOrder(glyph_order)
    builder.setupCharacterMap(font.getBestCmap())
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({g: font["hmtx"][g] for g in glyph_order})
    builder.setupHorizontalHeader(
        ascent=font["hhea"].ascent,
        descent=font["hhea"].descent,
        lineGap=font["hhea"].lineGap,
    )
    os2 = font["OS/2"]
    builder.setupOS2(
        sTypoAscender=os2.sTypoAscender,
        sTypoDescender=os2.sTypoDescender,
        sTypoLineGap=os2.sTypoLineGap,
        usWinAscent=os2.usWinAscent,
        usWinDescent=os2.usWinDescent,
        usWeightClass=700 if bold else 400,
        fsType=0,
    )
    style = "Bold" if bold else "Regular"
    builder.setupNameTable({
        "familyName": "Author Notes Noto Sans CJK SC",
        "styleName": style,
        "uniqueFontIdentifier": "AuthorNotesNotoSC-" + style,
        "fullName": "Author Notes Noto Sans CJK SC " + style,
        "psName": "AuthorNotesNotoSC-" + style,
        "version": "Version 1.0",
        "licenseDescription": "Based on Noto Sans CJK; SIL Open Font License 1.1.",
        "licenseInfoURL": "https://openfontlicense.org/open-font-license-official-text/",
    })
    builder.setupPost()
    builder.setupMaxp()
    builder.font.save(output)


def styles() -> dict[str, ParagraphStyle]:
    base = dict(fontName=FONT, fontSize=10.2, leading=15.3,
                textColor=TEXT, wordWrap="CJK", alignment=TA_LEFT,
                allowWidows=0, allowOrphans=0, splitLongWords=1)
    result = {"body": ParagraphStyle("body", spaceAfter=6.0, **base)}
    result["summary"] = ParagraphStyle(
        "summary", parent=result["body"], fontSize=11.2, leading=18.0,
        spaceAfter=10.0,
    )
    result["title"] = ParagraphStyle(
        "title", fontName=BOLD, fontSize=21, leading=29,
        textColor=INK, spaceAfter=12, wordWrap="CJK", keepWithNext=True,
    )
    result["h2"] = ParagraphStyle(
        "h2", fontName=BOLD, fontSize=13.3, leading=20,
        textColor=TEAL, spaceBefore=13, spaceAfter=8, wordWrap="CJK",
        keepWithNext=True,
    )
    result["h3"] = ParagraphStyle(
        "h3", fontName=BOLD, fontSize=11, leading=17,
        textColor=INK, spaceBefore=9, spaceAfter=6, wordWrap="CJK",
        keepWithNext=True,
    )
    result["table"] = ParagraphStyle(
        "table", fontName=FONT, fontSize=9.15, leading=13.0,
        textColor=TEXT, wordWrap="CJK", splitLongWords=1,
    )
    result["table_header"] = ParagraphStyle(
        "table_header", parent=result["table"], fontName=BOLD,
        textColor=INK, leading=13.7,
    )
    result["source"] = ParagraphStyle(
        "source", parent=result["body"], fontSize=9.5, leading=14.0,
        leftIndent=9, firstLineIndent=-9, spaceAfter=4.5,
    )
    return result


SOURCE_KEYS = {"RANGE", "CODE", "STRONG", "ROWS", "Q8F", "GUARD",
               "NATURAL", "WIDTH", "MODERN", "BACKEND", "GUIDE", "LATEX", "AI"}


def inline(raw: str, source_entry: bool = False) -> str:
    # Protect link, code, and bold spans before escaping the remaining text.
    saved: list[str] = []

    def protect(value: str) -> str:
        saved.append(value)
        return "ZZTOKEN" + str(len(saved) - 1) + "ZZ"

    raw = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
        lambda m: protect('<link href="' + html.escape(m.group(2), quote=True)
                          + '" color="#126A73">' + html.escape(m.group(1)) + '</link>'),
        raw,
    )
    raw = re.sub(
        r"`([^`]+)`",
        lambda m: protect('<font color="#405766">' + html.escape(m.group(1)) + '</font>'),
        raw,
    )
    raw = re.sub(
        r"\*\*([^*]+)\*\*",
        lambda m: protect('<b>' + html.escape(m.group(1)) + '</b>'),
        raw,
    )
    raw = html.escape(raw)
    if source_entry:
        found = re.match(r"\[([A-Z0-9]+)\]", raw)
        if found:
            key = found.group(1)
            raw = '<a name="source_' + key + '"/>' + raw
    else:
        raw = re.sub(
            r"\[([A-Z0-9]+)\]",
            lambda m: ('<link href="#source_' + m.group(1)
                       + '" color="#126A73">[' + m.group(1) + ']</link>')
            if m.group(1) in SOURCE_KEYS else m.group(0),
            raw,
        )
    for i, value in enumerate(saved):
        raw = raw.replace("ZZTOKEN" + str(i) + "ZZ", value)
    return raw


class NotesDoc(BaseDocTemplate):
    def __init__(self, output: Path):
        super().__init__(
            str(output), pagesize=A4,
            leftMargin=LEFT, rightMargin=RIGHT,
            topMargin=TOP, bottomMargin=BOTTOM,
            title="JPDC 投稿稿件：作者审阅说明",
            author="作者审阅材料",
            subject="Parallelizing Quantized LLM Inference Under a Fixed Numerical Reference",
            pageCompression=1,
        )
        frame = Frame(LEFT, BOTTOM, WIDTH, PAGE_H - TOP - BOTTOM,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate("notes", [frame], onPage=self.decoration))
        self.heading_count = 0

    @staticmethod
    def decoration(canvas, doc):
        canvas.saveState()
        canvas.setTitle("JPDC 投稿稿件：作者审阅说明")
        canvas.setCreator("Author-review document")
        canvas.setFont(FONT, 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(LEFT, PAGE_H - 27, "JPDC  /  作者审阅")
        canvas.drawRightString(PAGE_W - RIGHT, PAGE_H - 27, "13 NOV 2026")
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.55)
        canvas.line(LEFT, PAGE_H - 34, PAGE_W - RIGHT, PAGE_H - 34)
        canvas.line(LEFT, 31, PAGE_W - RIGHT, 31)
        canvas.setFont(FONT, 8)
        canvas.drawString(LEFT, 18, "作者审阅稿 · 未提交")
        canvas.drawRightString(PAGE_W - RIGHT, 18, f"{doc.page:02d}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in {"title", "h2"}:
            key = "heading_" + str(self.heading_count)
            self.heading_count += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.getPlainText(), key, level=0, closed=False)


def table_flowable(rows: list[list[str]], st: dict) -> Table:
    if "原稿" in rows[0][0]:
        fractions = [0.31, 0.40, 0.29]
    elif "主张" in rows[0][0]:
        fractions = [0.25, 0.39, 0.36]
    else:
        fractions = [0.25, 0.35, 0.40]
    cells = [[Paragraph(inline(cell), st["table_header" if r == 0 else "table"])
              for cell in row] for r, row in enumerate(rows)]
    table = Table(cells, colWidths=[WIDTH * x for x in fractions],
                  repeatRows=1, hAlign="LEFT", splitByRow=1)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, TEAL),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def make_story(markdown: str, st: dict) -> list:
    lines = markdown.splitlines()
    story = []
    i = 0
    in_summary = True
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == "<!--PAGEBREAK-->":
            story.append(PageBreak())
            in_summary = False
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                row = [x.strip() for x in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", cell) for cell in row):
                    rows.append(row)
                i += 1
            story.extend([Spacer(1, 3), table_flowable(rows, st), Spacer(1, 9)])
            continue
        match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if match:
            key = {1: "title", 2: "h2", 3: "h3"}[len(match.group(1))]
            story.append(Paragraph(inline(match.group(2)), st[key]))
            i += 1
            continue
        if line.startswith("- "):
            story.append(Paragraph(inline(line[2:], source_entry=True), st["source"]))
            i += 1
            continue
        paragraph = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "- ", "<!--")):
            paragraph.append(lines[i].strip())
            i += 1
        story.append(Paragraph(inline(" ".join(paragraph)), st["summary" if in_summary else "body"]))
    return story


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    parser.add_argument("--source", type=Path, default=here / "AUTHOR_NOTES.zh.md")
    parser.add_argument("--output", type=Path, default=here / "AUTHOR_NOTES.zh.pdf")
    parser.add_argument("--font-regular")
    parser.add_argument("--font-bold")
    args = parser.parse_args()
    source_bytes = args.source.read_bytes()
    markdown = source_bytes.decode("utf-8")
    font_text = markdown + "JPDC  /  作者审阅13 NOV 2026作者审阅稿 · 未提交0123456789"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="author_notes_fonts_") as directory:
        for name, is_bold, explicit in [(FONT, False, args.font_regular),
                                        (BOLD, True, args.font_bold)]:
            out = Path(directory) / (name + ".ttf")
            embedded_subset(find_font(explicit, is_bold), out, font_text, is_bold)
            pdfmetrics.registerFont(TTFont(name, str(out)))
        pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=BOLD,
                                      italic=FONT, boldItalic=BOLD)
        NotesDoc(args.output).build(make_story(markdown, styles()))
    assert source_bytes == args.source.read_bytes(), "The source Markdown changed during rendering."
    print("Built", args.output.name)
    print("Source SHA-256:", hashlib.sha256(source_bytes).hexdigest())


if __name__ == "__main__":
    main()
