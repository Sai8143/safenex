from sqlalchemy import Column, String, Float, DateTime
from app.database import Base
from datetime import datetime
import uuid
from enum import Enum

class AccidentLifecycle(str, Enum):
    DETECTED = "DETECTED"
    CONFIRMED = "CONFIRMED"
    DISPATCHED = "DISPATCHED"
    AMBULANCE_EN_ROUTE = "AMBULANCE_EN_ROUTE"
    HOSPITAL_NOTIFIED = "HOSPITAL_NOTIFIED"
    POLICE_NOTIFIED = "POLICE_NOTIFIED"
    RESOLVED = "RESOLVED"
    FALSE_ALARM = "FALSE_ALARM"

    # Backward compatibility mappings
    POTENTIAL = "potential"
    LEGACY_CONFIRMED = "confirmed"
    LEGACY_DISPATCHED = "dispatched"
    LEGACY_RESOLVED = "resolved"


class Accident(Base):
    __tablename__ = "accidents"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String, nullable=True, default="Sector Main Road")

    image_path = Column(String, nullable=True)        # raw uploaded photo or frame
    annotated_image = Column(String, nullable=True)   # annotated image with bounding boxes

    accident_type = Column(
        String,
        nullable=False,
        default="photo"   # photo / video / rtsp
    )

    status = Column(
        String,
        nullable=False,
        default="confirmed"  # DETECTED / CONFIRMED / DISPATCHED / RESOLVED / etc.
    )

    confidence_score = Column(Float, nullable=True, default=0.0)
    severity_level = Column(String, nullable=True, default="MODERATE_COLLISION")  # CRITICAL_TRAUMA / MODERATE_COLLISION / MINOR_INCIDENT
    evidence_hash = Column(String, nullable=True, default="")                     # SHA-256 digital forensic tamper-proof hash
    details = Column(String, nullable=True, default="")

    timestamp = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
