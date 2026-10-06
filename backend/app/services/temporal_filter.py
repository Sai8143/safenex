from collections import deque
import threading
from typing import Dict, Any, Optional

DEFAULT_WINDOW_SIZE = 7
COLLISION_PERSISTENCE_MIN = 3
CONFIDENCE_THRESHOLD = 0.55

class TemporalStreamVerifier:
    """
    Thread-safe temporal verifier tracking multi-frame accident evidence
    for a specific CCTV / camera stream.
    """
    def __init__(self, window_size: int = DEFAULT_WINDOW_SIZE):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)
        self.consecutive_collision_count = 0
        self.lock = threading.Lock()

    def add_frame_assessment(
        self,
        has_overlap: bool,
        max_iou: float,
        damage_score: float,
        confidence: float,
        has_abnormal_stop: bool = False
    ) -> Dict[str, Any]:
        """
        Record frame-level observation and return aggregated temporal metrics.
        """
        with self.lock:
            is_collision_candidate = has_overlap or (max_iou >= 0.10) or (damage_score >= 0.45)
            if is_collision_candidate:
                self.consecutive_collision_count += 1
            else:
                self.consecutive_collision_count = max(0, self.consecutive_collision_count - 1)

            entry = {
                "candidate": is_collision_candidate,
                "iou": max_iou,
                "damage": damage_score,
                "confidence": confidence,
                "abnormal_stop": has_abnormal_stop
            }
            self.history.append(entry)

            total_frames = len(self.history)
            candidate_frames = sum(1 for e in self.history if e["candidate"])
            abnormal_stops = sum(1 for e in self.history if e["abnormal_stop"])
            avg_confidence = (
                sum(e["confidence"] for e in self.history) / float(total_frames)
                if total_frames > 0 else 0.0
            )

            # Accident confirmed when collision candidates persist over multiple consecutive frames
            # along with substantial confidence or abnormal stopping following impact
            is_confirmed = (
                self.consecutive_collision_count >= COLLISION_PERSISTENCE_MIN and
                (avg_confidence >= CONFIDENCE_THRESHOLD or abnormal_stops >= 1 or damage_score >= 0.40)
            )

            is_potential = (
                self.consecutive_collision_count >= 1 or
                candidate_frames >= 2 or
                avg_confidence >= 0.35
            )

            return {
                "is_confirmed": is_confirmed,
                "is_potential": is_potential,
                "consecutive_collisions": self.consecutive_collision_count,
                "window_frames": total_frames,
                "candidate_frames": candidate_frames,
                "avg_confidence": round(avg_confidence, 2)
            }

    def reset(self):
        with self.lock:
            self.history.clear()
            self.consecutive_collision_count = 0


# Registry of session-isolated verifiers
_verifiers: Dict[str, TemporalStreamVerifier] = {}
_verifiers_lock = threading.Lock()

def get_temporal_verifier(session_id: str = "default") -> TemporalStreamVerifier:
    with _verifiers_lock:
        if session_id not in _verifiers:
            _verifiers[session_id] = TemporalStreamVerifier()
        return _verifiers[session_id]

def clear_temporal_verifier(session_id: str):
    with _verifiers_lock:
        _verifiers.pop(session_id, None)


# Backward-compatible global queue and helper
_legacy_scores = deque(maxlen=5)

def temporal_vote(score: float) -> bool:
    """Legacy helper for backward compatibility."""
    _legacy_scores.append(score)
    if len(_legacy_scores) == 1:
        return score >= 0.50
    positives = sum(1 for s in _legacy_scores if s >= 0.50)
    return positives >= (len(_legacy_scores) // 2 + 1)
