import os
import sys
from pathlib import Path
from geoclip import GeoCLIP
from geopy.geocoders import Nominatim
import time
import json

FRAMES_DIR = Path(__file__).parent / "clip-high-signal"

print("Loading GeoCLIP model...")
model = GeoCLIP()
print("GeoCLIP loaded.\n")

geolocator = Nominatim(user_agent="geolens-phase0-test")

def reverse_geocode(lat, lon):
    try:
        time.sleep(1)
        loc = geolocator.reverse(f"{lat}, {lon}", language="en", exactly_one=True)
        if loc:
            addr = loc.raw.get("address", {})
            parts = []
            for key in ["village", "town", "city", "county", "state", "country"]:
                if key in addr:
                    parts.append(addr[key])
            return ", ".join(parts) if parts else loc.address[:80]
    except Exception:
        pass
    return "lookup failed"

frames = sorted(FRAMES_DIR.glob("*.jpg"))
if not frames:
    print(f"No frames found in {FRAMES_DIR}")
    sys.exit(1)

print(f"Testing {len(frames)} high-signal frames from CLIP filter")
print(f"Ground truth: Southern Province, Sri Lanka (~6.1°N, 80.5°E)")
print("=" * 100)

results = []

for frame_path in frames:
    name = frame_path.stem
    timestamp = name.split("_")[2] if len(name.split("_")) >= 3 else "?"

    start = time.time()
    top_gps, top_probs = model.predict(str(frame_path), top_k=5)
    elapsed = time.time() - start

    predictions = []
    for i, (gps, prob) in enumerate(zip(top_gps, top_probs)):
        lat, lon = float(gps[0]), float(gps[1])
        prob_val = float(prob)
        predictions.append({"lat": lat, "lon": lon, "prob": prob_val})

    best = predictions[0]
    location_name = reverse_geocode(best["lat"], best["lon"])

    result = {
        "frame": name,
        "timestamp": timestamp,
        "predictions": predictions,
        "best_location": location_name,
        "elapsed": round(elapsed, 2),
    }
    results.append(result)

    print(f"\n  [{timestamp}] {name[:50]}")
    print(f"    #1: {best['lat']:8.4f}°, {best['lon']:9.4f}°  (prob: {best['prob']:.4f})  → {location_name}")
    for i, p in enumerate(predictions[1:4], 2):
        print(f"    #{i}: {p['lat']:8.4f}°, {p['lon']:9.4f}°  (prob: {p['prob']:.4f})")
    print(f"    Time: {elapsed:.1f}s")

# Summary
print("\n" + "=" * 100)
print("  SUMMARY")
print("=" * 100)

sri_lanka_bounds = {"lat_min": 5.9, "lat_max": 9.9, "lon_min": 79.4, "lon_max": 81.9}

correct_country = 0
close_region = 0
for r in results:
    best = r["predictions"][0]
    if (sri_lanka_bounds["lat_min"] <= best["lat"] <= sri_lanka_bounds["lat_max"]
            and sri_lanka_bounds["lon_min"] <= best["lon"] <= sri_lanka_bounds["lon_max"]):
        correct_country += 1
        if abs(best["lat"] - 6.1) < 0.5 and abs(best["lon"] - 80.5) < 0.5:
            close_region += 1
    loc = r["best_location"].lower()
    if "sri lanka" in loc:
        correct_country += 0  # already counted by bounds

total = len(results)
print(f"  Total frames tested:       {total}")
print(f"  Predicted Sri Lanka:       {correct_country}/{total} ({correct_country/total*100:.0f}%)")
print(f"  Close to actual region:    {close_region}/{total} ({close_region/total*100:.0f}%)")

countries = {}
for r in results:
    loc = r["best_location"]
    country = loc.split(",")[-1].strip() if "," in loc else loc
    countries[country] = countries.get(country, 0) + 1

print(f"\n  Country distribution of predictions:")
for country, count in sorted(countries.items(), key=lambda x: -x[1]):
    bar = "█" * count
    print(f"    {country:30s}: {count:2d} {bar}")

out_path = Path(__file__).parent / "geoclip_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"\n  Results saved to: {out_path}")
