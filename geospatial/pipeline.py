from pathlib import Path

from geospatial.indices.ndvi import calculate_ndvi
from geospatial.indices.water import calculate_ndwi
from geospatial.analysis.statistics import calculate_statistics
from geospatial.analysis.comparison import compare_values
from geospatial.outputs.rasters import save_raster
from geospatial.outputs.previews import create_raster_preview
from geospatial.reports.charts import create_time_series_chart
from geospatial.reports.build_report import build_report


def run_analysis(request, output_dir):
    """
    Run the basic geospatial analysis pipeline.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    red = request["red"]
    nir = request["nir"]
    green = request["green"]

    ndvi = calculate_ndvi(nir, red)
    ndwi = calculate_ndwi(green, nir)

    ndvi_stats = calculate_statistics(ndvi)
    ndwi_stats = calculate_statistics(ndwi)

    result = {
        "metrics": {
            "mean_ndvi": ndvi_stats["mean"],
            "mean_ndwi": ndwi_stats["mean"],
        },
        "statistics": {
            "ndvi": ndvi_stats,
            "ndwi": ndwi_stats,
        },
    }

    return result