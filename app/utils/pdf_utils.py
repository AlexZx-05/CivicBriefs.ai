import logging
from datetime import datetime
from pathlib import Path

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

logger = logging.getLogger(__name__)


def create_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="CategoryTitle",
            parent=styles["Heading1"],
            fontSize=17,
            textColor="#13372f",
            spaceBefore=14,
            spaceAfter=8,
            leading=21,
            fontName="Helvetica-Bold",
        )
    )

    styles.add(
        ParagraphStyle(
            name="CapsuleTitle",
            parent=styles["Heading2"],
            fontSize=13.5,
            textColor="#1f2d2a",
            spaceBefore=10,
            spaceAfter=7,
            leading=17,
            fontName="Helvetica-Bold",
        )
    )

    styles.add(
        ParagraphStyle(
            name="Summary",
            parent=styles["BodyText"],
            fontSize=10.5,
            textColor="#263633",
            alignment=TA_JUSTIFY,
            leading=14,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            parent=styles["Heading3"],
            fontSize=11.5,
            textColor="#20453e",
            spaceBefore=8,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        )
    )

    styles.add(
        ParagraphStyle(
            name="ListItem",
            parent=styles["BodyText"],
            fontSize=10,
            textColor="#2d3f3a",
            leftIndent=14,
            leading=13,
            spaceAfter=3,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Meta",
            parent=styles["BodyText"],
            fontSize=8.8,
            textColor="#5a6966",
            leading=11,
            spaceAfter=2,
        )
    )

    return styles


def build_pdf_from_markdown(md_file: str, output_pdf: str):
    """
    Convert capsule markdown to a readable PDF with section-wise rendering.
    """
    text = Path(md_file).read_text(encoding="utf-8")
    styles = create_styles()
    story = []

    story.append(Paragraph("<b>UPSC News Capsules</b>", styles["Heading1"]))
    story.append(
        Paragraph(
            f"Generated on: {datetime.utcnow().strftime('%d %B %Y')}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.24 * inch))

    current_category = None
    current_title = None
    current_section = "Summary"
    sections = {}
    meta = []

    preferred_order = [
        "In Simple Words",
        "Why It Matters for UPSC",
        "Prelims Pointers",
        "Mains Angle",
        "Key Terms",
        "Relevant PYQ",
        "Relevant Syllabus",
        "Summary",
    ]

    def flush_article():
        if not current_title:
            return

        story.append(Paragraph(current_title, styles["CapsuleTitle"]))

        ordered = preferred_order + [k for k in sections.keys() if k not in preferred_order]
        for sec_name in ordered:
            items = sections.get(sec_name, [])
            if not items:
                continue

            story.append(Paragraph(f"{sec_name}:", styles["SectionHeader"]))
            for item in items:
                if item.startswith("[[TEXT]]"):
                    story.append(Paragraph(item.replace("[[TEXT]]", "", 1).strip(), styles["Summary"]))
                else:
                    story.append(Paragraph(f"* {item}", styles["ListItem"]))

        for line in meta:
            story.append(Paragraph(line, styles["Meta"]))

        story.append(Spacer(1, 0.18 * inch))

    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ln == "---":
            continue

        if ln.startswith("## "):
            flush_article()
            current_category = ln[3:].strip()
            story.append(Paragraph(current_category, styles["CategoryTitle"]))
            current_title = None
            current_section = "Summary"
            sections = {}
            meta = []
            continue

        if ln.startswith("### "):
            flush_article()
            current_title = ln[4:].strip()
            current_section = "Summary"
            sections = {"Summary": []}
            meta = []
            continue

        if ln.startswith("**") and ln.endswith("**"):
            current_section = ln.strip("* ").strip()
            sections.setdefault(current_section, [])
            continue

        if ln.startswith("-") or ln.startswith("*"):
            item = ln.lstrip("-* ").strip()
            lowered = item.lower()
            if lowered.startswith("source:") or lowered.startswith("url:") or lowered.startswith("chunks:"):
                meta.append(item)
            else:
                sections.setdefault(current_section, []).append(item)
            continue

        # Plain text line under current section.
        sections.setdefault(current_section, []).append(f"[[TEXT]] {ln}")

    flush_article()

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=0.5 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    doc.build(story)
    logger.info("PDF created: %s", output_pdf)
    return output_pdf
