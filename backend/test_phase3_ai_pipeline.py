import os
import sys
import cv2
import numpy as np

# Ensure backend is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.services.tracker import CentroidVehicleTracker
from app.services.temporal_filter import TemporalStreamVerifier
from app.services.decision_engine import DecisionEngine, AccidentDecision

client = TestClient(app)

def create_synthetic_frame(boxes, damage=False):
    """Generates synthetic 640x480 frame with specified vehicle rectangles."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Background asphalt
    cv2.rectangle(img, (0, 0), (640, 480), (60, 60, 60), -1)

    for idx, (x1, y1, x2, y2) in enumerate(boxes):
        color = (255, 120, 0) if idx % 2 == 0 else (0, 100, 255)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)
        if damage:
            # Crinkle / scratch texture lines
            for _ in range(40):
                lx1 = np.random.randint(x1, x2)
                ly1 = np.random.randint(y1, y2)
                cv2.line(img, (lx1, ly1), (lx1 + 15, ly1 + 15), (255, 255, 255), 2)

    return img


def test_tracker():
    print("Testing CentroidVehicleTracker...")
    tracker = CentroidVehicleTracker(max_distance=90.0)

    # Frame 1: Vehicle at (100, 100, 180, 180)
    tracks = tracker.update([(100, 100, 180, 180)], ["car"], [0.9])
    assert len(tracks) == 1
    t1_id = tracks[0].track_id

    # Frame 2: Vehicle moves to (115, 100, 195, 180) (shift = 15 pixels)
    tracks = tracker.update([(115, 100, 195, 180)], ["car"], [0.9])
    assert len(tracks) == 1
    assert tracks[0].track_id == t1_id
    assert tracks[0].velocities[-1] > 10.0
    assert tracks[0].stopped_frames == 0

    # Frame 3: Vehicle stops at (115, 100, 195, 180) (shift = 0)
    tracks = tracker.update([(115, 100, 195, 180)], ["car"], [0.9])
    assert tracks[0].stopped_frames == 1

    # Frame 4: Still stopped
    tracks = tracker.update([(115, 100, 195, 180)], ["car"], [0.9])
    assert tracks[0].stopped_frames == 2
    print("✅ CentroidVehicleTracker: ID association, velocity & stop detection OK")


def test_temporal_verifier():
    print("Testing TemporalStreamVerifier...")
    verifier = TemporalStreamVerifier(window_size=7)

    # 1 single frame of overlap -> should NOT be confirmed
    res1 = verifier.add_frame_assessment(
        has_overlap=True,
        max_iou=0.18,
        damage_score=0.45,
        confidence=0.60
    )
    assert not res1["is_confirmed"], "Single frame must NOT confirm accident!"
    assert res1["is_potential"], "Single frame should be marked potential"

    # Frame 2 of overlap -> still not confirmed
    res2 = verifier.add_frame_assessment(
        has_overlap=True,
        max_iou=0.20,
        damage_score=0.45,
        confidence=0.65
    )
    assert not res2["is_confirmed"], "Two frames must NOT confirm accident (minimum 3 required)!"

    # Frame 3 of overlap + abnormal stop -> now CONFIRMED
    res3 = verifier.add_frame_assessment(
        has_overlap=True,
        max_iou=0.22,
        damage_score=0.50,
        confidence=0.70,
        has_abnormal_stop=True
    )
    assert res3["is_confirmed"], "Three persistent collision frames with stop must CONFIRM accident!"
    print("✅ TemporalStreamVerifier: Multi-frame persistence and confirmation OK")


def test_decision_engine():
    print("Testing DecisionEngine...")

    # Clear scene
    clear_eval = DecisionEngine.evaluate(vehicle_count=0, max_iou=0.0, damage_score=0.0, confidence=0.0)
    assert clear_eval["decision"] == AccidentDecision.NORMAL_TRAFFIC
    assert not clear_eval["should_notify"]

    # Normal traffic: two cars waiting at red light or in traffic (low overlap, no damage)
    normal_eval = DecisionEngine.evaluate(
        vehicle_count=2,
        max_iou=0.08,
        damage_score=0.12,
        confidence=0.30
    )
    assert normal_eval["decision"] == AccidentDecision.NORMAL_TRAFFIC
    assert not normal_eval["should_notify"]

    # Stream mode with non-confirmed temporal data
    temp_unconfirmed = {"is_confirmed": False, "is_potential": True, "avg_confidence": 0.40}
    stream_eval = DecisionEngine.evaluate(
        vehicle_count=2,
        max_iou=0.15,
        damage_score=0.30,
        confidence=0.45,
        temporal_data=temp_unconfirmed,
        is_stream=True
    )
    assert stream_eval["decision"] == AccidentDecision.POSSIBLE_INCIDENT
    assert not stream_eval["should_notify"], "Unconfirmed stream must NOT notify emergency!"

    # Stream mode with confirmed temporal data
    temp_confirmed = {"is_confirmed": True, "is_potential": False, "avg_confidence": 0.75, "consecutive_collisions": 4}
    stream_conf_eval = DecisionEngine.evaluate(
        vehicle_count=2,
        max_iou=0.35,
        damage_score=0.55,
        confidence=0.75,
        temporal_data=temp_confirmed,
        is_stream=True
    )
    assert stream_conf_eval["decision"] == AccidentDecision.CONFIRMED_ACCIDENT
    assert stream_conf_eval["should_notify"], "Confirmed accident MUST notify emergency!"
    print("✅ DecisionEngine: Normal / Potential / Confirmed state transitions OK")


def test_api_false_positive_suppression():
    print("Testing False Positive Suppression on /video-frame...")
    # Normal empty road frame
    road_img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(road_img, (0, 0), (640, 480), (80, 80, 80), -1)
    _, enc = cv2.imencode(".jpg", road_img)

    r = client.post(
        "/video-frame",
        files={"frame": ("road.jpg", enc.tobytes(), "image/jpeg")},
        data={"latitude": "28.6139", "longitude": "77.2090"}
    )
    assert r.status_code == 200
    res = r.json()
    assert res["status"] in ["normal", "potential"]
    assert "No accident detected" in res["message"] or "observing" in res["message"]
    print("✅ API Video Frame: Normal scene processed with zero false-alarm alert")


def run_all_phase3_tests():
    print("==================================================")
    print("RUNNING PHASE 3 AI DETECTION & DECISION TESTS")
    print("==================================================")
    test_tracker()
    test_temporal_verifier()
    test_decision_engine()
    test_api_false_positive_suppression()
    print("==================================================")
    print("ALL PHASE 3 TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    run_all_phase3_tests()
