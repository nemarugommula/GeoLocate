from __future__ import annotations
import time
from geoclip import GeoCLIP
from geopy.geocoders import Nominatim
from config import NOMINATIM_USER_AGENT

geolocator = Nominatim(user_agent=NOMINATIM_USER_AGENT)


def load_geoclip():
    return GeoCLIP()


def predict_location(image_path: str, model: GeoCLIP, top_k: int = 5) -> list[dict]:
    top_gps, top_probs = model.predict(image_path, top_k=top_k)

    predictions = []
    for gps, prob in zip(top_gps, top_probs):
        lat, lon, p = float(gps[0]), float(gps[1]), float(prob)
        place = _reverse_geocode(lat, lon)
        country = place.split(",")[-1].strip() if "," in place else place

        predictions.append({
            "lat": lat,
            "lon": lon,
            "prob": round(p, 4),
            "place": place,
            "country": country,
        })

    return predictions


def _reverse_geocode(lat: float, lon: float) -> str:
    try:
        time.sleep(1)
        loc = geolocator.reverse(f"{lat}, {lon}", language="en", exactly_one=True)
        if loc:
            addr = loc.raw.get("address", {})
            parts = [addr.get(k) for k in ["town", "city", "state", "country"] if k in addr]
            return ", ".join(parts) if parts else loc.address[:80]
    except Exception:
        pass
    return "unknown"
