from app.services.ai_detector import analyze_image_accident

def detect_crash(image_path: str) -> bool:
    """
    CCTV-based crash classifier (photo).
    Delegates to multi-tiered AI accident detector.
    """
    res = analyze_image_accident(image_path)
    return res["is_accident"]

