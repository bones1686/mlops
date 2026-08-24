#!/usr/bin/env python3
"""Render the Assignment 4 Markdown report as a polished PDF."""

from __future__ import annotations

import html
import math
import re
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports" / "assignment4_report.md"
OUTPUT = ROOT / "output" / "pdf" / "assignment4_complete_kubeflow_pipeline.pdf"

PAGE_W, PAGE_H = A4
LEFT = 18 * mm
RIGHT = 18 * mm
TOP = 18 * mm
BOTTOM = 17 * mm
CONTENT_W = PAGE_W - LEFT - RIGHT

NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#2D6CDF")
LIGHT_BLUE = colors.HexColor("#EAF1FC")
PALE = colors.HexColor("#F5F7FA")
MID = colors.HexColor("#D7DEE8")
TEXT = colors.HexColor("#243142")
MUTED = colors.HexColor("#617184")
GREEN = colors.HexColor("#E7F4EA")
GREEN_BORDER = colors.HexColor("#5BA66A")
AMBER = colors.HexColor("#FFF4D6")
AMBER_BORDER = colors.HexColor("#C99524")


def register_fonts() -> tuple[str, str, str]:
    candidates = [
        (
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            Path("/System/Library/Fonts/Supplemental/Courier New.ttf"),
        ),
        (
            Path("/Library/Fonts/Arial.ttf"),
            Path("/Library/Fonts/Arial Bold.ttf"),
            Path("/Library/Fonts/Courier New.ttf"),
        ),
    ]
    for regular, bold, mono in candidates:
        if regular.exists() and bold.exists() and mono.exists():
            pdfmetrics.registerFont(TTFont("ReportSans", str(regular)))
            pdfmetrics.registerFont(TTFont("ReportSans-Bold", str(bold)))
            pdfmetrics.registerFont(TTFont("ReportMono", str(mono)))
            return "ReportSans", "ReportSans-Bold", "ReportMono"
    return "Helvetica", "Helvetica-Bold", "Courier"


FONT, FONT_BOLD, FONT_MONO = register_fonts()


def normalize(value: str) -> str:
    return (
        value.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2011", "-")
        .replace("\u2192", "->")
        .replace("\u2265", ">=")
    )


def inline_markup(value: str) -> str:
    value = html.escape(normalize(value), quote=False)
    value = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{m.group(2)}" color="#2D6CDF"><u>{m.group(1)}</u></a>',
        value,
    )
    value = re.sub(
        r"`([^`]+)`",
        lambda m: f'<font name="{FONT_MONO}" size="8.4">{m.group(1)}</font>',
        value,
    )
    value = re.sub(r"\*\*([^*]+)\*\*", rf'<font name="{FONT_BOLD}">\1</font>', value)
    return value


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontName=FONT_BOLD,
            fontSize=25,
            leading=31,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=8 * mm,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Normal"],
            fontName=FONT,
            fontSize=13,
            leading=19,
            textColor=MUTED,
            spaceAfter=4 * mm,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName=FONT_BOLD,
            fontSize=16,
            leading=20,
            textColor=NAVY,
            spaceBefore=7 * mm,
            spaceAfter=3 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=9.3,
            leading=13.4,
            textColor=TEXT,
            spaceAfter=3.2 * mm,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=9.1,
            leading=13,
            leftIndent=6 * mm,
            firstLineIndent=-3.5 * mm,
            textColor=TEXT,
            spaceAfter=1.4 * mm,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=8.2,
            leading=11.2,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=2 * mm,
            spaceAfter=4.5 * mm,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            parent=base["BodyText"],
            fontName=FONT_BOLD,
            fontSize=8.2,
            leading=10.5,
            textColor=colors.white,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=7.8,
            leading=10.5,
            textColor=TEXT,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName=FONT_MONO,
            fontSize=7.7,
            leading=10.5,
            textColor=TEXT,
            leftIndent=4 * mm,
            rightIndent=4 * mm,
            borderColor=MID,
            borderWidth=0.6,
            borderPadding=3 * mm,
            backColor=PALE,
            spaceBefore=1.5 * mm,
            spaceAfter=4 * mm,
        ),
    }


STYLES = make_styles()


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(MID)
    canvas.setLineWidth(0.5)
    canvas.line(LEFT, 11.5 * mm, PAGE_W - RIGHT, 11.5 * mm)
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(LEFT, 7.2 * mm, "Assignment 4 - Complete Kubeflow MLOps Pipeline")
    canvas.drawRightString(PAGE_W - RIGHT, 7.2 * mm, f"Page {doc.page}")
    canvas.restoreState()


def arrow(drawing: Drawing, x1: float, y1: float, x2: float, y2: float) -> None:
    drawing.add(Line(x1, y1, x2, y2, strokeColor=BLUE, strokeWidth=1.7))
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 6
    left = (
        x2 - size * math.cos(angle) + size * 0.6 * math.sin(angle),
        y2 - size * math.sin(angle) - size * 0.6 * math.cos(angle),
    )
    right = (
        x2 - size * math.cos(angle) - size * 0.6 * math.sin(angle),
        y2 - size * math.sin(angle) + size * 0.6 * math.cos(angle),
    )
    drawing.add(
        Polygon(
            [x2, y2, left[0], left[1], right[0], right[1]],
            fillColor=BLUE,
            strokeColor=BLUE,
        )
    )


def pipeline_drawing() -> Drawing:
    width = CONTENT_W
    height = 70 * mm
    drawing = Drawing(width, height)
    box_w = 49 * mm
    box_h = 15 * mm
    gap = (width - 3 * box_w) / 2
    xs = [0, box_w + gap, 2 * (box_w + gap)]
    ys = [52 * mm, 27 * mm, 2 * mm]
    labels = [
        ("1. Gather data",),
        ("2. Validate and", "process"),
        ("3. Tune C with", "3-fold CV"),
        ("4. Train and", "evaluate"),
        ("5. Log run and", "artifacts"),
        ("6. Register", "candidate"),
        ("7. Compare with", "champion"),
        ("8. Promote candidate", "or keep champion"),
        ("9. Reload", "serving API"),
    ]
    positions = [
        (xs[0], ys[0]),
        (xs[1], ys[0]),
        (xs[2], ys[0]),
        (xs[2], ys[1]),
        (xs[1], ys[1]),
        (xs[0], ys[1]),
        (xs[0], ys[2]),
        (xs[1], ys[2]),
        (xs[2], ys[2]),
    ]
    for index, ((x, y), lines) in enumerate(zip(positions, labels)):
        if index < 3:
            fill, border = LIGHT_BLUE, BLUE
        elif index < 7:
            fill, border = AMBER, AMBER_BORDER
        else:
            fill, border = GREEN, GREEN_BORDER
        drawing.add(
            Rect(
                x,
                y,
                box_w,
                box_h,
                rx=6,
                ry=6,
                fillColor=fill,
                strokeColor=border,
                strokeWidth=1.2,
            )
        )
        center_x = x + box_w / 2
        center_y = y + box_h / 2
        if len(lines) == 1:
            drawing.add(
                String(
                    center_x,
                    center_y - 3,
                    lines[0],
                    fontName=FONT_BOLD,
                    fontSize=8.4,
                    textAnchor="middle",
                    fillColor=TEXT,
                )
            )
        else:
            for offset, line in zip((3.2, -6.5), lines):
                drawing.add(
                    String(
                        center_x,
                        center_y + offset,
                        line,
                        fontName=FONT_BOLD,
                        fontSize=8.1,
                        textAnchor="middle",
                        fillColor=TEXT,
                    )
                )

    arrow(drawing, xs[0] + box_w, ys[0] + box_h / 2, xs[1] - 4, ys[0] + box_h / 2)
    arrow(drawing, xs[1] + box_w, ys[0] + box_h / 2, xs[2] - 4, ys[0] + box_h / 2)
    arrow(drawing, xs[2] + box_w / 2, ys[0], xs[2] + box_w / 2, ys[1] + box_h + 4)
    arrow(drawing, xs[2], ys[1] + box_h / 2, xs[1] + box_w + 4, ys[1] + box_h / 2)
    arrow(drawing, xs[1], ys[1] + box_h / 2, xs[0] + box_w + 4, ys[1] + box_h / 2)
    arrow(drawing, xs[0] + box_w / 2, ys[1], xs[0] + box_w / 2, ys[2] + box_h + 4)
    arrow(drawing, xs[0] + box_w, ys[2] + box_h / 2, xs[1] - 4, ys[2] + box_h / 2)
    arrow(drawing, xs[1] + box_w, ys[2] + box_h / 2, xs[2] - 4, ys[2] + box_h / 2)
    return drawing


def scaled_image(path: Path) -> Image:
    with PILImage.open(path) as image:
        width, height = image.size
    max_width = CONTENT_W
    max_height = 105 * mm
    scale = min(max_width / width, max_height / height)
    return Image(str(path), width=width * scale, height=height * scale)


def make_table(rows: list[list[str]]) -> Table:
    column_count = len(rows[0])
    if column_count == 3:
        widths = [CONTENT_W * 0.20, CONTENT_W * 0.32, CONTENT_W * 0.48]
    elif column_count == 2:
        widths = [CONTENT_W * 0.34, CONTENT_W * 0.66]
    else:
        widths = [CONTENT_W / column_count] * column_count
    formatted = []
    for row_index, row in enumerate(rows):
        style = STYLES["table_header"] if row_index == 0 else STYLES["table_cell"]
        formatted.append([Paragraph(inline_markup(cell), style) for cell in row])
    table = Table(formatted, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.45, MID),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def is_special(line: str) -> bool:
    stripped = line.strip()
    return (
        not stripped
        or stripped.startswith("## ")
        or stripped.startswith("```")
        or stripped.startswith("![")
        or stripped.startswith("| ")
        or stripped.startswith("- ")
        or bool(re.match(r"\d+\. ", stripped))
    )


def report_story() -> list:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story: list = [
        Spacer(1, 34 * mm),
        Table(
            [[""]],
            colWidths=[26 * mm],
            rowHeights=[2.5 * mm],
            style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), BLUE)]),
        ),
        Spacer(1, 8 * mm),
        Paragraph("Assignment 4", STYLES["cover_subtitle"]),
        Paragraph("Complete Kubeflow<br/>MLOps Pipeline", STYLES["cover_title"]),
        Paragraph(
            "Customer Support Query Classification System",
            STYLES["cover_subtitle"],
        ),
        PageBreak(),
    ]

    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line or line.startswith("# "):
            index += 1
            continue

        if line.startswith("## "):
            story.append(Paragraph(inline_markup(line[3:]), STYLES["h2"]))
            index += 1
            continue

        if line.startswith("```mermaid"):
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                index += 1
            index += 1
            story.extend(
                [
                    KeepTogether(
                        [
                            pipeline_drawing(),
                            Paragraph(
                                "Pipeline flow from data gathering to champion serving.",
                                STYLES["caption"],
                            ),
                        ]
                    )
                ]
            )
            continue

        if line.startswith("```"):
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(normalize(lines[index]))
                index += 1
            index += 1
            story.append(Preformatted("\n".join(code_lines), STYLES["code"]))
            continue

        image_match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line)
        if image_match:
            image_path = (SOURCE.parent / image_match.group(2)).resolve()
            index += 1
            while index < len(lines) and not lines[index].strip():
                index += 1
            caption_lines = []
            while index < len(lines) and lines[index].strip():
                caption_lines.append(lines[index].strip())
                index += 1
            caption = " ".join(caption_lines).strip()
            if caption.startswith("*") and caption.endswith("*"):
                caption = caption[1:-1]
            story.append(
                KeepTogether(
                    [
                        scaled_image(image_path),
                        Paragraph(inline_markup(caption), STYLES["caption"]),
                    ]
                )
            )
            continue

        if line.startswith("| "):
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            rows = []
            for table_line in table_lines:
                cells = [cell.strip() for cell in table_line.strip("|").split("|")]
                if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                    continue
                rows.append(cells)
            story.extend([make_table(rows), Spacer(1, 4 * mm)])
            continue

        if line.startswith("- "):
            while index < len(lines) and lines[index].strip().startswith("- "):
                item = lines[index].strip()[2:]
                story.append(Paragraph(f"&#8226;&nbsp;&nbsp;{inline_markup(item)}", STYLES["bullet"]))
                index += 1
            story.append(Spacer(1, 2 * mm))
            continue

        if re.match(r"\d+\. ", line):
            while index < len(lines) and re.match(r"\d+\. ", lines[index].strip()):
                item_line = lines[index].strip()
                number, item = item_line.split(". ", 1)
                story.append(
                    Paragraph(
                        f'<font name="{FONT_BOLD}">{number}.</font>&nbsp;&nbsp;{inline_markup(item)}',
                        STYLES["bullet"],
                    )
                )
                index += 1
            story.append(Spacer(1, 2 * mm))
            continue

        paragraph_lines = [line]
        index += 1
        while index < len(lines) and not is_special(lines[index]):
            paragraph_lines.append(lines[index].strip())
            index += 1
        story.append(
            Paragraph(inline_markup(" ".join(paragraph_lines)), STYLES["body"])
        )

    return story


def build_pdf() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=LEFT,
        rightMargin=RIGHT,
        topMargin=TOP,
        bottomMargin=BOTTOM,
        title="Assignment 4 - Complete Kubeflow MLOps Pipeline",
        author="MLOps Coursework",
        subject="Customer Support Query Classification System",
    )
    frame = Frame(LEFT, BOTTOM, CONTENT_W, PAGE_H - TOP - BOTTOM, id="main")
    doc.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=footer)])
    doc.build(report_story())
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()
