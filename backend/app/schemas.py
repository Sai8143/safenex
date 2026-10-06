from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class AccidentResponse(BaseModel):
    id: Optional[str] = None
    message: Optional[str] = "Alert processed"
    latitude: float
    longitude: float
    location_name: Optional[str] = "Sector Main Road"
    timestamp: datetime
    image_saved_as: Optional[str] = None
    annotated_image: Optional[str] = None
    accident_type: Optional[str] = "photo"
    status: Optional[str] = "confirmed"
    confidence_score: Optional[float] = 0.0
    severity_level: Optional[str] = "MODERATE_COLLISION"
    evidence_hash: Optional[str] = ""
    details: Optional[str] = ""

    class Config:
        from_attributes = True

class StatusUpdateRequest(BaseModel):
    status: str  # DETECTED / CONFIRMED / DISPATCHED / AMBULANCE_EN_ROUTE / HOSPITAL_NOTIFIED / POLICE_NOTIFIED / RESOLVED / FALSE_ALARM

class SystemStatsResponse(BaseModel):
    total_accidents: int
    confirmed_count: int
    dispatched_count: int
    resolved_count: int
    potential_count: int
    active_streams: int

class HealthResponse(BaseModel):
    health: str
    status: str = "operational"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AccidentAlertPayload(BaseModel):
    event: str = "ACCIDENT_CONFIRMED"
    accident_id: str
    latitude: float
    longitude: float
    location: str
    confidence: float
    accident_type: str
    timestamp: str
    annotated_image: Optional[str] = None
    status: str = "CONFIRMED"
    severity_level: Optional[str] = "MODERATE_COLLISION"
    evidence_hash: Optional[str] = ""
    nearest_facilities: Optional[dict] = None
    type: Optional[str] = "ACCIDENT_ALERT"
    formatted_message: Optional[str] = None
