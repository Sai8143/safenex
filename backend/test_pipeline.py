import os
import sys
import time
import requests
import cv2
import numpy as np

BASE_URL = "http://127.0.0.1:8000"

def create_synthetic_car_image(filepath="test_crash.jpg"):
    """Generates a synthetic image simulating two overlapping vehicle shapes."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Background road
    cv2.rectangle(img, (0, 100), (640, 480), (50, 50, 50), -1)
    # Vehicle 1 (Blue rectangle)
    cv2.rectangle(img, (200, 200), (380, 320), (255, 100, 0), -1)
    # Vehicle 2 overlapping (Red rectangle)
    cv2.rectangle(img, (320, 220), (480, 340), (0, 0, 255), -1)
    # Texture/damage marks
    for _ in range(30):
        x1 = np.random.randint(280, 380)
        y1 = np.random.randint(200, 320)
        x2 = x1 + np.random.randint(-20, 20)
        y2 = y1 + np.random.randint(-20, 20)
        cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), 2)

    cv2.imwrite(filepath, img)
    return filepath

def run_tests():
    print("==================================================")
    print("[TEST] Running AcciSense Automated Integration Suite")
    print("==================================================")

    # 1. Health check
    try:
        r = requests.get(f"{BASE_URL}/health")
        print(f"1. Health Check: {r.status_code} | {r.json()}")
        assert r.status_code == 200
    except Exception as e:
        print(f"[FAIL] Server connection failed. Is FastAPI running on {BASE_URL}? Error: {e}")
        return False

    # 2. Synthetic Photo Alert Test
    test_img_path = create_synthetic_car_image()
    try:
        with open(test_img_path, "rb") as f:
            files = {"image": ("test_crash.jpg", f, "image/jpeg")}
            data = {
                "latitude": "28.6139",
                "longitude": "77.2090",
                "location_name": "Connaught Place Traffic Junction"
            }
            r = requests.post(f"{BASE_URL}/alert", files=files, data=data)
            print(f"2. Photo Alert Submit: {r.status_code}")
            res_json = r.json()
            print(f"   Response status: {res_json.get('status')} | confidence: {res_json.get('confidence_score')}")
            accident_id = res_json.get("id")
            annotated_img = res_json.get("annotated_image")
    finally:
        if os.path.exists(test_img_path):
            os.remove(test_img_path)

    # 3. Fetch Accidents List
    r = requests.get(f"{BASE_URL}/api/accidents")
    print(f"3. GET /api/accidents: {r.status_code} | Records count: {len(r.json())}")
    assert r.status_code == 200

    # 4. Status Update Test
    if accident_id:
        r = requests.patch(f"{BASE_URL}/api/accidents/{accident_id}/status", json={"status": "dispatched"})
        print(f"4. Status Update (Dispatched): {r.status_code} | {r.json()}")

    # 5. System Stats Test
    r = requests.get(f"{BASE_URL}/api/stats")
    print(f"5. GET /api/stats: {r.status_code} | {r.json()}")

    # 6. Verify Static Evidence Image Access
    if annotated_img:
        r = requests.get(f"{BASE_URL}/uploads/{annotated_img}")
        print(f"6. Evidence Image Access: {r.status_code} | Size: {len(r.content)} bytes")
        assert r.status_code == 200

    print("\n==================================================")
    print("[SUCCESS] All Integration Tests Passed Successfully!")
    print("==================================================")
    return True

if __name__ == "__main__":
    run_tests()
