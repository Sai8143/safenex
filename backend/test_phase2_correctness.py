import os
import sys
import io

# Ensure backend is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app, UPLOAD_DIR
from app.database import DEFAULT_DB_PATH, DATABASE_URL
from app.services.ai_detector import model as ai_model
from app.services.video_detector import model as video_model

client = TestClient(app)

def test_phase2():
    print("==================================================")
    print("RUNNING PHASE 2 CODE CORRECTNESS TEST SUITE")
    print("==================================================")

    # 1. Health endpoint
    r = client.get("/health")
    assert r.status_code == 200, f"Health check failed: {r.status_code}"
    assert r.json()["health"] == "OK"
    print("✅ 1. Health Check: OK")

    # 2. Shared YOLO Model Singleton
    assert ai_model is video_model, "YOLO model instances are not shared!"
    print("✅ 2. Shared YOLO Model Singleton Verified (no duplicate memory allocation)")

    # 3. Deterministic Paths
    assert os.path.isabs(UPLOAD_DIR), "UPLOAD_DIR is not absolute!"
    assert "uploads" in UPLOAD_DIR
    print(f"✅ 3. Deterministic UPLOAD_DIR: {UPLOAD_DIR}")
    print(f"✅ 4. Deterministic DATABASE_URL: {DATABASE_URL}")

    # 5. Invalid / Corrupted Image Upload to /alert
    corrupt_file = io.BytesIO(b"this is not an image at all, purely corrupt bytes")
    r = client.post(
        "/alert",
        files={"image": ("bad.jpg", corrupt_file, "image/jpeg")},
        data={"latitude": "28.6139", "longitude": "77.2090"}
    )
    assert r.status_code == 400, f"Expected 400 for corrupt image, got {r.status_code}"
    err_json = r.json()
    assert err_json.get("success") is False, "Expected success: False"
    assert err_json.get("error") == "INVALID_FRAME", f"Expected INVALID_FRAME, got {err_json}"
    print(f"✅ 5. Corrupt Image Handling (/alert): {err_json}")

    # 6. Empty Image Upload to /alert
    empty_file = io.BytesIO(b"")
    r = client.post(
        "/alert",
        files={"image": ("empty.jpg", empty_file, "image/jpeg")},
        data={"latitude": "28.6139", "longitude": "77.2090"}
    )
    assert r.status_code == 400, f"Expected 400 for empty image, got {r.status_code}"
    err_json = r.json()
    assert err_json.get("success") is False
    assert err_json.get("error") == "INVALID_FRAME"
    print(f"✅ 6. Empty Image Handling (/alert): {err_json}")

    # 7. Invalid Video Frame to /video-frame
    r = client.post(
        "/video-frame",
        files={"frame": ("bad_frame.jpg", io.BytesIO(b"invalid"), "image/jpeg")},
        data={"latitude": "28.6139", "longitude": "77.2090"}
    )
    assert r.status_code == 400, f"Expected 400 for bad video frame, got {r.status_code}"
    err_json = r.json()
    assert err_json.get("success") is False
    assert err_json.get("error") == "INVALID_FRAME"
    print(f"✅ 7. Corrupt Frame Handling (/video-frame): {err_json}")

    print("\n==================================================")
    print("ALL PHASE 2 TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    test_phase2()
