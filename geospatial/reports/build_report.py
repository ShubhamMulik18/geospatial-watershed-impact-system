from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def build_report(report_payload, output_path):
    """
    Build a simple PDF report from geospatial analysis results.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
    )

    styles = getSampleStyleSheet()

    story = []

    title = report_payload.get(
        "title",
        "Geospatial Watershed Analysis Report",
    )

    story.append(
        Paragraph(title, styles["Title"])
    )

    story.append(Spacer(1, 12))

    analysis_id = report_payload.get(
        "analysis_id",
        "N/A",
    )

    story.append(
        Paragraph(
            f"Analysis ID: {analysis_id}",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 12))

    metrics = report_payload.get(
        "metrics",
        {},
    )

    if metrics:
        table_data = [
            ["Metric", "Value"],
        ]

        for name, value in metrics.items():
            table_data.append(
                [str(name), str(value)]
            )

        table = Table(table_data)

        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        story.append(table)

        story.append(Spacer(1, 12))

    limitations = report_payload.get(
        "limitations",
        "Observed change does not prove that the intervention caused the change.",
    )

    story.append(
        Paragraph(
            f"Limitations: {limitations}",
            styles["Normal"],
        )
    )

    document.build(story)

    return output_path