import html
from io import BytesIO
from typing import Any, Dict, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_scouting_pdf(player_data: Dict[str, Any], schemes_data: List[Dict[str, Any]], dossier_text: str) -> BytesIO:
    """Generates an executive, print-ready defensive scouting report in PDF format."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0284C7"),
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1E293B"),
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )
    table_text = ParagraphStyle(
        "TableText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1E293B"),
    )
    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    elements = []

    # Header Banner
    elements.append(Paragraph("APEX-NGS | TACTICAL SCOUTING DOSSIER", subtitle_style))
    elements.append(Spacer(1, 4))
    player_name = player_data.get("player_name", "Target Player")
    team = player_data.get("team", "NFL")
    elements.append(Paragraph(f"{player_name} — #{team}", title_style))
    elements.append(Spacer(1, 6))

    # Divider Line
    divider = Table([[""]], colWidths=[540], rowHeights=[2])
    divider.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0284C7")),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(divider)
    elements.append(Spacer(1, 10))

    # Spatial Tracking Baseline Metrics Table
    elements.append(Paragraph("NEXT GEN STATS SPATIAL TRACKING BASELINE", section_heading))
    elements.append(Spacer(1, 6))

    metrics_table_data = [
        [
            Paragraph("Avg Separation", table_header),
            Paragraph("Avg Cushion", table_header),
            Paragraph("Route Sep Index (RSI)", table_header),
            Paragraph("Intended Air Yards", table_header),
            Paragraph("Catch %", table_header),
            Paragraph("Target Volume", table_header),
        ],
        [
            Paragraph(f"{float(player_data.get('separation', 0.0)):.2f} yds", table_text),
            Paragraph(f"{float(player_data.get('cushion', 0.0)):.2f} yds", table_text),
            Paragraph(f"{float(player_data.get('route_separation_index', 0.0)):.2f}", table_text),
            Paragraph(f"{float(player_data.get('air_yards', 0.0)):.1f} yds", table_text),
            Paragraph(f"{float(player_data.get('catch_pct', 0.0)):.1f}%", table_text),
            Paragraph(str(player_data.get("targets", 0)), table_text),
        ],
    ]

    t_metrics = Table(metrics_table_data, colWidths=[90] * 6)
    t_metrics.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94A3B8")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_metrics)
    elements.append(Spacer(1, 12))

    # Defensive Scheme Vulnerability Matrix
    elements.append(Paragraph("DEFENSIVE SCHEME MATCHUP VULNERABILITY MATRIX", section_heading))
    elements.append(Spacer(1, 6))

    scheme_rows = [
        [
            Paragraph("Coverage Scheme", table_header),
            Paragraph("Projected Sep", table_header),
            Paragraph("Delta", table_header),
            Paragraph("Win Rate", table_header),
            Paragraph("Leverage Rating", table_header),
            Paragraph("Secondary Coaching Mandate", table_header),
        ]
    ]

    for s in schemes_data:
        scheme_rows.append([
            Paragraph(s["scheme"], table_text),
            Paragraph(f"{s['projected_separation']} yds", table_text),
            Paragraph(f"{s['baseline_diff']:+.2f} yds", table_text),
            Paragraph(f"{s['win_rate']}%", table_text),
            Paragraph(s["leverage_rating"], table_text),
            Paragraph(s["coaching_mandate"], table_text),
        ])

    t_schemes = Table(scheme_rows, colWidths=[105, 55, 45, 55, 105, 175])
    t_schemes.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#64748B")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_schemes)
    elements.append(Spacer(1, 12))

    # Tactical Game Plan Mandates
    elements.append(Paragraph("TACTICAL GAME PLAN & COACHING MANDATES", section_heading))
    elements.append(Spacer(1, 6))

    clean_dossier = dossier_text.replace("### ", "").replace("**", "")
    for line in clean_dossier.split("\n"):
        line = line.strip()
        if not line:
            elements.append(Spacer(1, 3))
            continue
        safe_line = html.escape(line)
        elements.append(Paragraph(safe_line, body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer