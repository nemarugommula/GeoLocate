from __future__ import annotations
import time
from geopy.geocoders import Nominatim
from config import NOMINATIM_USER_AGENT

geolocator = Nominatim(user_agent=NOMINATIM_USER_AGENT)


def forward_geocode(place_name: str) -> dict | None:
    try:
        time.sleep(1)
        loc = geolocator.geocode(place_name)
        if loc:
            return {"lat": loc.latitude, "lon": loc.longitude, "display": loc.address}
    except Exception:
        pass
    return None


def reverse_geocode(lat: float, lon: float) -> dict | None:
    try:
        time.sleep(1)
        loc = geolocator.reverse(f"{lat}, {lon}", language="en", exactly_one=True)
        if loc:
            addr = loc.raw.get("address", {})
            return {
                "display": loc.address[:100],
                "country": addr.get("country", ""),
                "state": addr.get("state", ""),
                "city": addr.get("city", addr.get("town", "")),
            }
    except Exception:
        pass
    return None


def make_maps_url(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps?q={lat},{lon}"
