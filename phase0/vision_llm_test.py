import subprocess
import json
import time
from pathlib import Path

FRAMES_DIR = Path(__file__).parent / "clip-high-signal"
MODEL = "minicpm-v"

GEO_PROMPT = """You are a geolocation expert. Analyze this image and determine where it was taken.

Examine carefully:
1. Terrain and topography (mountains, valleys, coastline, elevation)
2. Vegetation type (tropical, temperate, arid, what specific plants/trees)
3. Architecture style (if any buildings visible)
4. Road type, markings, driving side
5. Any visible text, signage, or script (what language/script?)
6. Cultural markers (clothing, artifacts, farming style)
7. Sky, weather, sun position
8. Soil color and type
9. Water bodies
10. Any other geographic clues

Based on ALL clues, provide:
- Most likely country (with confidence: high/medium/low)
- Most likely region/province
- Estimated coordinates if possible
- Your reasoning for each clue you identified
- What clues were most decisive

Be specific and honest about uncertainty. If you can't determine the location, say what you CAN determine (continent, climate zone, etc.)."""

FRAMES_TO_TEST = [
    "03_geo+0.051_00m00s_panoramic-landscape-with-.jpg",   # Best landscape
    "01_geo+0.058_01m42s_aerial-drone-shot-looking.jpg",   # Best aerial
    "07_geo+0.027_07m27s_village.jpg",                      # Village scene
    "04_geo+0.050_22m45s_panoramic-landscape-with-.jpg",   # Second landscape
    "11_geo+0.020_13m36s_building.jpg",                     # Indoor/building
]

def run_ollama_vision(model, image_path, prompt):
    cmd = ["ollama", "run", model, prompt]
    result = subprocess.run(
        cmd,
        input=f"[img]{image_path}[/img]",
        capture_output=True,
        text=True,
        timeout=120
    )
    return result.stdout.strip()

def run_ollama_api(model, image_path, prompt):
    import base64
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    payload = {
        "model": model,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
        "options": {"temperature": 0.1}
    }

    result = subprocess.run(
        ["curl", "-s", "http://localhost:11434/api/generate",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=180
    )

    try:
        resp = json.loads(result.stdout)
        return resp.get("response", "No response")
    except json.JSONDecodeError:
        return f"Error parsing response: {result.stdout[:200]}"


print(f"Model: {MODEL}")
print(f"Testing {len(FRAMES_TO_TEST)} frames")
print(f"Ground truth: Southern Province, Sri Lanka (~6.1°N, 80.5°E)")
print("=" * 100)

results = []

for frame_name in FRAMES_TO_TEST:
    frame_path = FRAMES_DIR / frame_name
    if not frame_path.exists():
        print(f"  SKIP: {frame_name} not found")
        continue

    timestamp = frame_name.split("_")[2] if len(frame_name.split("_")) >= 3 else "?"
    print(f"\n{'─' * 100}")
    print(f"  Frame: {frame_name}")
    print(f"  Time:  {timestamp}")
    print(f"{'─' * 100}")

    start = time.time()
    response = run_ollama_api(MODEL, str(frame_path), GEO_PROMPT)
    elapsed = time.time() - start

    print(f"\n{response}")
    print(f"\n  ⏱ Time: {elapsed:.1f}s")

    results.append({
        "frame": frame_name,
        "timestamp": timestamp,
        "response": response,
        "elapsed": round(elapsed, 1),
    })

print(f"\n{'=' * 100}")
print("  DONE — Compare each response against ground truth:")
print("  Actual: Southern Province, Sri Lanka, ~6.1°N 80.5°E")
print("  Creator: Poorna - The Nature Girl, village in Matara District area")
print(f"{'=' * 100}")

out_path = Path(__file__).parent / "vision_llm_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"  Results saved to: {out_path}")
