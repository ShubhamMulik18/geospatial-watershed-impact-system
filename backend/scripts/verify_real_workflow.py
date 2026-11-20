import os
import sys
import uuid
from pathlib import Path

# Add backend and root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(backend_dir))

# Configure PROJ to use rasterio's internal PROJ data to prevent PostgreSQL PostGIS PROJ conflicts
proj_data_path = backend_dir / ".venv" / "Lib" / "site-packages" / "rasterio" / "proj_data"
if proj_data_path.exists():
    os.environ["PROJ_LIB"] = str(proj_data_path)
    os.environ["PROJ_DATA"] = str(proj_data_path)

# Force production environment for real geospatial processing
os.environ["APP_ENV"] = "production"

from fastapi.testclient import TestClient
from app.main import create_app
from app.db.session import SessionLocal
from app.models.photo import Photo
from app.models.analysis import Analysis
from app.workers.analysis_worker import AnalysisWorker
from app.integrations.geospatial.production_adapter import ProductionGeospatialAdapter


def run_verification():
    print("=" * 70)
    print("STARTING END-TO-END REAL WORKFLOW VERIFICATION")
    print("=" * 70)

    app = create_app()
    client = TestClient(app)

    # 1. Verify Health
    print("\n--- 1. Testing Backend Health Endpoint ---")
    resp = client.get("/api/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    print(f"Health response: {resp.json()}")

    # 2. Verify Datasets
    print("\n--- 2. Testing Datasets Catalog Endpoint ---")
    resp = client.get("/api/datasets")
    assert resp.status_code == 200, f"List datasets failed: {resp.text}"
    datasets = resp.json()
    print(f"Retrieved {len(datasets)} datasets from database:")
    for ds in datasets:
        print(f"  - [{ds['year']}] {ds['display_name']} (ID: {ds['dataset_id']})")
    assert len(datasets) >= 3, "Expected at least 3 satellite datasets"
    dataset_ids = [ds["dataset_id"] for ds in sorted(datasets, key=lambda d: d["year"])]

    # 3. Verify Photo & Prediction
    print("\n--- 3. Testing Photo & AI Prediction ---")
    db = SessionLocal()
    try:
        photos = db.query(Photo).all()
        valid_photo = next((p for p in photos if Path(p.safe_path).exists()), None)
        if valid_photo is None:
            from io import BytesIO
            from PIL import Image
            buf = BytesIO()
            Image.new("RGB", (224, 224), color=(100, 150, 80)).save(buf, format="JPEG")
            buf.seek(0)
            upload_resp = client.post(
                "/api/photos",
                files={"file": ("field_intervention.jpg", buf, "image/jpeg")},
            )
            assert upload_resp.status_code == 201, f"Photo upload failed: {upload_resp.text}"
            photo_id = upload_resp.json()["photo_id"]
            print(f"Uploaded new field photo ID: {photo_id}")
        else:
            photo_id = str(valid_photo.id)
            print(f"Selected existing photo ID: {photo_id} ({valid_photo.original_name})")
    finally:
        db.close()

    resp = client.post(f"/api/photos/{photo_id}/prediction")
    assert resp.status_code == 201, f"Prediction failed: {resp.text}"
    pred_data = resp.json()
    print(f"AI Prediction: Class='{pred_data['predicted_class']}', Confidence={pred_data['confidence']:.3f}, Model={pred_data.get('model_version')}")

    # 4. Create Analysis Request
    print("\n--- 4. Submitting Real Analysis Request ---")
    polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [74.24, 16.70],
                [74.25, 16.70],
                [74.25, 16.71],
                [74.24, 16.71],
                [74.24, 16.70],
            ]
        ],
    }

    payload = {
        "photo_id": photo_id,
        "polygon": polygon,
        "dataset_ids": dataset_ids,
        "indicators": ["ndvi", "water"],
    }

    resp = client.post("/api/analyses", json=payload)
    assert resp.status_code == 202, f"Create analysis failed: {resp.text}"
    created_analysis = resp.json()
    analysis_id = created_analysis["analysis_id"]
    print(f"Analysis created with ID: {analysis_id}, Status: {created_analysis['status']}")

    # 5. Process Job with Real Geospatial Pipeline
    print("\n--- 5. Processing Analysis Job with Real Sentinel-2 JP2 Rasters ---")
    db = SessionLocal()
    try:
        current = db.get(Analysis, uuid.UUID(analysis_id))
        print(f"Current analysis state: {current.status} (error: {current.error})")
        if current.status in ["created", "queued"]:
            worker = AnalysisWorker(
                db=db,
                geospatial_adapter=ProductionGeospatialAdapter(),
            )
            worker.process_job(current)
            print("Geospatial pipeline processing completed successfully by worker!")
        else:
            print(f"Analysis was processed to '{current.status}' by background worker task.")
    finally:
        db.close()

    # 6. Retrieve Persisted Analysis & Verify Results
    print("\n--- 6. Retrieving Persisted Analysis Results ---")
    resp = client.get(f"/api/analyses/{analysis_id}")
    assert resp.status_code == 200, f"Get analysis failed: {resp.text}"
    result = resp.json()
    assert result["status"] == "completed", f"Expected completed status, got: {result['status']}"

    print(f"Analysis Status: {result['status']}")
    print(f"Stage: {result['stage']}")
    print(f"Quality: {result['quality']}")
    print(f"Metrics: {result['metrics']}")
    print(f"Series (Chronological observations):")
    for pt in result.get("series", []):
        print(f"  - Date: {pt['date']} | Mean NDVI: {pt['ndvi_mean']} | Water Area: {pt['water_hectares']} ha")
    print(f"Comparisons (Before/After):")
    for comp in result.get("comparisons", []):
        print(f"  - NDVI Change: {comp.get('ndvi_change')} | Water Change: {comp.get('water_change_hectares')} ha ({comp.get('water_change_percent')}%)")

    # Verify scientific metrics are genuine floats, not mock constants
    metrics = result["metrics"]
    assert metrics["ndvi_before"] is not None
    assert metrics["ndvi_after"] is not None
    assert metrics["ndvi_change"] is not None
    assert -1.0 <= metrics["ndvi_before"] <= 1.0, "NDVI out of valid range [-1, 1]"
    assert -1.0 <= metrics["ndvi_after"] <= 1.0, "NDVI out of valid range [-1, 1]"

    # Verify water metrics are authentic and do NOT falsely equal the common valid area
    assert metrics["water_before_hectares"] is not None
    assert metrics["water_after_hectares"] is not None
    assert metrics["water_before_hectares"] < result["quality"]["common_valid_hectares"]
    assert metrics["water_before_hectares"] == 0.37
    assert metrics["water_after_hectares"] == 0.90
    assert metrics["water_change_hectares"] == 0.53
    print("Verified: Water area correctly identifies surface water (0.37 ha -> 0.90 ha), not whole AOI!")

    # 7. Verify Layers & Descriptors
    print("\n--- 7. Verifying Raster Layers and Map Descriptors ---")
    layers = result.get("layers", [])
    print(f"Total layers generated: {len(layers)}")
    assert len(layers) > 0, "No layers returned in analysis result"
    for lyr in layers:
        print(f"  - Layer: {lyr['layer_id']} ({lyr['kind']}) | Dataset: {lyr['dataset_id']}")
        print(f"    Preview URL:  {lyr['preview_url']}")
        print(f"    Download URL: {lyr['download_url']}")
        print(f"    Bounds WGS84: {lyr['bounds_wgs84']}")
        print(f"    Preview CRS:  {lyr['preview_crs']}")

        # Test preview URL retrieval
        if lyr["preview_url"]:
            p_resp = client.get(lyr["preview_url"])
            assert p_resp.status_code == 200, f"Failed to retrieve preview: {lyr['preview_url']}"
            assert p_resp.headers["content-type"] == "image/png"
            assert p_resp.content[:8] == b"\x89PNG\r\n\x1a\n", "Invalid PNG header"

        # Test raster GeoTIFF download URL retrieval
        if lyr["download_url"]:
            r_resp = client.get(lyr["download_url"])
            assert r_resp.status_code == 200, f"Failed to retrieve raster: {lyr['download_url']}"
            assert r_resp.headers["content-type"] in ["image/tiff", "application/octet-stream"]
            assert len(r_resp.content) > 100, "GeoTIFF content too small"

    # 8. Verify PDF Report Download
    print("\n--- 8. Verifying PDF Report Download Endpoint ---")
    rep_resp = client.get(f"/api/analyses/{analysis_id}/report")
    assert rep_resp.status_code == 200, f"Failed to download report: {rep_resp.text}"
    assert rep_resp.headers["content-type"] == "application/pdf"
    assert rep_resp.content[:4] == b"%PDF", "Invalid PDF file header"
    print(f"Report downloaded successfully: {len(rep_resp.content)} bytes, Content-Type: {rep_resp.headers['content-type']}")

    print("\n" + "=" * 70)
    print("ALL END-TO-END VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_verification()
