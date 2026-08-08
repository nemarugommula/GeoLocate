"""
Satellite matching — Yunnan drone frame vs Google Maps tiles around Shidian County
"""
import os, sys, cv2, numpy as np, json, urllib.request
from pathlib import Path
from math import cos, radians

API_KEY = "AIzaSyBq_xQLxOwn6MO2GGJ2ahoCltnOQ-lsoR8"
BASE_DIR = Path(__file__).parent
SAT_DIR = BASE_DIR / "yunnan-sat-tiles"
SAT_DIR.mkdir(exist_ok=True)

DRONE_FRAME = str(BASE_DIR / "yunnan-high-signal" / "06_geo+0.061_23m09s_aerial-drone-shot-looking.jpg")

# Known location: Shidian County, Baoshan, Yunnan
# Youwang town is within Shidian
CENTER_LAT = 24.7293
CENTER_LON = 99.1869
ZOOM = 16  # wider view since we're searching a larger area
TILE_SIZE = 640
GRID_RADIUS = 5  # 11x11 = 121 tiles, covers ~6km x 6km at zoom 16

# At zoom 16, each 640px tile covers ~600m
TILE_SPAN_M = 600
STEP_DEG_LAT = TILE_SPAN_M / 111320
STEP_DEG_LON = TILE_SPAN_M / (111320 * cos(radians(CENTER_LAT)))


def fetch_tile(lat, lon, zoom, size, filename):
    if os.path.exists(filename):
        return True
    url = (f"https://maps.googleapis.com/maps/api/staticmap?"
           f"center={lat},{lon}&zoom={zoom}&size={size}x{size}"
           f"&maptype=satellite&key={API_KEY}")
    try:
        urllib.request.urlretrieve(url, filename)
        return True
    except Exception as e:
        print(f"    Error: {e}")
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


drone = cv2.imread(DRONE_FRAME)
drone = cv2.resize(drone, (TILE_SIZE, TILE_SIZE))

print(f"Drone frame: 23:09 aerial shot")
print(f"Search center: Shidian County ({CENTER_LAT:.4f}°N, {CENTER_LON:.4f}°E)")
print(f"Grid: {2*GRID_RADIUS+1}x{2*GRID_RADIUS+1} = {(2*GRID_RADIUS+1)**2} tiles")
print(f"Zoom: {ZOOM}, Coverage: ~{(2*GRID_RADIUS+1)*TILE_SPAN_M/1000:.1f}km x {(2*GRID_RADIUS+1)*TILE_SPAN_M/1000:.1f}km")
print("=" * 80)

# Build tile grid
tiles = []
for r in range(-GRID_RADIUS, GRID_RADIUS + 1):
    for c in range(-GRID_RADIUS, GRID_RADIUS + 1):
        lat = CENTER_LAT + r * STEP_DEG_LAT
        lon = CENTER_LON + c * STEP_DEG_LON
        fname = str(SAT_DIR / f"tile_{r:+03d}_{c:+03d}.jpg")
        tiles.append({"lat": lat, "lon": lon, "r": r, "c": c, "path": fname})

print(f"\n  Fetching {len(tiles)} satellite tiles...")
for i, t in enumerate(tiles):
    fetch_tile(t["lat"], t["lon"], ZOOM, TILE_SIZE, t["path"])
    sys.stdout.write(f"\r    {i+1}/{len(tiles)}")
    sys.stdout.flush()
print(f"\r    {len(tiles)}/{len(tiles)} done")

print(f"\n  Matching drone frame against tiles...")
results = []
for i, t in enumerate(tiles):
    if not os.path.exists(t["path"]) or os.path.getsize(t["path"]) < 5000:
        continue
    sat = cv2.imread(t["path"])
    if sat is None:
        continue

    n_good, inliers = match_sift(drone, sat)
    t["matches"] = n_good
    t["inliers"] = inliers
    t["score"] = inliers * 2 + n_good
    results.append(t)

    if inliers > 3 or n_good > 8:
        print(f"    [{i+1:3d}] ({t['lat']:.4f}, {t['lon']:.4f}) matches={n_good:3d} inliers={inliers:3d} {'★' * min(inliers//2, 10)}")
    else:
        sys.stdout.write(f"\r    [{i+1:3d}/{len(tiles)}] scanning...")
        sys.stdout.flush()

print("\r" + " " * 80)

results.sort(key=lambda x: x["score"], reverse=True)

print(f"\n{'=' * 80}")
print("  TOP 10 MATCHING TILES")
print(f"{'=' * 80}")
for i, r in enumerate(results[:10]):
    star = "★" * min(r["inliers"] // 2, 5) if r["inliers"] > 0 else ""
    print(f"  {i+1:2d}. ({r['lat']:.5f}°N, {r['lon']:.5f}°E) "
          f"matches={r['matches']:3d}  inliers={r['inliers']:3d}  score={r['score']:4d}  {star}")

if results and results[0]["inliers"] > 5:
    best = results[0]
    print(f"\n  ★ POTENTIAL MATCH: {best['lat']:.5f}°N, {best['lon']:.5f}°E")
    print(f"  Google Maps: https://www.google.com/maps?q={best['lat']},{best['lon']}&z={ZOOM}&t=k")
else:
    print(f"\n  No strong match found in this grid.")
    print(f"  The village might be outside our {(2*GRID_RADIUS+1)*TILE_SPAN_M/1000:.0f}km search radius,")
    print(f"  or seasonal/resolution differences prevent matching.")

# Save the best satellite tile next to drone frame for visual comparison
if results:
    best = results[0]
    comparison_dir = BASE_DIR / "yunnan-comparison"
    comparison_dir.mkdir(exist_ok=True)
    import shutil
    shutil.copy2(DRONE_FRAME, str(comparison_dir / "drone_23m09s.jpg"))
    shutil.copy2(best["path"], str(comparison_dir / f"best_sat_{best['lat']:.4f}_{best['lon']:.4f}.jpg"))
    print(f"\n  Comparison saved to: {comparison_dir}/")
