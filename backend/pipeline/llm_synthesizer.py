from __future__ import annotations
import json
from llm.provider import generate as llm_generate

SYNTHESIS_PROMPT = """You are a geolocation expert. Your task is to determine where a YouTube video scene was filmed.

You have been given evidence from multiple automated signals. Analyze ALL evidence together with the image to triangulate the most likely filming location.

## Evidence from automated analysis:

### CLIP Scene Classification
{clip_result}

### GeoCLIP GPS Predictions (top matches)
{geoclip_result}

### Video Metadata
Title: {title}
Channel: {channel}
Metadata hints: {metadata_hints}

## Instructions:

1. Look at the image carefully for visual clues: terrain, vegetation, architecture, signage, script/language, road markings, driving side, cultural markers.
2. Weigh the automated evidence — metadata (title/description) is usually the strongest signal.
3. Combine all signals to determine the most likely location.
4. Be honest about uncertainty. If evidence is weak, say so.

## Required output format (valid JSON only, no other text):

IMPORTANT: Pick ONE best location as your primary answer. If you have alternative possibilities, list them separately. Do NOT combine multiple places into one location_name.

{{
    "location_name": "most specific place name for your BEST guess (one place only)",
    "region": "state/province/district of the best guess",
    "country": "country of the best guess",
    "lat": 0.0,
    "lon": 0.0,
    "confidence": "HIGH or MEDIUM or LOW",
    "reasoning": "2-3 sentences explaining which clues were most decisive",
    "alternatives": [
        {{"location": "second best guess location", "country": "country", "reason": "why this is possible"}}
    ]
}}

If you cannot determine the location at all, return:
{{
    "location_name": null,
    "region": null,
    "country": null,
    "lat": null,
    "lon": null,
    "confidence": "NONE",
    "reasoning": "explanation of what you could and couldn't determine",
    "alternatives": []
}}"""


def synthesize(
    image_b64: str,
    clip_result: dict,
    geoclip_predictions: list[dict],
    metadata_hints: dict,
    video_title: str,
    channel_name: str,
) -> dict:
    geoclip_summary = "\n".join(
        f"  #{i+1}: {p['place']} ({p['lat']:.4f}°, {p['lon']:.4f}°) prob={p['prob']:.4f}"
        for i, p in enumerate(geoclip_predictions[:5])
    )

    metadata_summary = json.dumps(metadata_hints, indent=2, default=str)

    prompt = SYNTHESIS_PROMPT.format(
        clip_result=json.dumps(clip_result, indent=2),
        geoclip_result=geoclip_summary or "No predictions available",
        title=video_title,
        channel=channel_name,
        metadata_hints=metadata_summary,
    )

    raw = llm_generate(prompt, image_b64=image_b64)
    return _parse_llm_response(raw)


def _parse_llm_response(raw: str) -> dict:
    # Try to extract JSON from the response
    try:
        # Look for JSON block in the response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except json.JSONDecodeError:
        pass

    # Fallback: return the raw text as reasoning with no structured location
    return {
        "location_name": None,
        "region": None,
        "country": None,
        "lat": None,
        "lon": None,
        "confidence": "LOW",
        "reasoning": raw[:500],
    }
