"""Unit tests for GeofenceValidator — multi-geofence any-match logic."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services.geofence_validator import GeofenceValidator
from app.models.geofence_location import GeofenceLocation


def _make_geofence(name="Office", lat=28.6139, lng=77.2090, radius=200):
    g = MagicMock(spec=GeofenceLocation)
    g.name = name
    g.latitude = lat
    g.longitude = lng
    g.radius_meters = radius
    return g


@pytest.fixture
def validator():
    return GeofenceValidator()


class TestManualMethod:
    def test_manual_skips_all_checks(self, validator):
        """method=manual should never raise regardless of coords."""
        validator.validate("manual", [], None, None)

    def test_both_without_coords_still_skips_when_manual(self, validator):
        validator.validate("manual", None, None, None)


class TestMissingCoordinates:
    def test_geofence_method_no_lat_raises_422(self, validator):
        g = _make_geofence()
        with pytest.raises(HTTPException) as exc:
            validator.validate("geofence", [g], None, 77.2090)
        assert exc.value.status_code == 422

    def test_geofence_method_no_lng_raises_422(self, validator):
        g = _make_geofence()
        with pytest.raises(HTTPException) as exc:
            validator.validate("geofence", [g], 28.6139, None)
        assert exc.value.status_code == 422

    def test_both_method_no_coords_raises_422(self, validator):
        g = _make_geofence()
        with pytest.raises(HTTPException) as exc:
            validator.validate("both", [g], None, None)
        assert exc.value.status_code == 422


class TestEmptyGeofenceList:
    def test_empty_list_raises_500(self, validator):
        with pytest.raises(HTTPException) as exc:
            validator.validate("geofence", [], 28.6139, 77.2090)
        assert exc.value.status_code == 500

    def test_none_list_raises_500(self, validator):
        with pytest.raises(HTTPException) as exc:
            validator.validate("geofence", None, 28.6139, 77.2090)
        assert exc.value.status_code == 500


class TestAnyMatchLogic:
    def test_within_first_geofence_passes(self, validator):
        g = _make_geofence()
        with patch("app.services.geofence_validator.is_within_geofence", return_value=(True, 50.0)):
            validator.validate("geofence", [g], 28.6139, 77.2090)

    def test_within_second_geofence_passes(self, validator):
        """Should pass even if employee is outside the first geofence."""
        g1 = _make_geofence("HQ")
        g2 = _make_geofence("Branch")

        def side_effect(lat, lng, glat, glng, radius):
            return (True, 30.0) if glat == g2.latitude else (False, 5000.0)

        with patch("app.services.geofence_validator.is_within_geofence", side_effect=side_effect):
            validator.validate("geofence", [g1, g2], 13.0, 80.0)

    def test_outside_all_geofences_raises_403(self, validator):
        g1 = _make_geofence("HQ")
        g2 = _make_geofence("Branch")
        with patch("app.services.geofence_validator.is_within_geofence", return_value=(False, 9999.0)):
            with pytest.raises(HTTPException) as exc:
                validator.validate("geofence", [g1, g2], 0.0, 0.0)
        assert exc.value.status_code == 403
        assert "HQ" in exc.value.detail
        assert "Branch" in exc.value.detail

    def test_accuracy_expands_radius(self, validator):
        """GPS accuracy should expand the effective fence radius."""
        g = _make_geofence(radius=100)
        captured = {}

        def capture(lat, lng, glat, glng, radius):
            captured["radius"] = radius
            return (True, 0.0)

        with patch("app.services.geofence_validator.is_within_geofence", side_effect=capture):
            validator.validate("geofence", [g], 28.6139, 77.2090, accuracy_meters=50.0)

        assert captured["radius"] == 150.0
