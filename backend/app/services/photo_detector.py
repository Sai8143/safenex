from app.services.ai_detector import analyze_image_accident

def detect_photo_accident_score(image_path: str) -> float:
    """
    Returns accident likelihood score (0.0 – 1.0)
    """
    res = analyze_image_accident(image_path)
    return res["confidence_score"]

