from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import cv2
import numpy as np
import threading
from typing import List, Optional

from app.database import SessionLocal, engine
from app.models import Accident, Base
from app.schemas import AccidentResponse, HealthResponse, StatusUpdateRequest, SystemStatsResponse

from app.services.ai_detector import analyze_image_accident
from app.services.video_detector import detect_video_accident, _default_tracker
from app.services.notifier import notify_emergency, log_no_accident
from app.services.location import EMERGENCY_FACILITIES, find_nearest_emergency_facilities
from app.services.rtsp_stream import (
    process_rtsp_stream,
    process_camera_stream,
    get_active_streams_count,
    stop_stream_by_id,
    stop_all_streams
)
from app.services.websocket_manager import ws_manager


# -------------------------
# Database Initialization
# -------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SafeNex Real-Time AI Accident Detection API",
    version="2.0",
    description="Automated crash detection, evidence annotation, and real-time emergency dispatch platform."
)

# Standardized Error Handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        return JSONResponse(status_code=exc.status_code, content=detail)
    error_code = "BAD_REQUEST" if exc.status_code == 400 else ("NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": error_code, "message": str(detail)}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": "VALIDATION_ERROR", "message": str(exc)}
    )

# Configurable CORS
origins_env = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True if origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(BACKEND_DIR, "uploads"))
STATIC_DIR = os.getenv("STATIC_DIR", os.path.join(os.path.dirname(__file__), "static"))

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Dependency for DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# Web Dashboard & Root
# -------------------------
@app.get("/")
def root():
    return {
        "status": "AcciSense AI Platform Active",
        "dashboard_url": "/dashboard",
        "docs_url": "/docs"
    }

@app.get("/dashboard")
def get_dashboard():
    dashboard_file = os.path.join(STATIC_DIR, "dashboard.html")
    if os.path.exists(dashboard_file):
        return FileResponse(dashboard_file)
    return {"error": "Dashboard template not found"}

@app.get("/hospital")
def get_hospital_portal():
    hospital_file = os.path.join(STATIC_DIR, "hospital.html")
    if os.path.exists(hospital_file):
        return FileResponse(hospital_file)
    return {"error": "Hospital template not found"}

@app.get("/police")
def get_police_portal():
    police_file = os.path.join(STATIC_DIR, "police.html")
    if os.path.exists(police_file):
        return FileResponse(police_file)
    return {"error": "Police template not found"}

@app.get("/ambulance")
def get_ambulance_portal():
    ambulance_file = os.path.join(STATIC_DIR, "ambulance.html")
    if os.path.exists(ambulance_file):
        return FileResponse(ambulance_file)
    return {"error": "Ambulance template not found"}

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(health="OK", status="operational", timestamp=datetime.utcnow())


# -------------------------
# WebSocket Real-Time Alert Stream
# -------------------------
@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# -------------------------
# PHOTO-BASED ALERT (MOBILE APP / SOS)
# -------------------------
@app.post("/alert", response_model=AccidentResponse)
async def receive_alert(
    image: UploadFile = File(...),
    latitude: float = Form(default=28.6139),
    longitude: float = Form(default=77.2090),
    location_name: Optional[str] = Form(default="Mobile Reporter GPS Zone"),
    db: Session = Depends(get_db)
):
    contents = await image.read()
    if not contents or len(contents) == 0:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "INVALID_FRAME", "message": "Uploaded image is empty"}
        )

    img = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "INVALID_FRAME", "message": "Unable to decode uploaded image"}
        )

    filename = f"{uuid4()}.jpg"
    filepath = os.path.join(UPLOAD_DIR, filename)
    cv2.imwrite(filepath, img)

    # Deep AI Detection & Visual Evidence Annotation
    ai_result = analyze_image_accident(filepath, upload_dir=UPLOAD_DIR, is_stream=False)

    is_accident = ai_result["is_accident"]
    is_potential = ai_result.get("is_potential", False)
    should_notify = ai_result.get("should_notify", False)

    if is_accident:
        status_str = "confirmed"
        msg = "🚨 Accident confirmed via AI Image Analysis!"
    elif is_potential:
        status_str = "potential"
        msg = "⚠️ Possible incident detected. Under evaluation."
    else:
        status_str = "normal"
        msg = "ℹ️ Normal traffic scene analyzed. No accident detected."

    severity_level = ai_result.get("severity_level", "NONE")
    evidence_hash = ai_result.get("evidence_hash", "")

    # Save DB record for all monitored inputs
    accident_record = Accident(
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        image_path=filename,
        annotated_image=ai_result["annotated_filename"],
        accident_type="photo",
        status=status_str,
        confidence_score=ai_result["confidence_score"],
        severity_level=severity_level,
        evidence_hash=evidence_hash,
        details=ai_result["details"]
    )
    db.add(accident_record)
    db.commit()
    db.refresh(accident_record)

    # Trigger emergency notification ONLY when accident is confirmed by decision engine
    if should_notify and is_accident:
        notify_emergency(latitude, longitude, {
            "accident_id": accident_record.id,
            "annotated_image": ai_result["annotated_filename"],
            "location_name": location_name,
            "confidence_score": ai_result["confidence_score"],
            "accident_type": "photo",
            "severity_level": severity_level,
            "evidence_hash": evidence_hash
        })
    else:
        log_no_accident(latitude, longitude)

    return AccidentResponse(
        id=accident_record.id,
        message=msg,
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        timestamp=accident_record.timestamp,
        image_saved_as=filename,
        annotated_image=ai_result["annotated_filename"],
        accident_type="photo",
        status=status_str,
        confidence_score=ai_result["confidence_score"],
        severity_level=severity_level,
        evidence_hash=evidence_hash,
        details=ai_result["details"]
    )


# -------------------------
# VIDEO FRAME ALERT (CCTV INTEGRATION)
# -------------------------
@app.post("/video-frame")
async def video_frame(
    frame: UploadFile = File(...),
    latitude: float = Form(default=28.6139),
    longitude: float = Form(default=77.2090),
    db: Session = Depends(get_db)
):
    contents = await frame.read()
    if not contents or len(contents) == 0:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "INVALID_FRAME", "message": "Uploaded video frame is empty"}
        )

    img = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "error": "INVALID_FRAME", "message": "Unable to decode uploaded video frame"}
        )

    # Pass frame through StreamSessionTracker
    stream_result = _default_tracker.process_frame(img)
    is_accident = stream_result["is_accident"]
    is_potential = stream_result.get("is_potential", False)
    should_notify = stream_result.get("should_notify", False)
    status_str = "confirmed" if is_accident else ("potential" if is_potential else "normal")

    filename = f"cctv_{uuid4()}.jpg"
    raw_path = os.path.join(UPLOAD_DIR, filename)
    cv2.imwrite(raw_path, img)

    ai_result = analyze_image_accident(
        raw_path,
        upload_dir=UPLOAD_DIR,
        temporal_data=stream_result.get("temporal_data"),
        is_stream=True
    )

    severity_level = ai_result.get("severity_level", stream_result.get("severity_level", "MODERATE_COLLISION"))
    evidence_hash = ai_result.get("evidence_hash", "")

    if should_notify and is_accident:
        accident = Accident(
            latitude=latitude,
            longitude=longitude,
            location_name="CCTV Traffic Monitoring",
            image_path=filename,
            annotated_image=ai_result["annotated_filename"],
            accident_type="video",
            status="confirmed",
            confidence_score=stream_result["confidence"],
            severity_level=severity_level,
            evidence_hash=evidence_hash,
            details=stream_result["reason"]
        )
        db.add(accident)
        db.commit()
        db.refresh(accident)

        notify_emergency(latitude, longitude, {
            "accident_id": accident.id,
            "annotated_image": ai_result["annotated_filename"],
            "confidence_score": stream_result["confidence"],
            "location_name": "CCTV Traffic Monitoring",
            "accident_type": "video",
            "severity_level": severity_level,
            "evidence_hash": evidence_hash
        })

        return {
            "id": accident.id,
            "message": "🚨 Accident confirmed via CCTV Video Stream",
            "status": "confirmed",
            "annotated_image": ai_result["annotated_filename"],
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": accident.timestamp,
            "confidence_score": stream_result["confidence"],
            "severity_level": severity_level,
            "evidence_hash": evidence_hash
        }

    log_no_accident(latitude, longitude)
    return {
        "message": "No accident detected" if status_str == "normal" else "Potential incident observing",
        "status": status_str,
        "confidence_score": stream_result["confidence"],
        "reason": stream_result["reason"]
    }


# -------------------------
# STREAM CONTROL ENDPOINTS
# -------------------------
@app.post("/start-rtsp")
def start_rtsp_monitoring(
    rtsp_url: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...)
):
    stream_id = f"rtsp_{uuid4().hex[:6]}"
    thread = threading.Thread(
        target=process_rtsp_stream,
        args=(rtsp_url, latitude, longitude, stream_id),
        daemon=True
    )
    thread.start()

    return {
        "message": "RTSP CCTV monitoring initiated",
        "stream_id": stream_id,
        "rtsp_url": rtsp_url
    }

@app.post("/start-camera")
def start_camera(
    camera_index: int = Form(0),
    latitude: float = Form(...),
    longitude: float = Form(...)
):
    stream_id = f"cam_{uuid4().hex[:6]}"
    thread = threading.Thread(
        target=process_camera_stream,
        args=(camera_index, latitude, longitude, stream_id),
        daemon=True
    )
    thread.start()

    return {"message": "Local camera monitoring started", "stream_id": stream_id}

@app.post("/stop-stream/{stream_id}")
def stop_stream(stream_id: str):
    success = stop_stream_by_id(stream_id)
    if not success:
        raise HTTPException(status_code=404, detail="Stream ID not active")
    return {"message": f"Stream {stream_id} stopped successfully"}


# -------------------------
# RESTful ACCIDENT LOGS & STATS
# -------------------------
@app.get("/api/accidents", response_model=List[AccidentResponse])
def get_accidents(db: Session = Depends(get_db)):
    accidents = db.query(Accident).order_by(Accident.timestamp.desc()).limit(100).all()
    return accidents

@app.get("/api/accidents/{id}", response_model=AccidentResponse)
def get_accident_detail(id: str, db: Session = Depends(get_db)):
    acc = db.query(Accident).filter(Accident.id == id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Accident record not found")
    return acc

@app.patch("/api/accidents/{id}/status")
def update_accident_status(id: str, payload: StatusUpdateRequest, db: Session = Depends(get_db)):
    acc = db.query(Accident).filter(Accident.id == id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Accident record not found")

    acc.status = payload.status
    db.commit()

    # Notify dashboard of status update via WebSocket
    ws_manager.broadcast_sync({
        "type": "STATUS_UPDATE",
        "accident_id": id,
        "status": payload.status
    })

    return {"message": f"Accident status updated to {payload.status}", "status": payload.status}

@app.delete("/api/accidents/{id}")
def delete_accident(id: str, db: Session = Depends(get_db)):
    acc = db.query(Accident).filter(Accident.id == id).first()
    if not acc:
        raise HTTPException(status_code=404, detail="Accident record not found")
    db.delete(acc)
    db.commit()
    return {"message": "Accident log deleted"}

@app.get("/api/emergency-facilities")
def get_emergency_facilities(lat: Optional[float] = None, lng: Optional[float] = None):
    facilities = EMERGENCY_FACILITIES
    if lat is not None and lng is not None:
        nearest = find_nearest_emergency_facilities(lat, lng)
        return {"facilities": facilities, "nearest": nearest}
    return {"facilities": facilities}

@app.get("/api/stats", response_model=SystemStatsResponse)
def get_system_stats(db: Session = Depends(get_db)):
    total = db.query(Accident).count()
    confirmed = db.query(Accident).filter(Accident.status.in_(["confirmed", "CONFIRMED"])).count()
    dispatched = db.query(Accident).filter(
        Accident.status.in_(["dispatched", "DISPATCHED", "AMBULANCE_EN_ROUTE", "HOSPITAL_NOTIFIED", "POLICE_NOTIFIED"])
    ).count()
    resolved = db.query(Accident).filter(Accident.status.in_(["resolved", "RESOLVED"])).count()
    potential = db.query(Accident).filter(Accident.status.in_(["potential", "POTENTIAL", "DETECTED"])).count()
    active_streams = get_active_streams_count()

    return SystemStatsResponse(
        total_accidents=total,
        confirmed_count=confirmed,
        dispatched_count=dispatched,
        resolved_count=resolved,
        potential_count=potential,
        active_streams=active_streams
    )