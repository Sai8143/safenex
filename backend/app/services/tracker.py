import numpy as np
from typing import Dict, List, Tuple, Optional

class VehicleTrack:
    def __init__(self, track_id: int, bbox: Tuple[int, int, int, int], class_name: str, confidence: float):
        self.track_id = track_id
        self.bbox = bbox  # (x1, y1, x2, y2)
        self.class_name = class_name
        self.confidence = confidence
        self.history: List[Tuple[float, float]] = [self._centroid(bbox)]
        self.velocities: List[float] = [0.0]
        self.missed_frames = 0
        self.stopped_frames = 0

    @staticmethod
    def _centroid(b: Tuple[int, int, int, int]) -> Tuple[float, float]:
        return ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)

    def update(self, bbox: Tuple[int, int, int, int], confidence: float):
        self.bbox = bbox
        self.confidence = confidence
        self.missed_frames = 0

        c_new = self._centroid(bbox)
        c_prev = self.history[-1]
        dist = float(np.hypot(c_new[0] - c_prev[0], c_new[1] - c_prev[1]))

        self.history.append(c_new)
        if len(self.history) > 15:
            self.history.pop(0)

        self.velocities.append(dist)
        if len(self.velocities) > 15:
            self.velocities.pop(0)

        # Detect if vehicle is nearly motionless (< 2.5 pixels shift per frame)
        if dist < 2.5:
            self.stopped_frames += 1
        else:
            self.stopped_frames = 0

    def mark_missed(self):
        self.missed_frames += 1


class CentroidVehicleTracker:
    """
    Lightweight, deterministic multi-vehicle tracker.
    Associates bounding boxes across frames via spatial centroid Euclidean distance.
    """
    def __init__(self, max_distance: float = 85.0, max_missed: int = 5):
        self.max_distance = max_distance
        self.max_missed = max_missed
        self.next_id = 1
        self.tracks: Dict[int, VehicleTrack] = {}

    def update(
        self,
        detections: List[Tuple[int, int, int, int]],
        class_names: List[str],
        confidences: List[float]
    ) -> List[VehicleTrack]:
        if not detections:
            to_del = []
            for tid, trk in self.tracks.items():
                trk.mark_missed()
                if trk.missed_frames > self.max_missed:
                    to_del.append(tid)
            for tid in to_del:
                del self.tracks[tid]
            return list(self.tracks.values())

        if not self.tracks:
            for b, cls_n, conf in zip(detections, class_names, confidences):
                self.tracks[self.next_id] = VehicleTrack(self.next_id, b, cls_n, conf)
                self.next_id += 1
            return list(self.tracks.values())

        track_ids = list(self.tracks.keys())
        track_centroids = [self.tracks[tid].history[-1] for tid in track_ids]
        det_centroids = [VehicleTrack._centroid(b) for b in detections]

        cost_matrix = np.zeros((len(track_ids), len(detections)))
        for i, tc in enumerate(track_centroids):
            for j, dc in enumerate(det_centroids):
                cost_matrix[i, j] = np.hypot(tc[0] - dc[0], tc[1] - dc[1])

        matched_tracks = set()
        matched_dets = set()

        if cost_matrix.size > 0:
            for _ in range(min(len(track_ids), len(detections))):
                min_idx = np.unravel_index(np.argmin(cost_matrix), cost_matrix.shape)
                val = cost_matrix[min_idx]
                if val > self.max_distance:
                    break
                t_idx, d_idx = min_idx
                cost_matrix[t_idx, :] = 1e6
                cost_matrix[:, d_idx] = 1e6

                matched_tracks.add(track_ids[t_idx])
                matched_dets.add(d_idx)

                self.tracks[track_ids[t_idx]].update(detections[d_idx], confidences[d_idx])

        for d_idx, (b, cls_n, conf) in enumerate(zip(detections, class_names, confidences)):
            if d_idx not in matched_dets:
                self.tracks[self.next_id] = VehicleTrack(self.next_id, b, cls_n, conf)
                self.next_id += 1

        to_del = []
        for tid in track_ids:
            if tid not in matched_tracks:
                self.tracks[tid].mark_missed()
                if self.tracks[tid].missed_frames > self.max_missed:
                    to_del.append(tid)

        for tid in to_del:
            del self.tracks[tid]

        return list(self.tracks.values())
