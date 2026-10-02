# Shared Contract Enums

This document records the enum values currently defined by the backend
contract for the Geospatial Watershed Impact Analysis System.

## EXIF Status

Used by `PhotoResponse.exif_status`.

Allowed values:

- `available`
- `partial`
- `missing`
- `invalid`

## Analysis Status

Used by `AnalysisResponse.status`.

Allowed values:

- `created`
- `queued`
- `running`
- `completed`
- `failed`

## Report Status

Used by `AnalysisResponse.report_status`.

Allowed values:

- `not_requested`
- `generating`
- `ready`
- `failed`

## Analysis Indicators

Used by `AnalysisRequest.indicators`.

Allowed values:

- `ndvi`
- `water`

## Contract Notes

- Enum values are lowercase `snake_case` strings unless otherwise specified.
- These values are part of the shared API contract.
- New values must not be introduced silently.
- Changes to enum values must be reflected in the corresponding Pydantic
  schemas, tests, and contract documentation.