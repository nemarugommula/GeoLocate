from __future__ import annotations
import json
from fastapi import APIRouter, Request, HTTPException
from models import LookupRequest, LookupResult
from database import (
    get_connection, check_rate_limit, increment_lookup_count,
    get_cached_result, save_cache, save_lookup,
)
from pipeline.runner import run_pipeline
from config import RATE_LIMIT_PER_DAY, CACHE_TIMESTAMP_TOLERANCE

router = APIRouter()


@router.post("/lookup", response_model=LookupResult)
def lookup(req: LookupRequest, request: Request):
    conn = get_connection()
    try:
        if req.user_id and not check_rate_limit(conn, req.user_id, RATE_LIMIT_PER_DAY):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit reached. Maximum {RATE_LIMIT_PER_DAY} lookups per day.",
            )

        cached = get_cached_result(conn, req.video_id, req.timestamp_seconds, CACHE_TIMESTAMP_TOLERANCE)
        if cached:
            return LookupResult(**json.loads(cached))

        result = run_pipeline(
            request=req,
            clip_model=request.app.state.clip_model,
            clip_preprocess=request.app.state.clip_preprocess,
            clip_text_features=request.app.state.clip_text_features,
            geoclip_model=request.app.state.geoclip_model,
        )

        if req.user_id:
            increment_lookup_count(conn, req.user_id)

        save_lookup(conn, {
            "id": result.id,
            "user_id": req.user_id,
            "video_id": result.video_id,
            "timestamp_seconds": result.timestamp_seconds,
            "location_name": result.location_name,
            "region": result.region,
            "country": result.country,
            "lat": result.lat,
            "lon": result.lon,
            "confidence": result.confidence,
            "evidence_json": json.dumps([e.model_dump() for e in result.evidence]),
            "maps_url": result.maps_url,
            "status": result.status,
        })

        save_cache(conn, req.video_id, req.timestamp_seconds,
                   CACHE_TIMESTAMP_TOLERANCE, result.model_dump_json())

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
    finally:
        conn.close()
