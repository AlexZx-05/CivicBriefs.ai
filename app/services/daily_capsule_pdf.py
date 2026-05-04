from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)
_REPORTLAB_WARNED = False


def build_daily_capsule_pdf(*, date_str: str, output_path: str) -> Path | None:
    """
    Build a lightweight PDF from the same daily capsule payload exposed to dashboard.
    Returns created file path, or None on failure.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception:
        global _REPORTLAB_WARNED
        if not _REPORTLAB_WARNED:
            logger.warning(
                "daily_capsule_pdf: reportlab unavailable; install with `pip install reportlab` "
                "or `pip install -r app/requirements.txt`"
            )
            _REPORTLAB_WARNED = True
        return None

    from app.services.news_summary import news_summary_service

    try:
        payload = news_summary_service.get_capsules("daily")
    except Exception as exc:
        logger.warning("daily_capsule_pdf: unable to load daily capsules: %s", exc)
        return None

    capsules = payload.get("capsules") if isinstance(payload, dict) else None
    if not isinstance(capsules, list):
        return None

    target = None
    for item in capsules:
        if isinstance(item, dict) and str(item.get("date", "")).strip() == date_str:
            target = item
            break
    if not isinstance(target, dict):
        return None

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        name="CapsuleTitle",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        spaceAfter=10,
    )
    section_title = ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=8,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        name="Body",
        parent=styles["BodyText"],
        fontSize=10,
        leading=13,
        spaceAfter=4,
    )

    story = []
    story.append(Paragraph("CivicBriefs Daily News Capsule", title))
    story.append(Paragraph(f"Date: {date_str}", styles["Normal"]))
    totals = target.get("totals") if isinstance(target.get("totals"), dict) else {}
    story.append(
        Paragraph(
            f"Articles: {int(totals.get('articles', 0) or 0)} | Categories: {int(totals.get('categories', 0) or 0)}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    sections = target.get("sections") if isinstance(target.get("sections"), list) else []
    for section in sections:
        if not isinstance(section, dict):
            continue
        label = str(section.get("label", "General")).strip()
        total_articles = int(section.get("total_articles", 0) or 0)
        story.append(Paragraph(f"{label} ({total_articles})", section_title))
        articles = section.get("articles") if isinstance(section.get("articles"), list) else []
        for article in articles[:5]:
            if not isinstance(article, dict):
                continue
            title_text = str(article.get("title", "Untitled")).strip()
            source_text = str(article.get("source", "Unknown")).strip()
            story.append(Paragraph(f"<b>{title_text}</b> - {source_text}", body))
            points = article.get("summary_points") if isinstance(article.get("summary_points"), list) else []
            for point in points[:3]:
                story.append(Paragraph(f"- {str(point)}", body))
            story.append(Spacer(1, 0.06 * inch))
        story.append(Spacer(1, 0.08 * inch))

    try:
        doc = SimpleDocTemplate(
            str(out),
            pagesize=A4,
            rightMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            topMargin=0.65 * inch,
            bottomMargin=0.65 * inch,
        )
        doc.build(story)
    except Exception as exc:
        logger.warning("daily_capsule_pdf: PDF build failed: %s", exc)
        return None

    return out
