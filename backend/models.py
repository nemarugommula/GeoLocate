from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel


class LookupRequest(BaseModel):
    image_b64: str
    video_id: str
    timestamp_seconds: float
    video_title: str = ""
    video_description: str = ""
    channel_name: str = ""
    user_id: str = ""


class EvidenceItem(BaseModel):
    source: str
    detail: str
    confidence: str = "medium"


class LookupResult(BaseModel):
    id: str
    video_id: str
    timestamp_seconds: float
    location_name: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    confidence: str = "NONE"
    evidence: List[EvidenceItem] = []
    maps_url: Optional[str] = None
    status: str = "processing"
    created_at: str = ""


class FeedbackRequest(BaseModel):
    lookup_id: str
    vote: str  # "up" or "down"
    correct_location: Optional[str] = None
