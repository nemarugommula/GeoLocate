"""
Satellite Image Matching — fetch Google Maps satellite tiles and match
against drone frames using SIFT feature matching.
"""
import os
import sys
import cv2
import numpy as np
import json
import urllib.request
from pathlib import Path
from math import cos, radians

API_KEY = "AIzaSyBq_xQLxOwn6MO2GGJ2ahoCltnOQ-lsoR8"
BASE_DIR = Path(__file__).parent
SAT_DIR = BASE_DIR / "satellite-tiles"
MATCH_DIR = BASE_DIR / "satellite-matches"
SAT_DIR.mkdir(exist_ok=True)
MATCH_DIR.mkdir(exist_ok=True)

DRONE_FRAME = str(BASE_DIR / "clip-high-signal" / "01_geo+0.058_01m42s_aerial-drone-shot-looking.jpg")

# Our best estimate from triangulation
CENTER_LAT = 6.1012
CENTER_LON = 80.4765

ZOOM = 18  # ~0.5m/pixel at equator
TILE_SIZE = 640  # max for Google Static Maps
GRID_RADIUS = 3  # 7x7 grid = 49 tiles

# At zoom 18, each 640px tile covers roughly:
# ~150m at equator, slightly more at lat 6°
TILE_SPAN_M = 150
STEP_DEG_LAT = TILE_SPAN_M / 111320  # ~0.00135°
STEP_DEG_LON = TILE_SPAN_M / (111320 * cos(radians(CENTER_LAT)))  # adjusted for latitude


def fetch_satellite_tile(lat, lon, zoom, size, filename):
    """Fetch a satellite tile from Google Maps Static API."""
    if os.path.exists(filename):
        return True

    url = (
        f"https://maps.googleapis.com/maps/api/staticmap?"
        f"center={lat},{lon}&zoom={zoom}&size={size}x{size}"
        f"&maptype=satellite&key={API_KEY}"
    )

    try:
        urllib.request.urlretrieve(url, filename)
        return True
    except Exception as e:
        print(f"    Error fetching tile: {e}")
        return False


def match_features(img1, img2):
    """Match features between two images using SIFT."""
    sift = cv2.SIFT_create(nfeatures=2000)

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)

    if des1 is None or des2 is None or len(des1) < 5 or len(des2) < 5:
        return 0, 0, []

    bf = cv2.BFMatcher(cv2.NORM_L2)
    matches = bf.knnMatch(des1, des2, k=2)

    good_matches = []
    for m_pair in matches:
        if len(m_pair) == 2:
            m, n = m_pair
            if m.distance < 0.7 * n.distance:
                good_matches.append(m)

    match_ratio = len(good_matches) / max(len(kp1), 1)
    return len(good_matches), match_ratio, good_matches


def match_with_homography(img1, img2):
    """Try to find a geometric transformation (homography) between images."""
    sift = cv2.SIFT_create(nfeatures=3000)

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)

    if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
        return None, 0, 0

    bf = cv2.BFMatcher(cv2.NORM_L2)
    matches = bf.knnMatch(des1, des2, k=2)

    good = []
    for m_pair in matches:
        if len(m_pair) == 2:
            m, n = m_pair
            if m.distance < 0.75 * n.distance:
                good.append(m)

    if len(good) < 10:
        return None, len(good), 0

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
    inliers = int(mask.sum()) if mask is not None else 0

    return M, len(good), inliers


# ─── MAIN ───

print(f"Drone frame: {DRONE_FRAME}")
print(f"Center: {CENTER_LAT:.4f}°N, {CENTER_LON:.4f}°E (Akuressa area)")
print(f"Grid: {2*GRID_RADIUS+1}x{2*GRID_RADIUS+1} = {(2*GRID_RADIUS+1)**2} tiles")
print(f"Zoom: {ZOOM}, Tile size: {TILE_SIZE}px")
print(f"Coverage: ~{(2*GRID_RADIUS+1) * TILE_SPAN_M}m x {(2*GRID_RADIUS+1) * TILE_SPAN_M}m")
print("=" * 80)

drone_img = cv2.imread(DRONE_FRAME)
if drone_img is None:
    print("Error: couldn't load drone frame")
    sys.exit(1)

drone_resized = cv2.resize(drone_img, (TILE_SIZE, TILE_SIZE))

# Step 1: Fetch satellite tiles
print("\n  Step 1: Fetching satellite tiles...")
tiles = []
for row in range(-GRID_RADIUS, GRID_RADIUS + 1):
    for col in range(-GRID_RADIUS, GRID_RADIUS + 1):
        lat = CENTER_LAT + row * STEP_DEG_LAT
        lon = CENTER_LON + col * STEP_DEG_LON
        filename = str(SAT_DIR / f"tile_r{row:+d}_c{col:+d}_{lat:.5f}_{lon:.5f}.jpg")
        tiles.append({"lat": lat, "lon": lon, "row": row, "col": col, "path": filename})

print(f"    Fetching {len(tiles)} tiles...")
fetched = 0
for t in tiles:
    if fetch_satellite_tile(t["lat"], t["lon"], ZOOM, TILE_SIZE, t["path"]):
        fetched += 1
    sys.stdout.write(f"\r    Fetched {fetched}/{len(tiles)}")
    sys.stdout.flush()
print(f"\r    Fetched {fetched}/{len(tiles)} tiles")

# Step 2: Match drone frame against each tile
print("\n  Step 2: Matching drone frame against satellite tiles...")
results = []

for i, t in enumerate(tiles):
    if not os.path.exists(t["path"]):
        continue

    sat_img = cv2.imread(t["path"])
    if sat_img is None:
        continue

    fsize = os.path.getsize(t["path"])
    if fsize < 5000:
        continue

    n_good, ratio, _ = match_features(drone_resized, sat_img)
    _, total_good, inliers = match_with_homography(drone_resized, sat_img)

    t["n_matches"] = n_good
    t["match_ratio"] = round(ratio, 4)
    t["homography_matches"] = total_good
    t["inliers"] = inliers
    t["score"] = inliers * 2 + n_good

    results.append(t)

    if n_good > 5 or inliers > 3:
        print(f"    [{i+1:3d}/{len(tiles)}] ({t['lat']:.4f}, {t['lon']:.4f}) "
              f"matches={n_good:3d} inliers={inliers:3d} {'★' * min(inliers // 3, 10)}")
    else:
        sys.stdout.write(f"\r    [{i+1:3d}/{len(tiles)}] scanning...")
        sys.stdout.flush()

print("\r" + " " * 80)

# Step 3: Results
results.sort(key=lambda x: x["score"], reverse=True)

print(f"\n{'=' * 80}")
print("  TOP 10 MATCHING TILES")
print(f"{'=' * 80}")

for i, r in enumerate(results[:10]):
    print(f"  {i+1:2d}. ({r['lat']:.5f}°N, {r['lon']:.5f}°E)  "
          f"matches={r['n_matches']:3d}  inliers={r['inliers']:3d}  "
          f"score={r['score']:4d}")

if results and results[0]["score"] > 20:
    best = results[0]
    print(f"\n  BEST MATCH: {best['lat']:.5f}°N, {best['lon']:.5f}°E")
    print(f"  Accuracy:   ~{TILE_SPAN_M}m (within one tile)")
    print(f"  Google Maps: https://www.google.com/maps?q={best['lat']},{best['lon']}&z=18&t=k")
else:
    print(f"\n  No strong match found in this area.")
    print(f"  This could mean:")
    print(f"    - The actual location is outside our search grid")
    print(f"    - Seasonal/temporal differences between drone and satellite")
    print(f"    - Scale/rotation mismatch")
    print(f"    - The area looks different from above vs satellite")

avg_matches = np.mean([r["n_matches"] for r in results]) if results else 0
avg_inliers = np.mean([r["inliers"] for r in results]) if results else 0
print(f"\n  Average matches per tile: {avg_matches:.1f}")
print(f"  Average inliers per tile: {avg_inliers:.1f}")

out_json = BASE_DIR / "satellite_match_results.json"
serializable = [{k: v for k, v in r.items() if k != "path"} for r in results[:20]]
with open(out_json, "w") as f:
    json.dump(serializable, f, indent=2)
print(f"  Results: {out_json}")
