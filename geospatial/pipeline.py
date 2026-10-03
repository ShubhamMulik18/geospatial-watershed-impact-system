from pathlib import Path
from geospatial.contracts import AnalysisRequest
from geospatial.indices.ndvi import calculate_ndvi
from geospatial.indices.water import calculate_ndwi
from geospatial.analysis.statistics import calculate_statistics
from geospatial.analysis.comparison import compare_values
#from geospatial.outputs.rasters import save_raster
#from geospatial.outputs.previews import create_raster_preview
from geospatial.reports.charts import create_time_series_chart
from geospatial.reports.build_report import build_report


def _get_first_dataset(request):
    if not request.dataset_specs:
        raise ValueError("At least one dataset specification is required.")

    return request.dataset_specs[0]


def run_analysis(request, output_dir, progress_callback=None):
    """
    Run the basic geospatial analysis pipeline.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not isinstance(request, AnalysisRequest):
        raise TypeError("request must be an AnalysisRequest.")
    dataset = _get_first_dataset(request)

    bands = dataset.get("bands", {})

    red = bands.get("red")
    nir = bands.get("nir")
    green = bands.get("green")

    if red is None or nir is None or green is None:
        raise ValueError(
            "Dataset must provide red, nir, and green band mappings."
        )

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