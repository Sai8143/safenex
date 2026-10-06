from enum import Enum
from typing import Dict, Any, Optional

class AccidentDecision(str, Enum):
    NORMAL_TRAFFIC = "NORMAL_TRAFFIC"
    POSSIBLE_INCIDENT = "POSSIBLE_INCIDENT"
    CONFIRMED_ACCIDENT = "CONFIRMED_ACCIDENT"

    # Aliases for backward compatibility
    NO_ACCIDENT = "NORMAL_TRAFFIC"
    POTENTIAL_ACCIDENT = "POSSIBLE_INCIDENT"


class DecisionEngine:
    """
    Central authority for validating and classifying traffic incidents.
    Enforces strict differentiation between:
    - NORMAL_TRAFFIC (flowing traffic, red light queues, close passing)
    - POSSIBLE_INCIDENT (sudden braking, single-frame overlap, slight proximity)
    - CONFIRMED_ACCIDENT (sustained spatial crash, kinetic halt, surface deformation)

    Also computes Medical Triage & Impact Severity:
    - CRITICAL_TRAUMA (High-velocity deformation / severe crash)
    - MODERATE_COLLISION (Structural collision / multi-vehicle impact)
    - MINOR_INCIDENT (Low-speed scrape / bumper fender-bender)
    """

    @staticmethod
    def calculate_severity(max_iou: float, damage_score: float, confidence: float) -> str:
        """
        Calculates medical triage & traffic severity level.
        """
        composite_score = (max_iou * 0.40) + (damage_score * 0.45) + (confidence * 0.15)
        if composite_score >= 0.55 or damage_score >= 0.60:
            return "CRITICAL_TRAUMA"
        elif composite_score >= 0.30 or max_iou >= 0.18:
            return "MODERATE_COLLISION"
        return "MINOR_INCIDENT"

    @classmethod
    def evaluate(
        cls,
        vehicle_count: int,
        max_iou: float,
        damage_score: float,
        confidence: float,
        temporal_data: Optional[Dict[str, Any]] = None,
        is_stream: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate traffic state and make authoritative decision.
        """
        severity_level = cls.calculate_severity(max_iou, damage_score, confidence)

        # Scenario 1: Zero vehicles detected
        if vehicle_count == 0:
            if damage_score >= 0.75:
                return {
                    "decision": AccidentDecision.POSSIBLE_INCIDENT,
                    "is_confirmed": False,
                    "is_potential": True,
                    "confidence": round(damage_score * 0.6, 2),
                    "severity_level": "MINOR_INCIDENT",
                    "reason": "Roadway obstruction or severe surface debris detected without visible vehicles",
                    "should_notify": False
                }
            return {
                "decision": AccidentDecision.NORMAL_TRAFFIC,
                "is_confirmed": False,
                "is_potential": False,
                "confidence": 0.0,
                "severity_level": "NONE",
                "reason": "Clear roadway. No vehicles or incident indicators",
                "should_notify": False
            }

        # Scenario 2: Continuous video / CCTV stream mode
        if is_stream and temporal_data is not None:
            if temporal_data.get("is_confirmed", False):
                return {
                    "decision": AccidentDecision.CONFIRMED_ACCIDENT,
                    "is_confirmed": True,
                    "is_potential": False,
                    "confidence": temporal_data.get("avg_confidence", confidence),
                    "severity_level": severity_level,
                    "reason": (
                        f"Temporal collision confirmed across {temporal_data.get('consecutive_collisions', 0)} "
                        f"consecutive frames (Avg Conf: {temporal_data.get('avg_confidence', 0):.2f}) | Severity: {severity_level}"
                    ),
                    "should_notify": True
                }

            if temporal_data.get("is_potential", False):
                return {
                    "decision": AccidentDecision.POSSIBLE_INCIDENT,
                    "is_confirmed": False,
                    "is_potential": True,
                    "confidence": temporal_data.get("avg_confidence", confidence),
                    "severity_level": severity_level,
                    "reason": "Potential incident under multi-frame observation. Awaiting temporal confirmation.",
                    "should_notify": False
                }

            return {
                "decision": AccidentDecision.NORMAL_TRAFFIC,
                "is_confirmed": False,
                "is_potential": False,
                "confidence": 0.0,
                "severity_level": "NONE",
                "reason": "Normal vehicle movement and traffic flow",
                "should_notify": False
            }

        # Scenario 3: Single static image alert (Mobile App SOS photo)
        # Vehicles close together or slight overlap without surface damage is NOT a confirmed accident
        if max_iou > 0.0 and max_iou < 0.20 and damage_score < 0.35:
            return {
                "decision": AccidentDecision.NORMAL_TRAFFIC,
                "is_confirmed": False,
                "is_potential": False,
                "confidence": round(confidence * 0.4, 2),
                "severity_level": "NONE",
                "reason": "Vehicles in close proximity or lane queue without structural deformation",
                "should_notify": False
            }

        # Severe structural deformation + overlap or heavy impact evidence
        if (max_iou >= 0.25 and damage_score >= 0.40) or (damage_score >= 0.65 and confidence >= 0.60):
            return {
                "decision": AccidentDecision.CONFIRMED_ACCIDENT,
                "is_confirmed": True,
                "is_potential": False,
                "confidence": round(confidence, 2),
                "severity_level": severity_level,
                "reason": f"High-confidence collision impact with structural surface damage (Severity: {severity_level})",
                "should_notify": True
            }

        if max_iou >= 0.10 or damage_score >= 0.35 or confidence >= 0.45:
            return {
                "decision": AccidentDecision.POSSIBLE_INCIDENT,
                "is_confirmed": False,
                "is_potential": True,
                "confidence": round(confidence, 2),
                "severity_level": severity_level,
                "reason": "Possible collision candidate. Requires further verification.",
                "should_notify": False
            }

        return {
            "decision": AccidentDecision.NORMAL_TRAFFIC,
            "is_confirmed": False,
            "is_potential": False,
            "confidence": round(confidence, 2),
            "severity_level": "NONE",
            "reason": "Normal traffic scene",
            "should_notify": False
        }


# Legacy helper function
def decide(photo_result: bool, video_result: bool) -> AccidentDecision:
    if video_result:
        return AccidentDecision.CONFIRMED_ACCIDENT
    if photo_result:
        return AccidentDecision.POSSIBLE_INCIDENT
    return AccidentDecision.NORMAL_TRAFFIC
