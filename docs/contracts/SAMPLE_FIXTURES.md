# Shared Contract Sample Fixtures

## Photo Response

{
  "photo_id": "photo-001",
  "latitude": 16.7,
  "longitude": 74.24,
  "capture_date": null,
  "exif_status": "partial",
  "warnings": [
    "Capture date is unavailable."
  ]
}

## Prediction Response

{
  "prediction_id": "prediction-001",
  "photo_id": "photo-001",
  "class_id": "check_dam",
  "predicted_class": "Check Dam",
  "confidence": 0.92,
  "requires_verification": false,
  "model_version": "intervention-mobilenetv2-v1"
}

## Dataset Response

{
  "dataset_id": "dataset-2021",
  "display_name": "Demo region 2021",
  "year": 2021,
  "coverage_available": true,
  "acquisition_date": "2021-02-15",
  "supported_indicators": [
    "ndvi",
    "water"
  ],
  "water_methods": [
    "ndwi",
    "mndwi"
  ],
  "bounds_wgs84": [
    74.0,
    16.5,
    74.5,
    17.0
  ],
  "resolution_metres": 20,
  "quality_mask_available": true,
  "warnings": []
}

## Analysis Request

{
  "photo_id": "photo-001",
  "polygon": {
    "type": "Polygon",
    "coordinates": [
      [
        [74.24, 16.70],
        [74.25, 16.70],
        [74.25, 16.71],
        [74.24, 16.71],
        [74.24, 16.70]
      ]
    ]
  },
  "dataset_ids": [
    "dataset-2021",
    "dataset-2026"
  ],
  "indicators": [
    "ndvi",
    "water"
  ]
}

## Completed Analysis Response

{
  "schema_version": "1.0",
  "analysis_id": "analysis-001",
  "status": "completed",
  "stage": "finished",
  "prediction": {
    "class": "Check Dam",
    "class_id": "check_dam",
    "confidence": 0.92,
    "requires_verification": false,
    "model_version": "intervention-mobilenetv2-v1"
  },
  "metrics": {
    "ndvi_before": 0.42,
    "ndvi_after": 0.57,
    "ndvi_change": 0.15,
    "water_before_hectares": 3.1,
    "water_after_hectares": 5.8,
    "water_change_hectares": 2.7,
    "water_change_percent": 87.096774
  },
  "series": [
    {
      "dataset_id": "dataset-2021",
      "date": "2021-02-15",
      "ndvi_mean": 0.42,
      "water_hectares": 3.1
    },
    {
      "dataset_id": "dataset-2026",
      "date": "2026-02-17",
      "ndvi_mean": 0.57,
      "water_hectares": 5.8
    }
  ],
  "warnings": [
    "Observed change does not prove that the intervention caused the change."
  ],
  "report_status": "not_requested",
  "error": null
}

## Error Response

{
  "error": {
    "code": "INVALID_POLYGON",
    "message": "The supplied GeoJSON polygon is invalid.",
    "details": {}
  }
}

## Contract Rules

- JSON fields use snake_case.
- IDs are opaque strings.
- Dates use YYYY-MM-DD.
- Timestamps use UTC ISO 8601.
- Unavailable values use null.
- Numeric values must be finite.
- Relative URLs resolve against the backend origin.