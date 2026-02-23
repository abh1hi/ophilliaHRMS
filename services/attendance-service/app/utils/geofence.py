"""Geofence distance calculation utility using Haversine formula."""
from geopy.distance import geodesic
import logging

logger = logging.getLogger(__name__)


def is_within_geofence(
    user_lat: float,
    user_lng: float,
    fence_lat: float,
    fence_lng: float,
    radius_meters: int,
) -> tuple[bool, float]:
    """Check if user coordinates are within the geofence radius.

    Args:
        user_lat: User's latitude
        user_lng: User's longitude
        fence_lat: Geofence center latitude
        fence_lng: Geofence center longitude
        radius_meters: Allowed radius in meters

    Returns:
        Tuple of (is_within: bool, distance_meters: float)
    """
    user_point = (user_lat, user_lng)
    fence_point = (fence_lat, fence_lng)

    distance = geodesic(user_point, fence_point).meters
    is_within = distance <= radius_meters

    logger.info(
        f"Geofence check: distance={distance:.1f}m, radius={radius_meters}m, within={is_within}",
        extra={"service_task": "geofence_check"},
    )

    return is_within, round(distance, 2)
