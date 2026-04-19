"""Geofence validation: check GPS coordinates against a list of policy geofences."""
from typing import Optional, List

from fastapi import HTTPException, status

from app.utils.geofence import is_within_geofence


class GeofenceValidator:
    """Validates clock-in/out coordinates against any of the assigned geofences.

    Stateless — no DB or session required. Instantiate once per request
    or use as a shared singleton.

    Clock-in succeeds if the employee is within ANY assigned geofence.
    """

    def validate(
        self,
        method: str,
        geofences: Optional[List],
        lat: Optional[float],
        lng: Optional[float],
        accuracy_meters: Optional[float] = None,
    ) -> None:
        """Raise HTTPException if location is required but invalid or out of range.

        accuracy_meters: GPS accuracy reported by the device. Expands the
        effective fence radius to absorb GPS jitter and avoid false rejections.
        """
        if method not in ("geofence", "both"):
            return

        if lat is None or lng is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Location (latitude, longitude) is required for geofence-based attendance",
            )
        if not geofences:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No geofence locations configured for this policy. Contact admin.",
            )

        for geofence in geofences:
            effective_radius = geofence.radius_meters + (accuracy_meters or 0.0)
            is_within, _ = is_within_geofence(
                lat, lng,
                geofence.latitude, geofence.longitude,
                effective_radius,
            )
            if is_within:
                return

        # None matched — report distance to the primary (first) geofence
        primary = geofences[0]
        _, distance = is_within_geofence(lat, lng, primary.latitude, primary.longitude, primary.radius_meters)
        names = ", ".join(f"'{g.name}'" for g in geofences)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"You are {distance:.0f}m from '{primary.name}' and outside all assigned locations "
                f"({names}). Move to a valid location to clock in."
            ),
        )
