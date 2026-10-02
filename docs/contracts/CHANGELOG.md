# Contract Changelog

## Version 1.0

Status: Baseline

This is the initial shared contract baseline for the Geospatial Watershed
Impact Analysis System.

### Added

- Common geographic and numeric validation types.
- Standard API error response.
- Photo response contract.
- Prediction response contract.
- Dataset catalogue response contract.
- Analysis request contract.
- Analysis lifecycle response contract.
- Shared enum definitions.
- Canonical sample fixtures.

### Contract Rules

- JSON fields use snake_case.
- IDs are opaque strings.
- Dates use YYYY-MM-DD.
- Timestamps use UTC ISO 8601.
- Unavailable values use null.
- Numeric values must be finite.
- Relative URLs resolve against the backend origin.

### Phase 0 Scope

This baseline only defines and verifies shared schemas and contract fixtures.

It does not implement:

- FastAPI endpoints
- Database models
- PostgreSQL/PostGIS integration
- Alembic migrations
- Photo upload processing
- Background workers
- Real AI inference
- Real geospatial processing

Those belong to later project phases.