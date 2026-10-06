---
title: AcciSense AI Accident Detection
emoji: 🚨
colorFrom: red
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# 🚨 AcciSense: AI-Powered Real-Time Accident Detection & Emergency Response System

AcciSense is an end-to-end intelligent road traffic safety platform that detects vehicle collisions in real time using multi-scale computer vision, tracks vehicle kinematics across consecutive frames, confirms accidents via temporal persistence analysis, and automatically dispatches emergency alerts with live GPS coordinates to Hospital, Police, and Ambulance departments over WebSockets.

---

## 🏗️ 1. System Architecture

```text
CCTV / Camera / Mobile Client Feed
              ↓
  Multi-Scale Vehicle Detection (YOLOv8)
              ↓
  Centroid Multi-Object Vehicle Tracking
              ↓
  Spatial Overlap (IoU) & Surface Deformation (Canny)
              ↓
  Temporal Multi-Frame Persistence Verification (>= 3 Frames)
              ↓
  Authoritative Decision Engine
      ├── NORMAL_TRAFFIC   → Zero Alert (Silent Log)
      ├── POSSIBLE_INCIDENT → Monitored Candidate (Observing)
      └── CONFIRMED_ACCIDENT
              ↓
      Visual Evidence Frame Generated
              ↓
      SQLite / PostgreSQL Database Persistence
              ↓
      Real-Time WebSocket Emergency Dispatch (/ws/alerts)
              ↓
  Hospital ER  |  Police Traffic  |  Ambulance EMS  |  Surveillance HUD
```

---

## 🌟 2. Key Features

- **Multi-Scale Vehicle Detection**: Scans full frames (`conf=0.10`) plus central zoom regions (`conf=0.08`) using YOLOv8 (`yolov8n.pt`) to detect cars, trucks, buses, motorcycles, and bicycles even on low-resolution screens or distant roads.
- **Centroid Multi-Object Vehicle Tracking**: Tracks vehicle identities (`track_id`), maintains trajectory history, estimates instantaneous speed, and detects post-impact abnormal vehicle stopping ($< 2.5\text{ px/frame}$).
- **Multi-Frame Temporal Verification**: Guarantees that single-frame anomalies, traffic stops, and close-passing vehicles do **not** trigger false alarms. Collisions must persist over $\ge 3$ consecutive frames with impact evidence.
- **Authoritative Decision Engine**: Enforces strict tripartite classification: `NORMAL_TRAFFIC`, `POSSIBLE_INCIDENT`, and `CONFIRMED_ACCIDENT`. Only confirmed decisions trigger emergency dispatch.
- **Real-Time WebSocket Push (`/ws/alerts`)**: Broadcasts structured emergency payloads instantly to listening department dispatchers.
- **Medical Trauma Triage & Crash Severity Rating**: Automatically assesses collision momentum and physical deformation to allocate triage priority: `CRITICAL_TRAUMA` (immediate surgical ER readiness), `MODERATE_COLLISION` (standard EMS dispatch), or `MINOR_INCIDENT` (traffic scrape).
- **Automated Nearest Facility & Siren ETA Engine**: Calculates real-time Haversine great-circle distances to the nearest registered Hospital, Police Station, and Ambulance Depot, computing dynamic response times at 45 km/h emergency siren velocities.
- **Forensic Chain-of-Custody SHA-256 Integrity**: Computes cryptographic digests on raw accident evidence frames, immutably linking them across database records, WebSocket broadcasts, and department consoles for legal and insurance validity.
- **Dedicated Department Portals**:
  - 📊 **Surveillance Dashboard (`/dashboard`)**: Live interactive Leaflet map, live video stream monitor, and telemetry stats.
  - 🏥 **Hospital ER Portal (`/hospital`)**: Trauma readiness coordination with `HOSPITAL_NOTIFIED` response triggers.
  - 🚓 **Police Traffic Portal (`/police`)**: Traffic clearance and patrol dispatches with `POLICE_NOTIFIED`.
  - 🚑 **Ambulance EMS Portal (`/ambulance`)**: Turn-by-turn GPS navigation links and siren deployment with `AMBULANCE_EN_ROUTE`.
- **Mobile CCTV HUD Scanner (`mobile-app`)**: React Native / Expo application with CCTV viewfinder HUD, continuous scanning, impact simulation, and automatic laptop/device GPS telemetry.

---

## 📁 3. Repository Structure

```text
Accident-Detection-AcciSense-main/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application & REST/WebSocket routes
│   │   ├── database.py              # SQLAlchemy engine & session factory
│   │   ├── models.py                # Database models & AccidentLifecycle enum
│   │   ├── schemas.py               # Pydantic schemas & response models
│   │   ├── services/
│   │   │   ├── ai_detector.py       # YOLOv8 multi-scale vehicle detection & Canny damage scoring
│   │   │   ├── tracker.py           # Centroid vehicle tracking & abnormal halt detection
│   │   │   ├── temporal_filter.py   # Thread-safe multi-frame temporal persistence verifier
│   │   │   ├── decision_engine.py   # Authoritative accident confirmation decision engine
│   │   │   ├── video_detector.py    # StreamSessionTracker integrating tracking & temporal verification
│   │   │   ├── notifier.py          # Structured Section 8 emergency alert broadcaster
│   │   │   ├── websocket_manager.py # Thread-safe WebSocket connection manager
│   │   │   ├── rtsp_stream.py       # RTSP CCTV & webcam worker stream processor
│   │   │   ├── location.py          # Haversine GPS distance calculation
│   │   │   ├── crash_classifier.py  # Backward-compatibility delegate
│   │   │   └── photo_detector.py    # Backward-compatibility delegate
│   │   └── static/
│   │       ├── dashboard.html       # Central Surveillance Command Center
│   │       ├── hospital.html        # Hospital ER Trauma Dispatch Portal
│   │       ├── police.html          # Police Traffic Control Station
│   │       └── ambulance.html       # Ambulance EMS Rescue Station
│   ├── yolov8n.pt                   # Pre-trained YOLOv8 nano neural network weights
│   ├── requirements.txt             # Backend Python dependencies
│   ├── test_full_suite.py           # Master automated end-to-end integration test suite
│   ├── test_phase2_correctness.py   # Code correctness & input validation test suite
│   ├── test_phase3_ai_pipeline.py   # Vehicle tracking & temporal verification test suite
│   ├── test_phase4_db_websocket.py  # Database lifecycle & WebSocket payload test suite
│   └── test_phase5_portals.py       # Department portals integration test suite
├── mobile-app/
│   ├── App.js                       # Multi-tab mobile container
│   ├── app.json                     # Expo configuration
│   ├── package.json                 # React Native / Expo dependencies
│   └── src/
│       ├── config.js                # Dynamic backend URL resolution
│       ├── screens/
│       │   ├── CameraScreen.js      # CCTV traffic monitor HUD & GPS tracker
│       │   ├── DepartmentScreens.js # Hospital, Police, and Ambulance mobile tabs
│       │   └── SettingsScreen.js    # Backend IP/port settings
│       ├── services/
│       │   └── api.js               # Cross-platform HTTP client (Web Blob + Mobile)
│       └── utils/
│           └── impactDetector.js    # Accelerometer / impact simulation
├── Dockerfile                       # Production Hugging Face Space Dockerfile (port 7860)
├── .gitignore                       # Clean repository exclusions
└── README.md                        # Project documentation
```

---

## ⚡ 4. Installation & Local Setup

### Prerequisites
- Python 3.10 or 3.11
- Node.js 18+ and npm

### Backend Setup
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the FastAPI Uvicorn Server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Mobile App / Web Viewfinder Setup
```bash
# In a second terminal:
cd mobile-app

# 1. Install dependencies
npm install

# 2. Launch the Expo surveillance web monitor
npx expo start --web
```

---

## 🌐 5. Web Portals & API Endpoints

Once the backend is running on `http://localhost:8000`:
- 📊 **Central Command Center**: `http://localhost:8000/dashboard`
- 🏥 **Hospital ER Portal**: `http://localhost:8000/hospital`
- 🚓 **Police Traffic Station**: `http://localhost:8000/police`
- 🚑 **Ambulance EMS Station**: `http://localhost:8000/ambulance`
- 📖 **Interactive Swagger API Docs**: `http://localhost:8000/docs`

### REST API Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check & system status |
| `POST` | `/alert` | Process static/mobile photo alert with GPS coordinates |
| `POST` | `/video-frame` | Process incoming CCTV / browser video frame through stream tracker |
| `POST` | `/start-rtsp` | Start asynchronous RTSP CCTV stream monitoring |
| `POST` | `/start-camera` | Start local webcam stream monitoring |
| `POST` | `/stop-stream/{id}` | Terminate active stream worker |
| `GET` | `/api/accidents` | Retrieve list of recent accident logs (last 100) |
| `GET` | `/api/accidents/{id}` | Retrieve individual incident details |
| `PATCH` | `/api/accidents/{id}/status` | Update incident lifecycle status |
| `GET` | `/api/stats` | Retrieve aggregated system statistics |

### WebSocket Endpoint
- **URL**: `ws://localhost:8000/ws/alerts` (or `wss://YOUR-DOMAIN/ws/alerts`)
- **Broadcast Payload Schema**:
```json
{
  "event": "ACCIDENT_CONFIRMED",
  "accident_id": "42",
  "latitude": 17.3850,
  "longitude": 78.4867,
  "location": "Sector Main Road",
  "confidence": 0.94,
  "accident_type": "collision",
  "timestamp": "2026-10-06 12:15:00",
  "annotated_image": "annotated_sample.jpg",
  "status": "CONFIRMED"
}
```

---

## 🔬 6. AI Detection & Verification Pipeline

1. **Object Detection**: YOLOv8 nano processes the frame to identify vehicles with bounding boxes $(x_1, y_1, x_2, y_2)$.
2. **Multi-Object Tracking**: Centroid distance matching associates detections across frames, assigning stable Track IDs and logging velocity vectors.
3. **Collision Candidate Analysis**:
   - $\text{IoU} \ge 0.12$ flags spatial collision overlap.
   - Canny edge detection + variance analysis measures vehicle body deformation.
4. **Temporal Verification**:
   - A sliding window of $N=7$ frames tracks consecutive incident candidates.
   - A minimum of $3$ consecutive candidate frames with sustained overlap, deceleration/abnormal stopping, or structural deformation is required.
5. **Decision Authority**:
   - `NORMAL_TRAFFIC`: Free flowing or queued vehicles without damage. Zero emergency dispatch.
   - `POSSIBLE_INCIDENT`: Transient proximity or sudden braking. Logged and monitored.
   - `CONFIRMED_ACCIDENT`: Multi-frame verified collision. Triggers database insertion, evidence annotation, and WebSocket dispatch.

---

## 🧪 7. Automated Testing

AcciSense includes a full suite of automated offline and integration tests:

```bash
cd backend

# Run Master End-to-End Test Suite (9 comprehensive tests)
python test_full_suite.py

# Run Individual Specialized Suites:
python test_phase2_correctness.py   # Input validation, singleton model, paths
python test_phase3_ai_pipeline.py   # Tracker, temporal persistence, decision engine
python test_phase4_db_websocket.py  # Lifecycle updates, stats, WebSocket payload
python test_phase5_portals.py       # HTML pages, title anchors, secure WebSocket
```

---

## 🚀 8. Production Deployment

### Target Architecture
```text
Vercel (React / Web Frontend) 
        ↓ HTTPS / WSS
Hugging Face Space (FastAPI Docker Backend)
        ↓ Port 7860
YOLOv8 + SQLite / PostgreSQL + WebSocket Manager
```

### Docker Deployment (Hugging Face Spaces)
1. The included `Dockerfile` is configured for Python 3.11, installs system OpenCV/FFmpeg dependencies (`libgl1`, `ffmpeg`), and exposes port `7860`.
2. Environment variables:
   - `PORT=7860`
   - `CORS_ORIGINS=*` (or your Vercel frontend domain)
   - `DATABASE_URL` (optional PostgreSQL connection string; defaults to SQLite)
3. Production API Base: `https://YOUR-SPACE.hf.space`
4. Production WebSocket: `wss://YOUR-SPACE.hf.space/ws/alerts`

---

## ⚠️ 9. Limitations & Scope

- **Day/Night Lighting Variations**: Under extreme darkness with zero street lighting, vehicle edge detection may experience lower contrast.
- **Hardware Profile**: Real-time multi-stream processing at 30 FPS per camera is optimized for GPU environments (e.g. NVIDIA CUDA / TensorRT). CPU-only environments process frames at ~10–15 FPS.
- **Occlusion**: Complete occlusion by large walls or signage can temporarily delay multi-frame association until the vehicle re-emerges in the camera field of view.

---

## 🔮 10. Future Enhancements

The following technologies are roadmap considerations and not currently part of the active codebase:
- **Temporal CNN / Video Transformer**: End-to-end spatio-temporal video neural network (e.g., VideoMAE / SlowFast) trained specifically on multi-camera CCTV crash datasets.
- **DeepSORT / Re-ID Embeddings**: Visual appearance feature extractors for tracking vehicles across non-overlapping camera blind spots.
- **Apache Kafka / Spark Streaming**: Enterprise-scale message bus for handling tens of thousands of distributed CCTV streams across an entire metropolitan area.
- **PostgreSQL / TimescaleDB Migration**: Managed time-series database for long-term historical traffic analytics.
