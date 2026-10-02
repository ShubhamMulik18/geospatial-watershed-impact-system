from app.schemas.errors import ErrorBody, ErrorResponse


def test_error_response_matches_contract():
    response = ErrorResponse(
        error=ErrorBody(
            code="INVALID_POLYGON",
            message="The supplied GeoJSON polygon is invalid.",
            details={},
        )
    )

    assert response.error.code == "INVALID_POLYGON"
    assert response.error.message == "The supplied GeoJSON polygon is invalid."
    assert response.error.details == {}


def test_error_response_serializes_with_error_envelope():
    response = ErrorResponse(
        error=ErrorBody(
            code="PREDICTION_REQUIRED",
            message="A prediction is required before analysis creation.",
        )
    )

    assert response.model_dump() == {
        "error": {
            "code": "PREDICTION_REQUIRED",
            "message": "A prediction is required before analysis creation.",
            "details": {},
        }
    }