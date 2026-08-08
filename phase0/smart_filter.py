import os
import sys
import subprocess
import cv2
import numpy as np
import json
import shutil
from pathlib import Path

VIDEO_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/Downloads/Santol Fruit Pickle Welithalapa Egg Hoppers and Fiery Sauce from My Sri Lankan Village Kitchen.mp4"
)
FRAME_INTERVAL = 2
BASE_DIR = Path(__file__).parent
RAW_FRAMES_DIR = BASE_DIR / "filter-raw-frames"
HIGH_SIGNAL_DIR = BASE_DIR / "high-signal-frames"
RAW_FRAMES_DIR.mkdir(exist_ok=True)
HIGH_SIGNAL_DIR.mkdir(exist_ok=True)

for f in HIGH_SIGNAL_DIR.glob("*.jpg"):
    f.unlink()


def get_duration(video_path):
    result = subprocess.run(["ffmpeg", "-i", video_path], capture_output=True, text=True)
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            t = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = t.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0


def extract_frame(video_path, timestamp, output_path):
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(timestamp), "-i", video_path,
         "-frames:v", "1", "-q:v", "2", output_path],
        capture_output=True
    )


# ─── DETECTOR 1: Perceptual Hash (dedup) ───

def dhash(img, hash_size=16):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (hash_size + 1, hash_size))
    diff = resized[:, 1:] > resized[:, :-1]
    return sum(2 ** i for i, v in enumerate(diff.flatten()) if v)


def hamming_distance(h1, h2):
    return bin(h1 ^ h2).count("1")


# ─── DETECTOR 2: Blur Detection ───

def blur_score(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


# ─── DETECTOR 3: Face Detection (skin-color heuristic, no model needed) ───

def detect_faces(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]

    skin1 = cv2.inRange(hsv, np.array([0, 40, 80]), np.array([20, 150, 255]))
    skin2 = cv2.inRange(hsv, np.array([160, 40, 80]), np.array([180, 150, 255]))
    skin_mask = cv2.bitwise_or(skin1, skin2)

    center = skin_mask[h // 4:3 * h // 4, w // 4:3 * w // 4]
    center_skin = cv2.countNonZero(center) / (center.shape[0] * center.shape[1])
    total_skin = cv2.countNonZero(skin_mask) / (h * w)

    is_face_dominant = center_skin > 0.3 and total_skin > 0.15
    face_count = 1 if is_face_dominant else 0
    face_ratio = total_skin if is_face_dominant else 0.0

    return face_count, face_ratio


# ─── DETECTOR 4: Sky / Horizon Detection ───

def detect_sky(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]
    top_third = hsv[:h // 3, :, :]

    blue_sky = cv2.inRange(top_third, (90, 30, 120), (135, 255, 255))
    white_sky = cv2.inRange(top_third, (0, 0, 180), (180, 40, 255))
    sky_mask = cv2.bitwise_or(blue_sky, white_sky)

    sky_ratio = cv2.countNonZero(sky_mask) / (h // 3 * w)
    return sky_ratio


def detect_horizon(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape[:2]
    middle_band = gray[h // 4: 3 * h // 4, :]
    edges = cv2.Canny(middle_band, 30, 100)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100,
                            minLineLength=w // 2, maxLineGap=15)
    if lines is None:
        return False, 0

    horizontal_lines = 0
    for line in lines:
        pts = line.flatten()
        if len(pts) < 4:
            continue
        x1, y1, x2, y2 = pts[0], pts[1], pts[2], pts[3]
        angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        if (angle < 10 or angle > 170) and length > w // 4:
            horizontal_lines += 1

    return horizontal_lines >= 3, horizontal_lines


# ─── DETECTOR 5: Aerial / Drone Shot (4-signal structural analysis) ───

def _grid_sharpness(gray, rows=4, cols=4):
    """Compute Laplacian variance (sharpness) per grid cell."""
    h, w = gray.shape
    ch, cw = h // rows, w // cols
    vals = []
    for r in range(rows):
        for c in range(cols):
            cell = gray[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]
            vals.append(cv2.Laplacian(cell, cv2.CV_64F).var())
    return vals


def _grid_edge_density(gray, rows=4, cols=4):
    """Compute edge pixel ratio per grid cell."""
    edges = cv2.Canny(gray, 50, 150)
    h, w = gray.shape
    ch, cw = h // rows, w // cols
    vals = []
    for r in range(rows):
        for c in range(cols):
            cell = edges[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]
            vals.append(cv2.countNonZero(cell) / (ch * cw))
    return vals


def _grid_color_variance(img, rows=4, cols=4):
    """Compute mean hue per grid cell — uniform color = low std."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]
    ch, cw = h // rows, w // cols
    vals = []
    for r in range(rows):
        for c in range(cols):
            cell = hsv[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]
            vals.append(cell[:, :, 0].mean())
    return vals


def _saliency_concentration(img):
    """Check if a dominant foreground object exists (high saliency in one area)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    blurred = cv2.GaussianBlur(gray, (0, 0), max(h, w) / 6)
    saliency = cv2.absdiff(gray, blurred).astype(np.float32)

    ch, cw = h // 4, w // 4
    cell_sums = []
    for r in range(4):
        for c in range(4):
            cell = saliency[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]
            cell_sums.append(cell.sum())

    total = sum(cell_sums)
    if total == 0:
        return 0.0
    max_cell_ratio = max(cell_sums) / total
    return max_cell_ratio


def _coeff_of_variation(vals):
    """std / mean — low = uniform, high = varied."""
    arr = np.array(vals, dtype=np.float64)
    m = arr.mean()
    if m < 1e-6:
        return 0.0
    return arr.std() / m


def detect_aerial(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]

    green_mask = cv2.inRange(hsv, (25, 30, 30), (95, 255, 255))
    green_ratio = cv2.countNonZero(green_mask) / (h * w)

    # Signal 1: Focus uniformity (low CV = everything in focus = aerial)
    sharpness_vals = _grid_sharpness(gray)
    focus_cv = _coeff_of_variation(sharpness_vals)
    focus_uniform = focus_cv < 0.6

    # Signal 2: Texture uniformity (low CV = similar patches = aerial)
    edge_vals = _grid_edge_density(gray)
    texture_cv = _coeff_of_variation(edge_vals)
    texture_uniform = texture_cv < 0.5

    # Signal 3: Edge distribution (high entropy = spread out = aerial)
    edge_arr = np.array(edge_vals, dtype=np.float64)
    edge_sum = edge_arr.sum()
    if edge_sum > 0:
        edge_probs = edge_arr / edge_sum
        edge_probs = edge_probs[edge_probs > 0]
        edge_entropy = -np.sum(edge_probs * np.log2(edge_probs))
        max_entropy = np.log2(len(edge_vals))
        normalized_entropy = edge_entropy / max_entropy if max_entropy > 0 else 0
    else:
        normalized_entropy = 0.0
    edges_spread = normalized_entropy > 0.85

    # Signal 4: No dominant foreground object
    saliency_conc = _saliency_concentration(img)
    no_dominant_object = saliency_conc < 0.15

    # Aerial = uniform HIGH sharpness (everything far away and in focus)
    # Bokeh/garden = uniform LOW sharpness (blurred background)
    avg_sharpness = np.mean(sharpness_vals)
    sharp_enough = avg_sharpness > 200  # real aerial has lots of detail

    # Need sky in top portion OR pure top-down (no sky at all but very high green)
    sky_ratio = detect_sky(img)
    has_perspective = sky_ratio > 0.1 or green_ratio > 0.6

    structural_score = sum([focus_uniform, texture_uniform, edges_spread, no_dominant_object])
    is_aerial = (green_ratio > 0.35
                 and structural_score == 4
                 and sharp_enough
                 and has_perspective)

    props = {
        "green": round(green_ratio, 3),
        "focus_cv": round(focus_cv, 3),
        "focus_uniform": focus_uniform,
        "texture_cv": round(texture_cv, 3),
        "texture_uniform": texture_uniform,
        "edge_entropy": round(normalized_entropy, 3),
        "edges_spread": edges_spread,
        "saliency_conc": round(saliency_conc, 3),
        "no_dominant_obj": no_dominant_object,
        "structural_score": f"{structural_score}/4",
    }

    return is_aerial, props


# ─── DETECTOR 6: Text Region Detection (CRAFT via EasyOCR) ───

try:
    import easyocr
    print("Loading EasyOCR text detector...")
    ocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    HAS_OCR = True
    print("Text detector loaded.")
except Exception:
    HAS_OCR = False
    print("EasyOCR not available, skipping text detection.")


def detect_text_regions(img_path):
    if not HAS_OCR:
        return []
    results = ocr_reader.readtext(img_path, paragraph=False)
    detections = []
    for (bbox, text, conf) in results:
        text = text.strip()
        if len(text) < 2:
            continue
        has_non_latin = any(ord(ch) > 127 and not ch.isspace() for ch in text)
        detections.append({
            "text": text,
            "conf": round(conf, 3),
            "non_latin": has_non_latin
        })
    return detections


# ─── DETECTOR 7: Structure / Architecture Detection ───

def detect_structures(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape[:2]
    edges = cv2.Canny(gray, 50, 150)

    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50,
                            minLineLength=30, maxLineGap=10)
    if lines is None:
        return False, 0, 0

    vertical = 0
    horizontal = 0
    for line in lines:
        pts = line.flatten()
        if len(pts) < 4:
            continue
        x1, y1, x2, y2 = pts[0], pts[1], pts[2], pts[3]
        angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        if angle > 75 and angle < 105:
            vertical += 1
        elif angle < 15 or angle > 165:
            horizontal += 1

    structured = (vertical > 15 and horizontal > 15) or (vertical + horizontal > 50)
    return structured, vertical, horizontal


# ─── DETECTOR 8: Food Close-up / Skin Detection ───

def detect_food_closeup(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]

    skin_lower1 = np.array([0, 30, 60])
    skin_upper1 = np.array([20, 150, 255])
    skin_lower2 = np.array([160, 30, 60])
    skin_upper2 = np.array([180, 150, 255])
    skin_mask1 = cv2.inRange(hsv, skin_lower1, skin_upper1)
    skin_mask2 = cv2.inRange(hsv, skin_lower2, skin_upper2)
    skin_mask = cv2.bitwise_or(skin_mask1, skin_mask2)
    skin_ratio = cv2.countNonZero(skin_mask) / (h * w)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = cv2.countNonZero(edges) / (h * w)

    center_region = img[h // 4:3 * h // 4, w // 4:3 * w // 4]
    center_hsv = cv2.cvtColor(center_region, cv2.COLOR_BGR2HSV)
    center_sat = center_hsv[:, :, 1].mean()

    is_food = (
        skin_ratio > 0.15
        and edge_ratio > 0.05
        and center_sat > 60
    )

    return is_food, round(skin_ratio, 3)


# ─── DETECTOR 9: Color Analysis (vegetation, water, desert) ───

def color_analysis(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, w = img.shape[:2]
    total = h * w

    green = cv2.countNonZero(cv2.inRange(hsv, (25, 30, 30), (95, 255, 255))) / total
    blue_water = cv2.countNonZero(cv2.inRange(hsv, (90, 40, 40), (135, 255, 255))) / total
    brown_earth = cv2.countNonZero(cv2.inRange(hsv, (5, 30, 30), (25, 200, 200))) / total
    white_snow = cv2.countNonZero(cv2.inRange(hsv, (0, 0, 200), (180, 30, 255))) / total

    brightness = hsv[:, :, 2].mean()
    saturation = hsv[:, :, 1].mean()

    return {
        "green": round(green, 3),
        "water_blue": round(blue_water, 3),
        "earth_brown": round(brown_earth, 3),
        "snow_white": round(white_snow, 3),
        "brightness": round(brightness, 1),
        "saturation": round(saturation, 1),
    }


# ─── SCORING ENGINE ───

def score_frame(analysis):
    score = 0
    tags = []
    reasons = []

    if analysis["is_aerial"]:
        score += 40
        tags.append("AERIAL")
        ap = analysis["aerial_props"]
        reasons.append(f"Aerial/drone shot ({ap['structural_score']} checks passed: "
                       f"focus_cv={ap['focus_cv']}, texture_cv={ap['texture_cv']}, "
                       f"entropy={ap['edge_entropy']}, saliency={ap['saliency_conc']})")

    if analysis["has_horizon"] and analysis["sky_ratio"] > 0.1:
        score += 25
        tags.append("HORIZON")
        reasons.append(f"Landscape with horizon + sky ({analysis['horizon_count']} lines, sky: {analysis['sky_ratio']:.0%})")
    elif analysis["has_horizon"]:
        score += 10
        tags.append("HORIZON")
        reasons.append(f"Horizon line detected ({analysis['horizon_count']} lines)")

    if analysis["sky_ratio"] > 0.25:
        score += 5
        tags.append("SKY")

    non_latin_text = [d for d in analysis["text_detections"] if d.get("non_latin")]
    latin_text = [d for d in analysis["text_detections"] if not d.get("non_latin") and d["conf"] > 0.3]

    if non_latin_text:
        score += 50
        tags.append("NON-LATIN-TEXT")
        texts = [d["text"] for d in non_latin_text]
        reasons.append(f"Non-Latin script detected: {', '.join(texts[:3])}")

    if latin_text:
        score += 15
        tags.append("TEXT")
        texts = [d["text"] for d in latin_text[:3]]
        reasons.append(f"Readable text: {', '.join(texts)}")

    if (analysis["has_structures"]
            and not analysis["is_food_closeup"]
            and analysis["colors"]["green"] < 0.3
            and analysis["vert_lines"] > 10):
        score += 20
        tags.append("STRUCTURE")
        reasons.append(f"Architecture/structures (V:{analysis['vert_lines']} H:{analysis['horiz_lines']})")

    colors = analysis["colors"]
    if colors["water_blue"] > 0.15:
        score += 15
        tags.append("WATER")
        reasons.append(f"Water body visible ({colors['water_blue']:.0%})")

    if analysis["is_food_closeup"]:
        score -= 20
        tags.append("FOOD-CLOSEUP")
        reasons.append("Food/cooking close-up (low geo value)")

    if analysis["face_ratio"] > 0.1:
        score -= 25
        tags.append("TALKING-HEAD")
        reasons.append(f"Face dominant ({analysis['face_ratio']:.0%} of frame)")

    if analysis["blur"] < 50:
        score -= 15
        tags.append("BLURRY")
        reasons.append(f"Blurry frame (score: {analysis['blur']:.0f})")

    if analysis["brightness"] < 50:
        score -= 15
        tags.append("DARK")
        reasons.append(f"Too dark (brightness: {analysis['brightness']:.0f})")

    return max(score, 0), tags, reasons


# ═══════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════

print(f"\nVideo: {os.path.basename(VIDEO_PATH)}")
duration = get_duration(VIDEO_PATH)
total_frames = int(duration / FRAME_INTERVAL)
print(f"Duration: {duration:.0f}s ({duration / 60:.1f} min)")
print(f"Total frames to scan: {total_frames}")
print("=" * 90)

all_results = []
hashes_seen = {}
dup_count = 0

for i in range(total_frames):
    ts = i * FRAME_INTERVAL
    mins, secs = divmod(ts, 60)
    time_str = f"{int(mins):02d}:{int(secs):02d}"
    frame_path = str(RAW_FRAMES_DIR / f"frame_{ts:04d}.jpg")

    extract_frame(VIDEO_PATH, ts, frame_path)
    if not os.path.exists(frame_path):
        continue

    img = cv2.imread(frame_path)
    if img is None:
        continue

    frame_hash = dhash(img)
    is_dup = False
    for prev_ts, prev_hash in hashes_seen.items():
        if hamming_distance(frame_hash, prev_hash) < 20:
            is_dup = True
            dup_count += 1
            break

    if is_dup:
        sys.stdout.write(f"\r  Scanning... {time_str} (dup, skipped)")
        sys.stdout.flush()
        continue

    hashes_seen[ts] = frame_hash

    face_count, face_ratio = detect_faces(img)
    sky_ratio = detect_sky(img)
    has_horizon, horizon_count = detect_horizon(img)
    is_aerial, aerial_props = detect_aerial(img)
    has_structures, vert_lines, horiz_lines = detect_structures(img)
    is_food, skin_ratio = detect_food_closeup(img)
    colors = color_analysis(img)
    blur = blur_score(img)
    text_dets = detect_text_regions(frame_path)

    analysis = {
        "timestamp": ts,
        "time": time_str,
        "frame_path": frame_path,
        "face_count": face_count,
        "face_ratio": face_ratio,
        "sky_ratio": sky_ratio,
        "has_horizon": has_horizon,
        "horizon_count": horizon_count,
        "is_aerial": is_aerial,
        "aerial_props": aerial_props,
        "has_structures": has_structures,
        "vert_lines": vert_lines,
        "horiz_lines": horiz_lines,
        "is_food_closeup": is_food,
        "skin_ratio": skin_ratio,
        "colors": colors,
        "blur": blur,
        "brightness": colors["brightness"],
        "text_detections": text_dets,
    }

    score, tags, reasons = score_frame(analysis)
    analysis["score"] = score
    analysis["tags"] = tags
    analysis["reasons"] = reasons

    all_results.append(analysis)

    if score >= 20:
        stars = "★★★" if score >= 50 else "★★" if score >= 30 else "★"
        tag_str = " ".join(f"[{t}]" for t in tags if t not in ("VEGETATION",))
        print(f"\r  [{time_str}] score={score:3d} {stars}  {tag_str:40s} {'; '.join(reasons)}")
    else:
        sys.stdout.write(f"\r  Scanning... {time_str}")
        sys.stdout.flush()

print(f"\r" + " " * 90)

# ═══ Sort and output ═══

all_results.sort(key=lambda x: x["score"], reverse=True)
high_signal = [r for r in all_results if r["score"] >= 25]

print("\n" + "=" * 90)
print("  RESULTS SUMMARY")
print("=" * 90)
print(f"  Total frames extracted:  {total_frames}")
print(f"  Duplicates removed:      {dup_count}")
print(f"  Unique frames analyzed:  {len(all_results)}")
print(f"  High-signal frames:      {len(high_signal)}")
print(f"  Filter ratio:            {len(all_results)} → {len(high_signal)} ({len(high_signal)/max(len(all_results),1)*100:.0f}% kept)")
print(f"  Cost savings:            ~{(1 - len(high_signal)/max(len(all_results),1))*100:.0f}% fewer frames sent to LLM")

# Tag distribution
print(f"\n{'=' * 90}")
print("  HIGH-SIGNAL TAG DISTRIBUTION")
print("=" * 90)
tag_counts = {}
for r in high_signal:
    for t in r["tags"]:
        tag_counts[t] = tag_counts.get(t, 0) + 1
for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
    bar = "█" * min(count, 40)
    print(f"  {tag:20s}: {count:3d} {bar}")

# Copy high-signal frames to output directory with descriptive names
print(f"\n{'=' * 90}")
print("  HIGH-SIGNAL FRAMES (saved for review)")
print("=" * 90)

for idx, r in enumerate(high_signal):
    tag_slug = "_".join(t.lower() for t in r["tags"] if t not in ("VEGETATION",))[:40]
    out_name = f"{idx + 1:02d}_score{r['score']:03d}_{r['time'].replace(':', 'm')}s_{tag_slug}.jpg"
    src = r["frame_path"]
    dst = str(HIGH_SIGNAL_DIR / out_name)
    shutil.copy2(src, dst)
    r["output_path"] = dst

    print(f"  {idx + 1:2d}. [{r['time']}] score={r['score']:3d}  {' '.join(f'[{t}]' for t in r['tags'])}")
    for reason in r["reasons"]:
        print(f"       → {reason}")

print(f"\n  Frames saved to: {HIGH_SIGNAL_DIR}/")
print(f"  Open in Finder:  open \"{HIGH_SIGNAL_DIR}\"")

# Save JSON
output_json = BASE_DIR / "filter_results.json"
serializable = []
for r in all_results[:100]:
    sr = {k: v for k, v in r.items() if k != "frame_path"}
    serializable.append(sr)
with open(output_json, "w") as f:
    json.dump(serializable, f, indent=2, default=str)
print(f"  Full results:    {output_json}")
