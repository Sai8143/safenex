import os
import sys
import cv2
import json
import io
import time
import numpy as np

# Ensure backend is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app, UPLOAD_DIR
from app.database import SessionLocal, DATABASE_URL
from app.models import Accident, AccidentLifecycle
from app.services.tracker import CentroidVehicleTracker
from app.services.temporal_filter import TemporalStreamVerifier
from app.services.decision_engine import DecisionEngine, AccidentDecision
from app.services.ai_detector import analyze_image_accident, compute_iou, compute_roi_damage_score
from app.services.notifier import notify_emergency

client = TestClient(app)

def make_test_image(num_cars=2, overlap=False, damage=False):
    """Synthesize 640x480 test image."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Gray road
    cv2.rectangle(img, (0, 0), (640, 480), (60, 60, 60), -1)

    if num_cars == 1:
        cv2.rectangle(img, (220, 180), (420, 300), (255, 120, 0), -1)
    elif num_cars >= 2:
        if overlap:
            # Overlapping vehicles (collision candidate)
            cv2.rectangle(img, (180, 180), (360, 300), (255, 120, 0), -1)
            cv2.rectangle(img, (300, 190), (480, 310), (0, 100, 255), -1)
        else:
            # Parallel lanes (normal traffic)
            cv2.rectangle(img, (100, 180), (250, 300), (255, 120, 0), -1)
            cv2.rectangle(img, (380, 180), (530, 300), (0, 100, 255), -1)

    if damage:
        # Texture lines to simulate crushed metal / shattered glass
        for _ in range(60):
            x = np.random.randint(180, 480)
            y = np.random.randint(180, 310)
            cv2.line(img, (x, y), (x + 20, y + 20), (255, 255, 255), 2)

    return img


def run_full_suite():
    print("==================================================================")
    print("⚡ ACCISENSE MASTER AUTOMATED END-TO-END TEST SUITE ⚡")
    print("==================================================================")

    # -------------------------------------------------------------
    # Test 1: Backend Health & Diagnostics
    # -------------------------------------------------------------
    print("\n[TEST 1] Backend Health & Diagnostics...")
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["health"] == "OK"
    print("  ✅ /health endpoint responded 200 OK")

    # -------------------------------------------------------------
    # Test 2: Input Validation & Structured JSON Errors
    # -------------------------------------------------------------
    print("\n[TEST 2] Input Validation & Structured Error Responses...")
    # Empty upload
    r_empty = client.post("/alert", files={"image": ("empty.jpg", io.BytesIO(b""), "image/jpeg")}, data={"latitude": "28.6", "longitude": "77.2"})
    assert r_empty.status_code == 400
    assert r_empty.json()["error"] == "INVALID_FRAME"

    # Corrupt upload
    r_corrupt = client.post("/alert", files={"image": ("corrupt.jpg", io.BytesIO(b"not-an-image"), "image/jpeg")}, data={"latitude": "28.6", "longitude": "77.2"})
    assert r_corrupt.status_code == 400
    assert r_corrupt.json()["error"] == "INVALID_FRAME"
    print("  ✅ Invalid & empty uploads rejected with structured JSON errors")

    # -------------------------------------------------------------
    # Test 3: Centroid Vehicle Tracking & Motion Estimation
    # -------------------------------------------------------------
    print("\n[TEST 3] Centroid Multi-Vehicle Tracking & Velocity...")
    tracker = CentroidVehicleTracker(max_distance=90.0)
    # Frame 1: initial detection
    tracks_f1 = tracker.update([(120, 120, 220, 220)], ["car"], [0.92])
    assert len(tracks_f1) == 1
    tid = tracks_f1[0].track_id

    # Frame 2: moving forward
    tracks_f2 = tracker.update([(140, 120, 240, 220)], ["car"], [0.92])
    assert tracks_f2[0].track_id == tid
    assert tracks_f2[0].velocities[-1] >= 15.0

    # Frame 3: halted post-impact
    tracks_f3 = tracker.update([(140, 120, 240, 220)], ["car"], [0.92])
    assert tracks_f3[0].stopped_frames >= 1
    print("  ✅ Vehicle track preservation & kinematic halt detection verified")

    # -------------------------------------------------------------
    # Test 4: Temporal Multi-Frame Persistence Verification
    # -------------------------------------------------------------
    print("\n[TEST 4] Temporal Multi-Frame Persistence...")
    verifier = TemporalStreamVerifier(window_size=7)
    # Frame 1 overlap: candidate but NOT confirmed
    res_t1 = verifier.add_frame_assessment(has_overlap=True, max_iou=0.25, damage_score=0.45, confidence=0.60)
    assert not res_t1["is_confirmed"]
    assert res_t1["is_potential"]

    # Frame 2 overlap: still NOT confirmed (needs >= 3 consecutive)
    res_t2 = verifier.add_frame_assessment(has_overlap=True, max_iou=0.25, damage_score=0.45, confidence=0.65)
    assert not res_t2["is_confirmed"]

    # Frame 3 overlap + abnormal stop: CONFIRMED
    res_t3 = verifier.add_frame_assessment(has_overlap=True, max_iou=0.28, damage_score=0.50, confidence=0.75, has_abnormal_stop=True)
    assert res_t3["is_confirmed"]
    print("  ✅ Single-frame false alarm suppressed; multi-frame persistence confirmed")

    # -------------------------------------------------------------
    # Test 5: Decision Engine Authority
    # -------------------------------------------------------------
    print("\n[TEST 5] Authoritative Decision Engine...")
    # Normal traffic (low overlap, no damage)
    dec_norm = DecisionEngine.evaluate(vehicle_count=2, max_iou=0.08, damage_score=0.10, confidence=0.25)
    assert dec_norm["decision"] == AccidentDecision.NORMAL_TRAFFIC
    assert not dec_norm["should_notify"]

    # Confirmed accident
    temp_conf = {"is_confirmed": True, "avg_confidence": 0.88, "consecutive_collisions": 4}
    dec_conf = DecisionEngine.evaluate(vehicle_count=2, max_iou=0.35, damage_score=0.55, confidence=0.88, temporal_data=temp_conf, is_stream=True)
    assert dec_conf["decision"] == AccidentDecision.CONFIRMED_ACCIDENT
    assert dec_conf["should_notify"]
    print("  ✅ Decision Engine properly gates emergency dispatches")

    # -------------------------------------------------------------
    # Test 6: Database CRUD & Full Incident Lifecycle
    # -------------------------------------------------------------
    print("\n[TEST 6] Database Incident Lifecycle...")
    db = SessionLocal()
    try:
        acc = Accident(
            latitude=17.4485,
            longitude=78.3758,
            location_name="Hitec City Cyber Towers",
            image_path="test_raw.jpg",
            annotated_image="test_ann.jpg",
            accident_type="video",
            status=AccidentLifecycle.CONFIRMED.value,
            confidence_score=0.92,
            details="Collision confirmed via decision engine"
        )
        db.add(acc)
        db.commit()
        db.refresh(acc)
        test_id = acc.id

        # Lifecycle update: POLICE_NOTIFIED
        r_p = client.patch(f"/api/accidents/{test_id}/status", json={"status": AccidentLifecycle.POLICE_NOTIFIED.value})
        assert r_p.status_code == 200
        assert r_p.json()["status"] == AccidentLifecycle.POLICE_NOTIFIED.value

        # Lifecycle update: AMBULANCE_EN_ROUTE
        r_a = client.patch(f"/api/accidents/{test_id}/status", json={"status": AccidentLifecycle.AMBULANCE_EN_ROUTE.value})
        assert r_a.status_code == 200
        assert r_a.json()["status"] == AccidentLifecycle.AMBULANCE_EN_ROUTE.value

        # Lifecycle update: RESOLVED
        r_r = client.patch(f"/api/accidents/{test_id}/status", json={"status": AccidentLifecycle.RESOLVED.value})
        assert r_r.status_code == 200
        assert r_r.json()["status"] == AccidentLifecycle.RESOLVED.value

        db.delete(acc)
        db.commit()
        print("  ✅ Full lifecycle progression (CONFIRMED -> POLICE -> AMBULANCE -> RESOLVED) verified")
    finally:
        db.close()

    # -------------------------------------------------------------
    # Test 7: Real-Time WebSocket Section 8 Event Broadcast
    # -------------------------------------------------------------
    print("\n[TEST 7] WebSocket Section 8 Emergency Payload Broadcast...")
    with client.websocket_connect("/ws/alerts") as ws:
        notify_emergency(
            latitude=17.4485,
            longitude=78.3758,
            extra_data={
                "accident_id": "test_e2e_99",
                "location_name": "Cyber Towers Traffic Signal",
                "confidence_score": 0.94,
                "accident_type": "collision"
            }
        )
        msg = ws.receive_text()
        payload = json.loads(msg)
        assert payload["event"] == "ACCIDENT_CONFIRMED"
        assert payload["accident_id"] == "test_e2e_99"
        assert payload["status"] == "CONFIRMED"
        assert payload["confidence"] == 0.94
        print("  ✅ Section 8 structured event payload delivered across WebSocket")

    # -------------------------------------------------------------
    # Test 8: False-Positive Suppression on Video Stream
    # -------------------------------------------------------------
    print("\n[TEST 8] False Positive Suppression on Normal Traffic...")
    normal_img = make_test_image(num_cars=2, overlap=False, damage=False)
    _, norm_enc = cv2.imencode(".jpg", normal_img)
    r_stream = client.post(
        "/video-frame",
        files={"frame": ("normal_traffic.jpg", norm_enc.tobytes(), "image/jpeg")},
        data={"latitude": "17.4485", "longitude": "78.3758"}
    )
    assert r_stream.status_code == 200
    res_st = r_stream.json()
    assert res_st["status"] in ["normal", "potential"]
    assert "No accident detected" in res_st["message"] or "observing" in res_st["message"]
    print("  ✅ Normal traffic processed without false positive emergency alert")

    # -------------------------------------------------------------
    # Test 9: Department Portals Availability & Script Integrity
    # -------------------------------------------------------------
    print("\n[TEST 9] Multi-Department Portals & Static Serving...")
    for route in ["/dashboard", "/hospital", "/police", "/ambulance"]:
        resp = client.get(route)
        assert resp.status_code == 200
        assert "/ws/alerts" in resp.text
        assert "AcciSense" in resp.text
    print("  ✅ All 4 Department Portals active with live WebSocket integrations")

    # -------------------------------------------------------------
    # Test 10: Medical Triage Severity & Nearest Facility Routing
    # -------------------------------------------------------------
    print("\n[TEST 10] Medical Triage Severity & Dynamic Nearest Facilities...")
    from app.services.location import find_nearest_emergency_facilities
    # Test triage calculation
    crit_sev = DecisionEngine.calculate_severity(max_iou=0.45, damage_score=0.65, confidence=0.90)
    assert crit_sev == "CRITICAL_TRAUMA"
    mod_sev = DecisionEngine.calculate_severity(max_iou=0.20, damage_score=0.25, confidence=0.60)
    assert mod_sev == "MODERATE_COLLISION"

    # Test dynamic facility discovery (Hyderabad coordinates)
    facilities = find_nearest_emergency_facilities(17.4485, 78.3758)
    assert "hospital" in facilities and "police" in facilities and "ambulance" in facilities
    assert facilities["hospital"]["distance_km"] > 0.0
    assert facilities["hospital"]["eta_minutes"] >= 1
    print(f"  ✅ Nearest hospital found: {facilities['hospital']['name']} (ETA: {facilities['hospital']['eta_minutes']} min)")
    print("  ✅ Automated emergency dispatch routing & triage verified")

    # -------------------------------------------------------------
    # Test 11: Digital Forensic Chain-of-Custody SHA-256 Hash
    # -------------------------------------------------------------
    print("\n[TEST 11] Digital Forensic Evidence Hash & WebSocket Payload Integrity...")
    with client.websocket_connect("/ws/alerts") as ws:
        notify_emergency(
            latitude=17.4485,
            longitude=78.3758,
            extra_data={
                "accident_id": "forensic_test_01",
                "severity_level": "CRITICAL_TRAUMA",
                "evidence_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "location_name": "Cyber Towers Junction"
            }
        )
        msg = ws.receive_text()
        payload = json.loads(msg)
        assert payload["severity_level"] == "CRITICAL_TRAUMA"
        assert payload["evidence_hash"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert "nearest_facilities" in payload
        assert payload["nearest_facilities"] is not None
        print("  ✅ Forensic SHA-256 integrity hash & triage rating broadcast verified")

    print("\n==================================================================")
    print("🎉 ALL 11 END-TO-END VERIFICATION TESTS PASSED SUCCESSFULLY! 🎉")
    print("==================================================================")


if __name__ == "__main__":
    run_full_suite()
