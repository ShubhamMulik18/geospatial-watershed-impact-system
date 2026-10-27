from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def build_report(report_payload, output_path):
    """
    Build a PDF report from geospatial analysis results.
    Optionally embeds a chart when chart_path is provided.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
    )

    styles = getSampleStyleSheet()
    story = []

    # Report title
    title = report_payload.get(
        "title",
        "Geospatial Watershed Analysis Report",
    )

    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))

    # Analysis ID
    analysis_id = report_payload.get("analysis_id", "N/A")

    story.append(
        Paragraph(
            f"Analysis ID: {analysis_id}",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 12))

    # Metrics table
    metrics = report_payload.get("metrics", {})

    if metrics:
        table_data = [["Metric", "Value"]]

        for name, value in metrics.items():
            table_data.append([str(name), str(value)])

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

    # Optional analysis chart
    chart_path = report_payload.get("chart_path")

    if chart_path:
        chart_path = Path(chart_path)

        if chart_path.is_file():
            story.append(
                Paragraph("Analysis Chart", styles["Heading2"])
            )
            story.append(Spacer(1, 8))

            story.append(
                Image(
                    str(chart_path),
                    width=450,
                    height=250,
                    kind="proportional",
                )
            )

            story.append(Spacer(1, 12))

    # Limitations
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

    # Generate PDF
    document.build(story)

    return output_path