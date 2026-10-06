import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.lib.units import inch

def create_pdf(filename="AcciSense_Complete_Project_Speech_and_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#0f172a")
    c_accent = colors.HexColor("#ef4444")
    c_blue = colors.HexColor("#2563eb")
    c_dark = colors.HexColor("#1e293b")
    c_light = colors.HexColor("#f8fafc")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=c_primary,
        alignment=1,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=12,
        leading=16,
        textColor=c_accent,
        alignment=1,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'H1Style',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_blue,
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_dark,
        spaceAfter=6
    )

    quote_style = ParagraphStyle(
        'QuoteStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=14,
        textColor=c_primary,
        backColor=colors.HexColor("#fee2e2"),
        borderColor=c_accent,
        borderWidth=1,
        borderPadding=8,
        spaceBefore=6,
        spaceAfter=10
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=1,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6
    )

    story = []

    # Document Header
    story.append(Paragraph("AcciSense: Automated CCTV Crash Detection & Multi-Agency Dispatch System", title_style))
    story.append(Paragraph("Complete Presentation Speech, Technical Documentation, Mathematical Models & Future Roadmap", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceAfter=12))

    # Section 1: Pitch Speech Script
    story.append(Paragraph("1. EXECUTIVE SUMMARY & 60-SECOND PITCH SPEECH", h1_style))
    speech_text = (
        "<b>Presenter Speech:</b><br/>"
        "\"Good morning evaluators and members of the panel. Every 24 seconds, a life is lost in a road traffic collision worldwide. "
        "The single most critical factor determining survival is emergency response time — known as the <b>Golden Hour</b>. "
        "Current emergency response systems suffer from manual reporting delays, vague location descriptions, and zero real-time situational awareness.<br/><br/>"
        "We created <b>AcciSense</b> — an autonomous AI platform that converts standard municipal CCTV cameras, RTSP traffic streams, and mobile video into an intelligent emergency dispatch shield. "
        "Powered by a multi-scale YOLOv8 deep learning pipeline, AcciSense detects crashes within 400ms, measures structural damage severity, acquires live device GPS coordinates, and instantly broadcasts emergency payloads directly to dedicated control portals for <b>Hospitals</b>, <b>Police</b>, and <b>Ambulance EMS teams</b>. AcciSense doesn't just record accidents — it saves lives automatically.\""
    )
    story.append(Paragraph(speech_text, quote_style))

    # Section 2: Mathematical Models
    story.append(Paragraph("2. MATHEMATICAL FORMULATIONS & AI DETECTION PIPELINE", h1_style))
    math_text = (
        "<b>A. Intersection over Union (IoU) Collision Metric:</b><br/>"
        "For two vehicle bounding boxes A and B:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>IoU(A, B) = Area(A ∩ B) / Area(A ∪ B)</b><br/>"
        "If IoU(A, B) ≥ 0.08, an active spatial collision overlap is flagged.<br/><br/>"
        "<b>B. Vehicle Structural Damage Surface Score (S<sub>D</sub>):</b><br/>"
        "Evaluated inside detected vehicle Region of Interest (ROI) using Canny edge density (δ<sub>E</sub>) and intensity variance (σ<sup>2</sup><sub>I</sub>):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>S<sub>D</sub> = 0.40 · I(δ<sub>E</sub> > 0.12) + 0.35 · I(σ<sup>2</sup><sub>I</sub> > 550) + 0.25 · I(Contours ≥ 2)</b><br/><br/>"
        "<b>C. Multi-Scale Central Zoom Detection:</b><br/>"
        "Executes a full-frame scan (conf=0.10) alongside a central 80% zoom crop scan (conf=0.08) to detect small or screen-captured vehicles reliably."
    )
    story.append(Paragraph(math_text, body_style))

    # Section 3: Technical Specifications Table
    story.append(Paragraph("3. SYSTEM ARCHITECTURE SPECS", h1_style))
    table_data = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Functionality</b>", body_style)],
        [Paragraph("Deep Learning", body_style), Paragraph("PyTorch / YOLOv8", body_style), Paragraph("Sensitive vehicle detection & classification", body_style)],
        [Paragraph("Computer Vision", body_style), Paragraph("OpenCV / NumPy", body_style), Paragraph("Edge density, multi-scale crop zoom, bounding boxes", body_style)],
        [Paragraph("Backend Framework", body_style), Paragraph("Python FastAPI", body_style), Paragraph("Async REST API, database ORM, static hosting", body_style)],
        [Paragraph("Database", body_style), Paragraph("SQLite / SQLAlchemy", body_style), Paragraph("Incident log persistence & evidence mapping", body_style)],
        [Paragraph("Real-Time Engine", body_style), Paragraph("WebSockets (ws://)", body_style), Paragraph("Zero-latency event broadcast to department portals", body_style)],
        [Paragraph("Department Portals", body_style), Paragraph("HTML5 / Leaflet.js", body_style), Paragraph("Dedicated control stations for Hospital, Police, EMS", body_style)]
    ]
    t = Table(table_data, colWidths=[1.5*inch, 1.8*inch, 3.7*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Section 4: Emergency Dispatch Message Format
    story.append(Paragraph("4. MULTI-AGENCY EMERGENCY MESSAGE DISPATCH PAYLOAD", h1_style))
    msg_block = (
        "================ EMERGENCY ALERT ================\n"
        "🚨 ACCIDENT CONFIRMED\n"
        "🕒 Time (UTC): 2026-08-11 20:22:21\n"
        "📍 Location: Latitude 17.497985, Longitude 78.1467645\n"
        "🏥 Hospital Services: NOTIFIED\n"
        "🚓 Police Department: NOTIFIED\n"
        "🚑 Ambulance Services: NOTIFIED\n"
        "================================================="
    )
    story.append(Paragraph(msg_block.replace("\n", "<br/>"), code_style))

    # Section 5: Step-by-Step Presentation Script
    story.append(Paragraph("5. STEP-BY-STEP PRESENTATION SCRIPT FOR VIVA & DEMOS", h1_style))
    script_p1 = (
        "<b>Slide 1: Problem & Motivation</b><br/>"
        "\"Bystanders often take 10 to 15 minutes to report accidents, and manual location reports are frequently inaccurate. AcciSense makes traffic infrastructure self-reporting.\""
    )
    script_p2 = (
        "<b>Slide 2: Dual-Stage Computer Vision</b><br/>"
        "\"AcciSense doesn't just check distance between cars. It combines bounding box spatial overlap (IoU) with surface damage texture analysis, preventing false alarms in heavy traffic.\""
    )
    script_p3 = (
        "<b>Slide 3: Multi-Department Dispatch</b><br/>"
        "\"When a crash is confirmed, AcciSense sends direct tailored alerts to three separate web stations: Hospital ER (/hospital), Police Control (/police), and Ambulance EMS (/ambulance).\""
    )
    story.append(Paragraph(script_p1, body_style))
    story.append(Paragraph(script_p2, body_style))
    story.append(Paragraph(script_p3, body_style))

    # Section 6: Viva Defense Q&A
    story.append(Paragraph("6. VIVA & JUDGES' Q&A DEFENSE GUIDE", h1_style))
    qa1 = (
        "<b>Q1: How do you prevent false positives in heavy traffic congestion?</b><br/>"
        "<i>Answer:</i> Normal bumper-to-bumper traffic has spatial overlap but low surface damage scores (smooth metallic reflection). AcciSense requires high structural edge density alongside IoU overlap to confirm a crash."
    )
    qa2 = (
        "<b>Q2: How does laptop/device location tracking work?</b><br/>"
        "<i>Answer:</i> AcciSense integrates HTML5 navigator.geolocation and Expo Location services to pull high-accuracy hardware GPS coordinates directly from the laptop/device."
    )
    story.append(Paragraph(qa1, body_style))
    story.append(Paragraph(qa2, body_style))

    # Section 7: Future Enhancements & Roadmap
    story.append(Paragraph("7. FUTURE ENHANCEMENTS & EXPANSION ROADMAP", h1_style))
    roadmap_text = (
        "<b>1. Autonomous Drone Swarm Dispatch:</b> Automatically launches drones from junction stations to hover over crash scenes, streaming 4K aerial video.<br/>"
        "<b>2. Automatic License Plate Recognition (ALPR):</b> Reads license plates via OCR to retrieve driver blood type and medical history (EHR) before hospital arrival.<br/>"
        "<b>3. Smart Green Wave Signal Priority:</b> Interfaces with SCATS traffic lights to force signals green along the ambulance route.<br/>"
        "<b>4. 5G C-V2X Highway Warning Broadcast:</b> Transmits decelerate warnings to nearby connected vehicles within 1km to prevent pileups.<br/>"
        "<b>5. Edge AI TensorRT Acceleration:</b> Deploys TensorRT FP16 models directly onto NVIDIA Jetson hardware for 120+ FPS local edge processing."
    )
    story.append(Paragraph(roadmap_text, body_style))

    # Section 8: Real-World Deployment & Non-CCTV Coverage Solutions
    story.append(Paragraph("8. REAL-WORLD DEPLOYMENT & NON-CCTV COVERAGE SOLUTIONS", h1_style))
    deploy_text = (
        "<b>A. Camera Mounting Geometry:</b> Mounted 6m to 10m high at traffic poles angled downward 30° to 45° with 110° wide-angle FOV covering a 150m detection radius.<br/><br/>"
        "<b>B. Non-CCTV Regions & Blind Spots:</b><br/>"
        "&nbsp;&nbsp;1. <i>Mobile App & G-Sensors:</i> Smartphone accelerometers detect impact (>3.5G), capturing crash frames and GPS coordinates automatically.<br/>"
        "&nbsp;&nbsp;2. <i>Patrol Dashcams:</i> Police and ambulance vehicles stream live dashcam feeds while patrolling remote highway stretches.<br/><br/>"
        "<b>C. Edge Architecture & Bandwidth Optimization:</b> Processing is executed on-edge inside camera housings (NVIDIA Jetson). Video is NEVER continuously uploaded to the cloud — only 2KB JSON alert payloads and single annotated crash evidence images are transmitted."
    )
    story.append(Paragraph(deploy_text, body_style))

    doc.build(story)
    print(f"PDF successfully generated at: {os.path.abspath(filename)}")

if __name__ == "__main__":
    create_pdf()
