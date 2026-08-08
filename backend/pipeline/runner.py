from __future__ import annotations
import os
import base64
import uuid
import tempfile
from datetime import datetime, timezone
from PIL import Image
from io import BytesIO

from models import LookupRequest, LookupResult, EvidenceItem
from pipeline.clip_filter import classify_frame
from pipeline.geoclip_predict import predict_location
from pipeline.metadata_parser import extract_location_hints
from pipeline.llm_synthesizer import synthesize
from pipeline.geocoder import forward_geocode, make_maps_url
def run_pipeline(request: LookupRequest, clip_model, clip_preprocess, clip_text_features,
                 geoclip_model) -> LookupResult:
    lookup_id = str(uuid.uuid4())
    evidence = []

    image_bytes = base64.b64decode(request.image_b64)
    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    tmp_path = None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp_path = tmp.name
        tmp.close()
        image.save(tmp_path, "JPEG")

        # Step 1: CLIP
        clip_result = classify_frame(image, clip_model, clip_preprocess, clip_text_features)
        evidence.append(EvidenceItem(
            source="CLIP Scene Filter",
            detail=f"{'Geo-relevant' if clip_result['is_high_signal'] else 'Low geo signal'}: "
                   f"{clip_result['best_category']} (score: {clip_result['geo_score']:+.3f})",
            confidence="high" if clip_result["is_high_signal"] else "low",
        ))

        # Step 2: GeoCLIP
        geoclip_predictions = predict_location(tmp_path, geoclip_model, top_k=5)
        if geoclip_predictions:
            top = geoclip_predictions[0]
            evidence.append(EvidenceItem(
                source="GeoCLIP GPS Prediction",
                detail=f"Top prediction: {top['place']} ({top['lat']:.4f}°, {top['lon']:.4f}°, prob={top['prob']:.4f})",
                confidence="medium" if top["prob"] > 0.05 else "low",
            ))

        # Step 3: Metadata
        metadata = extract_location_hints(request.video_title, request.video_description, request.channel_name)
        if metadata["country_mentions"]:
            evidence.append(EvidenceItem(
                source="Video Metadata",
                detail=f"Countries mentioned: {', '.join(metadata['country_mentions'])}",
                confidence="high",
            ))
        if metadata["scripts_detected"]:
            evidence.append(EvidenceItem(
                source="Script Detection",
                detail=f"Scripts found: {', '.join(metadata['scripts_detected'])} → "
                       f"{', '.join(metadata['country_hints_from_scripts'])}",
                confidence="high",
            ))
        if metadata["place_names"]:
            evidence.append(EvidenceItem(
                source="Place Names",
                detail=f"Found: {', '.join(metadata['place_names'][:5])}",
                confidence="medium",
            ))

        # Step 4: LLM synthesis
        llm_result = synthesize(
            image_b64=request.image_b64,
            clip_result=clip_result,
            geoclip_predictions=geoclip_predictions,
            metadata_hints=metadata,
            video_title=request.video_title,
            channel_name=request.channel_name,
        )

        if llm_result.get("reasoning"):
            evidence.append(EvidenceItem(
                source="AI Synthesis",
                detail=llm_result["reasoning"][:300],
                confidence=llm_result.get("confidence", "low").lower(),
            ))

        alternatives = llm_result.get("alternatives", [])
        if alternatives:
            alt_text = " | ".join(
                f"{a.get('location', a.get('country', '?'))}" for a in alternatives[:3]
            )
            evidence.append(EvidenceItem(
                source="Alternative Locations",
                detail=f"Also possible: {alt_text}",
                confidence="low",
            ))

        # Step 5: Geocoding
        lat = llm_result.get("lat")
        lon = llm_result.get("lon")
        location_name = llm_result.get("location_name")
        region = llm_result.get("region")
        country = llm_result.get("country")

        if not lat and (location_name or country):
            search = ", ".join(filter(None, [location_name, region, country]))
            geo = forward_geocode(search)
            if geo:
                lat, lon = geo["lat"], geo["lon"]

        # Fallback: use GeoCLIP's best prediction if we still have no coordinates
        if not lat and geoclip_predictions:
            best_geo = geoclip_predictions[0]
            lat, lon = best_geo["lat"], best_geo["lon"]
            if not location_name:
                location_name = best_geo.get("place", "Unknown area")
            if not country:
                country = best_geo.get("country", "")

        maps_url = make_maps_url(lat, lon) if lat and lon else None

        return LookupResult(
            id=lookup_id,
            video_id=request.video_id,
            timestamp_seconds=request.timestamp_seconds,
            location_name=location_name,
            region=region,
            country=country,
            lat=lat,
            lon=lon,
            confidence=llm_result.get("confidence", "NONE"),
            evidence=evidence,
            maps_url=maps_url,
            status="complete",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
