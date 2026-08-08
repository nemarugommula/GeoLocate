"""
Satellite matching using FREE ESRI World Imagery tiles (no API key needed).
Compare against Google Maps results to validate free alternative.
"""
import os, sys, cv2, numpy as np, json, urllib.request, math
from pathlib import Path

BASE_DIR = Path(__file__).parent
SAT_DIR = BASE_DIR / "esri-sat-tiles"
COMPARE_DIR = BASE_DIR / "free-vs-google-comparison"
SAT_DIR.mkdir(exist_ok=True)
COMPARE_DIR.mkdir(exist_ok=True)

DRONE_FRAME = str(BASE_DIR / "yunnan-high-signal" / "06_geo+0.061_23m09s_aerial-drone-shot-looking.jpg")

CENTER_LAT = 24.7293
CENTER_LON = 99.1869
ZOOM = 16
GRID_RADIUS = 5  # 11x11 grid


def lat_lon_to_tile(lat, lon, zoom):
    """Convert lat/lon to tile x,y at given zoom."""
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def tile_to_lat_lon(x, y, zoom):
    """Convert tile x,y to lat/lon (top-left corner)."""
    n = 2 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon


def tile_center_lat_lon(x, y, zoom):
    """Get center lat/lon of a tile."""
    lat1, lon1 = tile_to_lat_lon(x, y, zoom)
    lat2, lon2 = tile_to_lat_lon(x + 1, y + 1, zoom)
    return (lat1 + lat2) / 2, (lon1 + lon2) / 2


def fetch_esri_tile(z, y, x, filename):
    """Fetch satellite tile from ESRI World Imagery (FREE, no API key)."""
    if os.path.exists(filename) and os.path.getsize(filename) > 1000:
        return True
    url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GeoLens-Phase0-Test/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            with open(filename, "wb") as f:
                f.write(resp.read())
        return True
    except Exception as e:
        return False


def match_sift(img1, img2):
    sift = cv2.SIFT_create(nfeatures=3000)
    g1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    kp1, d1 = sift.detectAndCompute(g1, None)
    kp2, d2 = sift.detectAndCompute(g2, None)
    if d1 is None or d2 is None or len(d1) < 10 or len(d2) < 10:
        return 0, 0
    matches = cv2.BFMatcher(cv2.NORM_L2).knnMatch(d1, d2, k=2)
    good = [m for m, n in matches if len([m, n]) == 2 and m.distance < 0.75 * n.distance]
    if len(good) < 8:
        return len(good), 0
    src = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    _, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    inliers = int(mask.sum()) if mask is not None else 0
    return len(good), inliers


# ─── MAIN ───

drone = cv2.imread(DRONE_FRAME)
if drone is None:
    print("Error: drone frame not found")
    sys.exit(1)

center_tx, center_ty = lat_lon_to_tile(CENTER_LAT, CENTER_LON, ZOOM)

print(f"{'=' * 80}")
print(f"  FREE Satellite Matching (ESRI World Imagery — no API key)")
print(f"{'=' * 80}")
print(f"  Drone frame: 23:09 aerial shot")
print(f"  Search center: Shidian County ({CENTER_LAT:.4f}°N, {CENTER_LON:.4f}°E)")
print(f"  Center tile: z={ZOOM}, x={center_tx}, y={center_ty}")
print(f"  Grid: {2*GRID_RADIUS+1}x{2*GRID_RADIUS+1} = {(2*GRID_RADIUS+1)**2} tiles")
print(f"  Cost: $0.00 (ESRI is free, no API key)")

# Build tile grid
tiles = []
for dy in range(-GRID_RADIUS, GRID_RADIUS + 1):
    for dx in range(-GRID_RADIUS, GRID_RADIUS + 1):
        tx = center_tx + dx
        ty = center_ty + dy
        lat, lon = tile_center_lat_lon(tx, ty, ZOOM)
        fname = str(SAT_DIR / f"esri_z{ZOOM}_x{tx}_y{ty}.jpg")
        tiles.append({"tx": tx, "ty": ty, "lat": lat, "lon": lon, "path": fname})

# Fetch tiles
print(f"\n  Fetching {len(tiles)} ESRI tiles...")
fetched = 0
for i, t in enumerate(tiles):
    if fetch_esri_tile(ZOOM, t["ty"], t["tx"], t["path"]):
        fetched += 1
    sys.stdout.write(f"\r    {i+1}/{len(tiles)} ({fetched} fetched)")
    sys.stdout.flush()
print(f"\r    {fetched}/{len(tiles)} tiles fetched successfully")

# Resize drone frame to match ESRI tile size (256x256)
drone_256 = cv2.resize(drone, (256, 256))

# Match
print(f"\n  Matching drone frame against ESRI tiles...")
results = []
for i, t in enumerate(tiles):
    if not os.path.exists(t["path"]) or os.path.getsize(t["path"]) < 1000:
        continue
    sat = cv2.imread(t["path"])
    if sat is None:
        continue

    n_good, inliers = match_sift(drone_256, sat)
    t["matches"] = n_good
    t["inliers"] = inliers
    t["score"] = inliers * 2 + n_good
    results.append(t)

    if inliers > 3 or n_good > 8:
        print(f"    [{i+1:3d}] ({t['lat']:.4f}, {t['lon']:.4f}) "
              f"matches={n_good:3d} inliers={inliers:3d} {'★' * min(inliers//2, 10)}")
    else:
        sys.stdout.write(f"\r    [{i+1:3d}/{len(tiles)}] scanning...")
        sys.stdout.flush()

print("\r" + " " * 80)

results.sort(key=lambda x: x["score"], reverse=True)

print(f"\n{'=' * 80}")
print("  ESRI TOP 10 MATCHES")
print(f"{'=' * 80}")
for i, r in enumerate(results[:10]):
    star = "★" * min(r["inliers"] // 2, 5)
    print(f"  {i+1:2d}. ({r['lat']:.5f}°N, {r['lon']:.5f}°E) "
          f"matches={r['matches']:3d}  inliers={r['inliers']:3d}  score={r['score']:4d}  {star}")

# Compare with Google results
print(f"\n{'=' * 80}")
print("  COMPARISON: ESRI (Free) vs Google Maps ($2/1000 req)")
print(f"{'=' * 80}")

google_best = {"lat": 24.72930, "lon": 99.19283, "matches": 30, "inliers": 15, "score": 60}
esri_best = results[0] if results else {"lat": 0, "lon": 0, "matches": 0, "inliers": 0, "score": 0}

print(f"  {'':30s} {'Google':>12s}  {'ESRI (Free)':>12s}")
print(f"  {'─' * 60}")
print(f"  {'Best match lat':30s} {google_best['lat']:>12.5f}  {esri_best['lat']:>12.5f}")
print(f"  {'Best match lon':30s} {google_best['lon']:>12.5f}  {esri_best['lon']:>12.5f}")
print(f"  {'SIFT matches':30s} {google_best['matches']:>12d}  {esri_best['matches']:>12d}")
print(f"  {'RANSAC inliers':30s} {google_best['inliers']:>12d}  {esri_best['inliers']:>12d}")
print(f"  {'Score':30s} {google_best['score']:>12d}  {esri_best['score']:>12d}")
print(f"  {'Cost per 121 tiles':30s} {'$0.24':>12s}  {'$0.00':>12s}")

if esri_best["score"] > 0:
    ratio = esri_best["score"] / max(google_best["score"], 1) * 100
    print(f"\n  ESRI achieves {ratio:.0f}% of Google's match score at $0 cost.")

# Save best ESRI tile for visual comparison
if results:
    import shutil
    best = results[0]
    shutil.copy2(DRONE_FRAME, str(COMPARE_DIR / "drone_23m09s.jpg"))
    shutil.copy2(best["path"], str(COMPARE_DIR / f"esri_best_{best['lat']:.4f}_{best['lon']:.4f}.jpg"))

    # Also save the Google tile if available
    google_tile = BASE_DIR / "yunnan-sat-tiles" / "tile_+00_+01.jpg"
    if google_tile.exists():
        shutil.copy2(str(google_tile), str(COMPARE_DIR / "google_best.jpg"))

    print(f"\n  Comparison saved to: {COMPARE_DIR}/")
    if results[0]["score"] > 20:
        print(f"  Best ESRI match: https://www.google.com/maps?q={best['lat']},{best['lon']}&z={ZOOM}&t=k")

print(f"\n  Verdict: {'ESRI is a viable free alternative' if esri_best['score'] >= google_best['score'] * 0.5 else 'ESRI quality is significantly lower'}")
