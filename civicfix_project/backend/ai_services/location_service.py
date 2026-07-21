"""
ai_services.location_service
-------------------------------
"Location should also need OpenAPI map integration" -> we use the free
OpenStreetMap Nominatim API (no API key required) to reverse-geocode the
citizen's GPS coordinates into a human-readable address, which gets
stored alongside the complaint.
"""

import requests
from django.conf import settings

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


def reverse_geocode(latitude: float, longitude: float) -> str:
    """
    Returns a human-readable address string for the given coordinates.
    Fails gracefully (returns an empty string) if the network/API is
    unavailable, so complaint submission never blocks on this.
    """
    if latitude is None or longitude is None:
        return ""

    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"lat": latitude, "lon": longitude, "format": "json"},
            headers={"User-Agent": settings.NOMINATIM_USER_AGENT},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("display_name", "")
    except Exception:
        return ""
