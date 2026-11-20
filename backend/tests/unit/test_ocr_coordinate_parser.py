from app.utils.coordinate_parser import parse_coordinates_from_text


def test_parse_decimal_degrees_labeled():
    text = "Latitude: 16.7050° N, Longitude: 74.2450° E"
    res = parse_coordinates_from_text(text)
    assert res.is_valid is True
    assert res.latitude == 16.705
    assert res.longitude == 74.245


def test_parse_decimal_degrees_short_labels():
    text = "Lat: 16.7050 N, Long: 74.2450 E"
    res = parse_coordinates_from_text(text)
    assert res.is_valid is True
    assert res.latitude == 16.705
    assert res.longitude == 74.245


def test_parse_dms_coordinates():
    text = '16° 42\' 18" N, 74° 14\' 42" E'
    res = parse_coordinates_from_text(text)
    assert res.is_valid is True
    assert res.latitude == 16.705
    assert res.longitude == 74.245


def test_parse_dms_text_abbreviations():
    text = "16 deg 42 min 18 sec N, 74 deg 14 min 42 sec E"
    res = parse_coordinates_from_text(text)
    assert res.is_valid is True
    assert res.latitude == 16.705
    assert res.longitude == 74.245


def test_parse_southern_and_western_hemispheres():
    text = "Latitude: 16.7050° S, Longitude: 74.2450° W"
    res = parse_coordinates_from_text(text)
    assert res.is_valid is True
    assert res.latitude == -16.705
    assert res.longitude == -74.245


def test_parse_signed_decimal_pair():
    text = "Coordinates: -16.7050, -74.2450 (GPS)"
    res = parse_coordinates_from_text(text)
    assert res.is_valid is True
    assert res.latitude == -16.705
    assert res.longitude == -74.245


def test_parse_multiline_banner_with_noise():
    text = """
    CHECK DAM SITE #4
    Elevation: 580m MSL
    16.7050 N, 74.2450 E
    Timestamp: 2026-10-24 11:30:00
    Accuracy: 3.2m
    """
    res = parse_coordinates_from_text(text)
    assert res.is_valid is True
    assert res.latitude == 16.705
    assert res.longitude == 74.245


def test_parse_ocr_degree_misread_as_zero():
    # Common OCR artifact: 16.7050° N -> 16.70500 N
    text = "Latitude: 16.70500 N Longitude: 74.24500 E"
    res = parse_coordinates_from_text(text)
    assert res.is_valid is True
    assert res.latitude == 16.705
    assert res.longitude == 74.245


def test_parse_empty_or_non_coordinate_text():
    assert parse_coordinates_from_text("").is_valid is False
    assert parse_coordinates_from_text("Just some scenery without stamps").is_valid is False
    assert parse_coordinates_from_text("Photo taken at noon").latitude is None


def test_parse_partial_coordinates():
    only_lat = parse_coordinates_from_text("Latitude: 16.7050° N, Elevation: 580m")
    assert only_lat.is_valid is False
    assert only_lat.latitude == 16.705
    assert only_lat.longitude is None

    only_lon = parse_coordinates_from_text("Longitude: 74.2450° E, Heading: 180°")
    assert only_lon.is_valid is False
    assert only_lon.latitude is None
    assert only_lon.longitude == 74.245


def test_reject_out_of_range_coordinates():
    # Latitude > 90 must be rejected
    invalid_lat = parse_coordinates_from_text("Latitude: 95.5000° N, Longitude: 74.2450° E")
    assert invalid_lat.is_valid is False
    assert invalid_lat.latitude is None
    assert invalid_lat.longitude == 74.245

    # Longitude > 180 must be rejected
    invalid_lon = parse_coordinates_from_text("Latitude: 16.7050° N, Longitude: 195.2450° E")
    assert invalid_lon.is_valid is False
    assert invalid_lon.latitude == 16.705
    assert invalid_lon.longitude is None

