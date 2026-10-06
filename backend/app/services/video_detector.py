import os
import cv2
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

from app.services.ai_detector import model, VEHICLE_CLASSES, compute_iou, compute_roi_damage_score, _resolve_model_path
from app.services.tracker import CentroidVehicleTracker
from app.services.temporal_filter import TemporalStreamVerifier
from app.services.decision_engine import DecisionEngine, AccidentDecision

class StreamSessionTracker:
    """
    Session-isolated stream tracker integrating:
    1. Multi-scale YOLO vehicle detection
    2. Centroid multi-object vehicle tracking with speed & abnormal stop detection
    3. Spatial collision overlap & structural deformation scoring
    4. Multi-frame temporal persistence verification
    5. Authoritative decision engine evaluation
    """
    def __init__(self, session_id: str = "default_stream", window_size: int = 7):
        self.session_id = session_id
        self.vehicle_tracker = CentroidVehicleTracker(max_distance=85.0, max_missed=5)
        self.temporal_verifier = TemporalStreamVerifier(window_size=window_size)
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=200, varThreshold=32, detectShadows=False
        )

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        if frame is None or frame.size == 0:
            return {
                "is_accident": False,
                "is_potential": False,
                "decision": AccidentDecision.NORMAL_TRAFFIC.value,
                "confidence": 0.0,
                "max_iou": 0.0,
                "tracks_count": 0,
                "reason": "Empty or invalid frame",
                "should_notify": False
            }

        h, w = frame.shape[:2]
        resized = cv2.resize(frame, (640, 480))

        # 1. Background subtraction for gross motion disruption
        fg_mask = self.bg_subtractor.apply(resized)
        fg_mask = cv2.medianBlur(fg_mask, 5)
        fg_pixels = cv2.countNonZero(fg_mask)
        fg_ratio = fg_pixels / float(fg_mask.size)

        # 2. Vehicle detection
        results = model(resized, conf=0.25, classes=VEHICLE_CLASSES)
        boxes: List[Tuple[int, int, int, int]] = []
        class_names: List[str] = []
        confidences: List[float] = []

        for r in results:
            for box in r.boxes:
                b = tuple(map(int, box.xyxy[0]))
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                boxes.append(b)
                class_names.append(model.names.get(cls_id, "Vehicle"))
                confidences.append(conf)

        # 3. Vehicle Tracking & Kinematics
        active_tracks = self.vehicle_tracker.update(boxes, class_names, confidences)
        abnormal_stopped = any(t.stopped_frames >= 2 and len(t.velocities) >= 3 for t in active_tracks)

        # 4. Proximity & Structural Damage
        max_iou = 0.0
        max_damage = 0.0
        has_overlap = False

        if len(boxes) >= 2:
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    iou_val = compute_iou(boxes[i], boxes[j])
                    if iou_val > max_iou:
                        max_iou = iou_val
                    if iou_val >= 0.12:
                        has_overlap = True

                # Inspect ROI damage
                rx1, ry1, rx2, ry2 = boxes[i]
                roi = resized[ry1:ry2, rx1:rx2]
                d = compute_roi_damage_score(roi)
                if d > max_damage:
                    max_damage = d
        elif len(boxes) == 1:
            rx1, ry1, rx2, ry2 = boxes[0]
            roi = resized[ry1:ry2, rx1:rx2]
            max_damage = compute_roi_damage_score(roi)

        frame_confidence = round(
            min(max((max_iou * 0.45) + (max_damage * 0.55), 0.0), 1.0), 2
        )

        # 5. Temporal Verification over sliding window
        temporal_result = self.temporal_verifier.add_frame_assessment(
            has_overlap=has_overlap,
            max_iou=max_iou,
            damage_score=max_damage,
            confidence=frame_confidence,
            has_abnormal_stop=abnormal_stopped
        )

        # 6. Decision Engine Evaluation
        decision_info = DecisionEngine.evaluate(
            vehicle_count=len(boxes),
            max_iou=max_iou,
            damage_score=max_damage,
            confidence=frame_confidence,
            temporal_data=temporal_result,
            is_stream=True
        )

        return {
            "is_accident": decision_info["is_confirmed"],
            "is_potential": decision_info["is_potential"],
            "decision": decision_info["decision"].value,
            "confidence": decision_info["confidence"],
            "max_iou": max_iou,
            "damage_score": max_damage,
            "tracks_count": len(active_tracks),
            "severity_level": decision_info.get("severity_level", "NONE"),
            "temporal_data": temporal_result,
            "reason": decision_info["reason"],
            "should_notify": decision_info["should_notify"]
        }


# Global default tracker for single-frame calls
_default_tracker = StreamSessionTracker(session_id="global_default")

def detect_video_accident(frame) -> bool:
    """
    CCTV-based accident detection for individual video frames.
    Returns True only when confirmed by temporal decision engine.
    """
    res = _default_tracker.process_frame(frame)
    return res["is_accident"]
