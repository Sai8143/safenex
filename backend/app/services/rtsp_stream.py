import os
import cv2
import time
import threading
from uuid import uuid4
from typing import Dict, Any

from app.services.video_detector import StreamSessionTracker
from app.services.ai_detector import analyze_image_accident
from app.services.notifier import notify_emergency
from app.database import SessionLocal
from app.models import Accident

active_streams = {}
active_streams_lock = threading.Lock()

def get_active_streams_count() -> int:
    with active_streams_lock:
        return len(active_streams)

def stop_stream_by_id(stream_id: str) -> bool:
    with active_streams_lock:
        if stream_id in active_streams:
            active_streams[stream_id]["running"] = False
            return True
        return False

def stop_all_streams():
    with active_streams_lock:
        for sid in list(active_streams.keys()):
            active_streams[sid]["running"] = False


def _record_stream_incident(
    frame: cv2.Mat,
    latitude: float,
    longitude: float,
    stream_id: str,
    stream_type: str,
    assessment: Dict[str, Any]
):
    """Save evidence frame and persist accident record to database."""
    try:
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        upload_dir = os.getenv("UPLOAD_DIR", os.path.join(backend_dir, "uploads"))
        os.makedirs(upload_dir, exist_ok=True)

        filename = f"{stream_type}_{uuid4().hex[:8]}.jpg"
        raw_path = os.path.join(upload_dir, filename)
        cv2.imwrite(raw_path, frame)

        ai_res = analyze_image_accident(
            raw_path,
            upload_dir=upload_dir,
            temporal_data=assessment.get("temporal_data"),
            is_stream=True
        )

        db = SessionLocal()
        try:
            record = Accident(
                latitude=latitude,
                longitude=longitude,
                location_name=f"CCTV Stream [{stream_id}]",
                image_path=filename,
                annotated_image=ai_res["annotated_filename"],
                accident_type=stream_type,
                status="confirmed",
                confidence_score=assessment.get("confidence", 0.85),
                details=assessment.get("reason", "CCTV multi-frame temporal confirmation")
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            notify_emergency(latitude, longitude, {
                "accident_id": record.id,
                "annotated_image": ai_res["annotated_filename"],
                "confidence_score": record.confidence_score,
                "location_name": record.location_name,
                "accident_type": stream_type,
                "stream_id": stream_id
            })
        finally:
            db.close()
    except Exception as e:
        print(f"❌ Error persisting stream incident: {e}")


def process_rtsp_stream(rtsp_url: str, latitude: float, longitude: float, stream_id: str = "rtsp_default"):
    """
    Continuously processes RTSP CCTV stream with isolated StreamSessionTracker.
    """
    tracker = StreamSessionTracker(session_id=stream_id)
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print(f"❌ RTSP stream ({rtsp_url}) not accessible")
        return

    print(f"✅ RTSP stream connected: {rtsp_url}")
    with active_streams_lock:
        active_streams[stream_id] = {
            "type": "rtsp",
            "url": rtsp_url,
            "running": True,
            "start_time": time.time()
        }

    frame_count = 0
    skip_frames = 3

    try:
        while True:
            with active_streams_lock:
                if stream_id in active_streams and not active_streams[stream_id]["running"]:
                    print(f"🛑 Stopping RTSP stream: {stream_id}")
                    break

            ret, frame = cap.read()
            if not ret:
                print("⚠️ Frame read failed, retrying...")
                time.sleep(1)
                continue

            frame_count += 1
            if frame_count % skip_frames != 0:
                continue

            assessment = tracker.process_frame(frame)
            if assessment.get("is_accident") and assessment.get("should_notify"):
                print(f"🚨 ACCIDENT CONFIRMED FROM RTSP STREAM [{stream_id}]")
                _record_stream_incident(frame, latitude, longitude, stream_id, "rtsp", assessment)
                time.sleep(8)  # Cooldown before resuming checks
    finally:
        cap.release()
        with active_streams_lock:
            active_streams.pop(stream_id, None)


def process_camera_stream(source, latitude: float, longitude: float, stream_id: str = "webcam_default"):
    tracker = StreamSessionTracker(session_id=stream_id)
    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"❌ Camera source ({source}) not accessible")
        return

    print(f"✅ Camera connected: {source}")
    with active_streams_lock:
        active_streams[stream_id] = {
            "type": "webcam",
            "source": source,
            "running": True,
            "start_time": time.time()
        }

    try:
        while True:
            with active_streams_lock:
                if stream_id in active_streams and not active_streams[stream_id]["running"]:
                    print(f"🛑 Stopping Camera stream: {stream_id}")
                    break

            ret, frame = cap.read()
            if not ret:
                break

            assessment = tracker.process_frame(frame)
            if assessment.get("is_accident") and assessment.get("should_notify"):
                print(f"🚨 ACCIDENT CONFIRMED FROM CAMERA STREAM [{stream_id}]")
                _record_stream_incident(frame, latitude, longitude, stream_id, "camera", assessment)
                time.sleep(8)
    finally:
        cap.release()
        with active_streams_lock:
            active_streams.pop(stream_id, None)
