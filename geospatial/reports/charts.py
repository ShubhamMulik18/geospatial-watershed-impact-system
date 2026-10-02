from pathlib import Path

import matplotlib.pyplot as plt


def create_time_series_chart(
    dates,
    values,
    output_path,
    title="Time Series",
    y_label="Value",
):
    """
    Create a simple time-series chart.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(figsize=(8, 5))

    plt.plot(
        dates,
        values,
        marker="o",
    )

    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel(y_label)
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()

    return output_path