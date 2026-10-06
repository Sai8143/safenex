from datetime import datetime
from typing import Dict, Any, Optional
from app.services.websocket_manager import ws_manager
from app.services.location import find_nearest_emergency_facilities

def notify_emergency(latitude: float, longitude: float, extra_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Trigger emergency notifications.
    Used ONLY when accident is CONFIRMED by the Decision Engine.
    Emits structured Section 8 payload over WebSockets to Hospital, Police, Ambulance & Dashboard.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    extra = extra_data or {}

    accident_id = str(extra.get("accident_id", "N/A"))
    location_name = extra.get("location_name", f"Traffic Sector ({latitude:.4f}, {longitude:.4f})")
    confidence = float(extra.get("confidence_score", extra.get("confidence", 0.90)))
    accident_type = extra.get("accident_type", "collision")
    annotated_image = extra.get("annotated_image", None)
    severity_level = extra.get("severity_level", "MODERATE_COLLISION")
    evidence_hash = extra.get("evidence_hash", "")

    # Automated Nearest Facility & Route ETA Discovery
    nearest_facilities = extra.get("nearest_facilities")
    if not nearest_facilities:
        try:
            nearest_facilities = find_nearest_emergency_facilities(latitude, longitude)
        except Exception:
            nearest_facilities = None

    print("\n================ EMERGENCY ALERT ================")
    print("🚨 ACCIDENT CONFIRMED")
    print(f"🕒 Time (UTC): {timestamp}")
    print(f"📍 Location: {location_name} (Lat {latitude:.4f}, Lng {longitude:.4f})")
    print(f"🔢 Accident ID: {accident_id} | Confidence: {confidence*100:.1f}%")
    print(f"🩺 Triage Severity: {severity_level}")
    if evidence_hash:
        print(f"🔒 Forensic SHA-256: {evidence_hash[:16]}...")
    print("🏥 Hospital Services: NOTIFIED")
    print("🚓 Police Department: NOTIFIED")
    print("🚑 Ambulance Services: NOTIFIED")
    print("=================================================\n")

    formatted = (
        "================ EMERGENCY ALERT ================\n"
        "🚨 ACCIDENT CONFIRMED\n"
        f"🕒 Time (UTC): {timestamp}\n"
        f"📍 Location: {location_name}\n"
        f"🌐 Coordinates: {latitude:.5f}, {longitude:.5f}\n"
        f"🩺 Triage Severity: {severity_level}\n"
        f"🔢 Incident ID: {accident_id} | Type: {accident_type.upper()}\n"
        "🏥 Hospital Services: NOTIFIED\n"
        "🚓 Police Department: NOTIFIED\n"
        "🚑 Ambulance Services: NOTIFIED\n"
        "================================================="
    )

    # Structured Section 8 Emergency Payload with Uniqueness Extensions
    event_data = {
        "event": "ACCIDENT_CONFIRMED",
        "accident_id": accident_id,
        "latitude": latitude,
        "longitude": longitude,
        "location": location_name,
        "location_name": location_name,
        "confidence": confidence,
        "accident_type": accident_type,
        "severity_level": severity_level,
        "evidence_hash": evidence_hash,
        "nearest_facilities": nearest_facilities,
        "timestamp": timestamp,
        "annotated_image": annotated_image,
        "status": "CONFIRMED",
        # Backward compatibility for portal cards
        "type": "ACCIDENT_ALERT",
        "formatted_message": formatted,
        "message": f"🚨 ACCIDENT CONFIRMED ({severity_level})! Emergency Services Dispatched."
    }

    # Add any auxiliary metadata
    for k, v in extra.items():
        if k not in event_data:
            event_data[k] = v

    # Broadcast thread-safely
    ws_manager.broadcast_sync(event_data)

    return event_data


def log_no_accident(latitude: float, longitude: float) -> None:
    """
    Silent logging for normal conditions.
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[INFO] {timestamp} | No accident detected at ({latitude:.4f}, {longitude:.4f})")
