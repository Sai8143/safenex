import os
import sys
import json
import pytest

# Ensure backend is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Accident, AccidentLifecycle
from app.services.notifier import notify_emergency
from app.services.websocket_manager import ws_manager

client = TestClient(app)

def test_database_lifecycle():
    print("Testing Database Accident Lifecycle...")
    db = SessionLocal()
    try:
        # Create test accident with CONFIRMED status
        acc = Accident(
            latitude=17.3850,
            longitude=78.4867,
            location_name="Hyderabad Hitec Junction",
            image_path="test_raw.jpg",
            annotated_image="test_annotated.jpg",
            accident_type="video",
            status=AccidentLifecycle.CONFIRMED.value,
            confidence_score=0.94,
            details="Temporal multi-frame collision confirmed"
        )
        db.add(acc)
        db.commit()
        db.refresh(acc)
        acc_id = acc.id
        assert acc_id is not None

        # Verify via GET /api/accidents/{id}
        r = client.get(f"/api/accidents/{acc_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "CONFIRMED"
        assert data["location_name"] == "Hyderabad Hitec Junction"

        # Update status to AMBULANCE_EN_ROUTE
        r = client.patch(
            f"/api/accidents/{acc_id}/status",
            json={"status": AccidentLifecycle.AMBULANCE_EN_ROUTE.value}
        )
        assert r.status_code == 200
        assert r.json()["status"] == AccidentLifecycle.AMBULANCE_EN_ROUTE.value

        # Update status to RESOLVED
        r = client.patch(
            f"/api/accidents/{acc_id}/status",
            json={"status": AccidentLifecycle.RESOLVED.value}
        )
        assert r.status_code == 200
        assert r.json()["status"] == AccidentLifecycle.RESOLVED.value

        # Clean up
        db.delete(acc)
        db.commit()
        print("✅ Database Accident Lifecycle: Insertion, Retrieval, Status Updates OK")
    finally:
        db.close()


def test_system_stats():
    print("Testing /api/stats...")
    r = client.get("/api/stats")
    assert r.status_code == 200
    stats = r.json()
    assert "total_accidents" in stats
    assert "confirmed_count" in stats
    assert "dispatched_count" in stats
    assert "resolved_count" in stats
    print(f"✅ System Stats API OK: {stats}")


def test_websocket_emergency_payload():
    print("Testing WebSocket Emergency Payload Delivery...")
    with client.websocket_connect("/ws/alerts") as ws:
        # Trigger emergency notification
        payload = notify_emergency(
            latitude=17.3850,
            longitude=78.4867,
            extra_data={
                "accident_id": "test_ws_42",
                "location_name": "Hyderabad Cyber Gateway",
                "confidence_score": 0.95,
                "accident_type": "collision",
                "annotated_image": "annotated_sample.jpg"
            }
        )

        # Receive from WebSocket
        msg = ws.receive_text()
        rec_data = json.loads(msg)

        # Verify Section 8 Structured Keys
        assert rec_data["event"] == "ACCIDENT_CONFIRMED"
        assert rec_data["accident_id"] == "test_ws_42"
        assert rec_data["latitude"] == 17.3850
        assert rec_data["longitude"] == 78.4867
        assert rec_data["confidence"] == 0.95
        assert rec_data["accident_type"] == "collision"
        assert rec_data["annotated_image"] == "annotated_sample.jpg"
        assert rec_data["status"] == "CONFIRMED"

        # Verify backward-compatibility keys
        assert rec_data["type"] == "ACCIDENT_ALERT"
        assert "formatted_message" in rec_data
        print("✅ WebSocket Emergency Payload: Section 8 Specification & Delivery Verified")


def run_all_phase4_tests():
    print("==================================================")
    print("RUNNING PHASE 4 DATABASE & WEBSOCKET TESTS")
    print("==================================================")
    test_database_lifecycle()
    test_system_stats()
    test_websocket_emergency_payload()
    print("==================================================")
    print("ALL PHASE 4 TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    run_all_phase4_tests()
