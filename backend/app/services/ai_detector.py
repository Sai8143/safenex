import os
os.environ["YOLO_VERBOSE"] = "False"
import cv2
import hashlib
import numpy as np
from ultralytics import YOLO
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

# Robust model path resolution
def _resolve_model_path():
    candidates = [
        "yolov8n.pt",
        os.path.join("backend", "yolov8n.pt"),
        os.path.join(os.path.dirname(__file__), "..", "..", "yolov8n.pt"),
        os.path.join(os.path.dirname(__file__), "..", "yolov8n.pt")
    ]
    for path in candidates:
        if os.path.exists(path):
            return os.path.abspath(path)
    return "yolov8n.pt"

model = YOLO(_resolve_model_path())

# COCO vehicle classes: bicycle(1), car(2), motorcycle(3), bus(5), train(6), truck(7)
VEHICLE_CLASSES = [1, 2, 3, 5, 6, 7]


def compute_iou(boxA, boxB):
    """Compute Intersection over Union (IoU)"""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter = max(0, xB - xA) * max(0, yB - yA)
    if inter == 0:
        return 0.0

    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    return inter / float(areaA + areaB - inter)


def compute_roi_damage_score(roi) -> float:
    """
    Computes ROI damage score (0.0 to 1.0) based on edge density,
    contour complexity, and texture variance.
    """
    if roi is None or roi.size == 0:
        return 0.0

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(blur, 90, 200)
    edge_density = np.count_nonzero(edges) / float(edges.size)

    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    large_contours = [
        c for c in contours if cv2.contourArea(c) > 0.008 * roi.size
    ]

    texture_variance = np.var(gray)

    score = 0.0
    if edge_density > 0.12:
        score += 0.40
    if texture_variance > 550:
        score += 0.35
    if len(large_contours) >= 2:
        score += 0.25

    return min(score, 1.0)


def detect_vehicles_multiscale(frame):
    """
    Multi-scale vehicle detection.
    Pass 1: Full frame scan (conf=0.10)
    Pass 2: Central zoom scan (conf=0.08) for small/screen-captured vehicles
    """
    h, w = frame.shape[:2]
    boxes = []
    class_names = []
    confidences = []

    # Pass 1: Full frame sensitive scan
    res_full = model(frame, conf=0.05, classes=VEHICLE_CLASSES)
    for r in res_full:
        for box in r.boxes:
            b = tuple(map(int, box.xyxy[0]))
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            boxes.append(b)
            class_names.append(model.names.get(cls_id, "Vehicle"))
            confidences.append(conf)

    # Pass 2: Central zoom scan (focus on inner screen / road center)
    y1_crop, y2_crop = int(h * 0.05), int(h * 0.95)
    x1_crop, x2_crop = int(w * 0.05), int(w * 0.95)
    crop_frame = frame[y1_crop:y2_crop, x1_crop:x2_crop]

    if crop_frame.size > 0:
        res_crop = model(crop_frame, conf=0.04, classes=VEHICLE_CLASSES)
        for r in res_crop:
            for box in r.boxes:
                cb = tuple(map(int, box.xyxy[0]))
                b = (cb[0] + x1_crop, cb[1] + y1_crop, cb[2] + x1_crop, cb[3] + y1_crop)
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])

                is_dup = False
                for existing in boxes:
                    if compute_iou(existing, b) > 0.35:
                        is_dup = True
                        break
                if not is_dup:
                    boxes.append(b)
                    class_names.append(model.names.get(cls_id, "Vehicle"))
                    confidences.append(conf)

    return boxes, class_names, confidences


def analyze_image_accident(
    image_path: str,
    upload_dir: str = "uploads",
    temporal_data: Optional[dict] = None,
    is_stream: bool = False
):
    """
    Multi-stage high-precision AI accident detector with multi-scale vehicle detection.
    """
    frame = cv2.imread(image_path)
    if frame is None:
        return {
            "is_accident": False,
            "confidence_score": 0.0,
            "annotated_filename": None,
            "details": "Failed to read image frame"
        }

    h, w = frame.shape[:2]
    annotated_frame = frame.copy()

    # Multi-scale sensitive vehicle detection
    boxes, class_names, confidences = detect_vehicles_multiscale(frame)

    # Draw detected vehicle bounding boxes (Bright Green)
    for idx, (x1, y1, x2, y2) in enumerate(boxes):
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            annotated_frame,
            f"{class_names[idx]} {confidences[idx]:.2f}",
            (x1, max(y1 - 6, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 0),
            2
        )

    max_collision_iou = 0.0
    highest_damage_score = 0.0
    overlapping_pairs = []

    # Vehicle Overlaps & Individual Damage
    if len(boxes) >= 2:
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                iou_val = compute_iou(boxes[i], boxes[j])
                if iou_val > max_collision_iou:
                    max_collision_iou = iou_val

                if iou_val > 0.08:
                    overlapping_pairs.append((boxes[i], boxes[j]))
                    x1 = min(boxes[i][0], boxes[j][0])
                    y1 = min(boxes[i][1], boxes[j][1])
                    x2 = max(boxes[i][2], boxes[j][2])
                    y2 = max(boxes[i][3], boxes[j][3])
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(
                        annotated_frame,
                        f"COLLISION ZONE (IoU: {iou_val:.2f})",
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2
                    )

                for (rx1, ry1, rx2, ry2) in [boxes[i], boxes[j]]:
                    roi = frame[ry1:ry2, rx1:rx2]
                    d_score = compute_roi_damage_score(roi)
                    if d_score > highest_damage_score:
                        highest_damage_score = d_score

    # Single vehicle damage check
    if len(boxes) == 1:
        rx1, ry1, rx2, ry2 = boxes[0]
        roi = frame[ry1:ry2, rx1:rx2]
        highest_damage_score = compute_roi_damage_score(roi)

    # Fallback full-scene crash analysis
    scene_damage_score = compute_roi_damage_score(frame)

    if not boxes:
        cx1, cy1, cx2, cy2 = int(w * 0.15), int(h * 0.15), int(w * 0.85), int(h * 0.85)
        cv2.rectangle(annotated_frame, (cx1, cy1), (cx2, cy2), (255, 165, 0), 2)
        cv2.putText(
            annotated_frame,
            f"SCENE DAMAGE SCAN (Score: {scene_damage_score:.2f})",
            (cx1, cy1 - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 165, 0),
            2
        )

    # Confidence calculation
    if len(boxes) >= 2:
        confidence = (max_collision_iou * 0.4) + (highest_damage_score * 0.6)
    elif len(boxes) == 1:
        confidence = (highest_damage_score * 0.7) + (scene_damage_score * 0.3)
    else:
        confidence = scene_damage_score * 0.85

    from app.services.decision_engine import DecisionEngine, AccidentDecision

    # Pass assessment to Decision Engine
    decision_info = DecisionEngine.evaluate(
        vehicle_count=len(boxes),
        max_iou=max_collision_iou,
        damage_score=highest_damage_score,
        confidence=confidence,
        temporal_data=temporal_data if "temporal_data" in locals() else None,
        is_stream=is_stream if "is_stream" in locals() else False
    )

    is_confirmed = decision_info["is_confirmed"]
    is_potential = decision_info["is_potential"]
    decision = decision_info["decision"]

    # Status Overlay Banner on top of image
    if is_confirmed:
        banner_color = (0, 0, 255)  # Red
        status_label = "CRASH CONFIRMED"
    elif is_potential:
        banner_color = (0, 165, 255)  # Orange
        status_label = "POSSIBLE INCIDENT"
    else:
        banner_color = (0, 200, 0)  # Green
        status_label = "NORMAL TRAFFIC"

    status_text = f"AcciSense AI: {status_label} (Vehicles: {len(boxes)} | Conf: {confidence*100:.0f}%)"
    cv2.rectangle(annotated_frame, (0, 0), (w, 42), banner_color, -1)
    cv2.putText(
        annotated_frame,
        status_text,
        (15, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    # Save annotated evidence image
    annotated_filename = f"annotated_{os.path.basename(image_path)}"
    os.makedirs(upload_dir, exist_ok=True)
    annotated_path = os.path.join(upload_dir, annotated_filename)
    cv2.imwrite(annotated_path, annotated_frame)

    # Forensic Chain-of-Custody SHA-256 Hash
    try:
        with open(image_path, "rb") as ef:
            evidence_hash = hashlib.sha256(ef.read()).hexdigest()
    except Exception:
        evidence_hash = ""

    severity_level = decision_info.get("severity_level", "NONE")

    details_str = (
        f"Decision: {decision.value} ({decision_info['reason']}) | "
        f"Vehicles: {len(boxes)} | Max Collision IoU: {max_collision_iou:.2f} | "
        f"Vehicle Damage: {highest_damage_score:.2f} | Scene Damage: {scene_damage_score:.2f}"
    )

    return {
        "is_accident": is_confirmed,
        "is_potential": is_potential,
        "decision": decision.value,
        "confidence_score": confidence,
        "severity_level": severity_level,
        "evidence_hash": evidence_hash,
        "annotated_filename": annotated_filename,
        "details": details_str,
        "should_notify": decision_info["should_notify"],
        "max_collision_iou": max_collision_iou,
        "vehicle_count": len(boxes),
        "damage_score": highest_damage_score
    }

def detect_potential_accident(image_path: str) -> bool:
    """Backward compatibility helper"""
    res = analyze_image_accident(image_path)
    return res["is_accident"]



