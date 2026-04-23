# Video Pipeline

## Overview
The video pipeline enables the doll to "see" its environment. The Pi captures video frames and streams them to the server, where a vision LLM analyzes them for emotion detection, gesture recognition, scene understanding, and object detection. The results feed into the conversation engine and action planner.

## Pipeline Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Camera    │────▶│   Encode    │────▶│   Stream    │────▶│   Server    │
│  (Pi, 720p) │     │  (JPEG)     │     │ (WebSocket) │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                    │
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐
│   Action    │◀────│   Vision    │◀────│   Vision    │◀────│   Decode    │
│   Planner   │     │   Parser    │     │    LLM      │     │   (JPEG)    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           ▲
                           │
                    ┌──────┴──────┐
                    │  Conversation │
                    │    Engine     │
                    └───────────────┘
```

## 1. Video Capture (Pi)

### Camera Options

#### Raspberry Pi Camera Module (CSI)
- **Library**: `picamera2` (libcamera-based, official)
- **Resolution**: 1280×720 (720p) or 1640×1232 (2x2 binned)
- **FPS**: 5–10 (sufficient for scene understanding)
- **Format**: RGB or YUV → encode to JPEG on CPU

```python
from picamera2 import Picamera2

camera = Picamera2()
camera.configure(camera.create_preview_configuration(
    main={"size": (1280, 720), "format": "RGB888"}
))
camera.start()
```

#### USB Webcam (UVC)
- **Library**: `opencv-python` (`cv2`)
- **Resolution**: 1280×720
- **FPS**: 10–30
- **Format**: MJPEG (hardware-encoded) or YUY2

```python
import cv2

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 5)
```

### Frame Encoding
- **Target**: JPEG, quality 75–85
- **Size**: ~50–100KB per frame at 720p
- **CPU Cost**: ~20ms per frame on Pi Zero 2 W
- **Bandwidth**: 5 FPS × 75KB = ~3 Mbps (well within Wi-Fi capacity)

```python
import cv2

_, jpeg_buffer = cv2.imencode('.jpg', frame, [
    cv2.IMWRITE_JPEG_QUALITY, 85,
    cv2.IMWRITE_JPEG_OPTIMIZE, 1
])
jpeg_bytes = jpeg_buffer.tobytes()
```

## 2. Motion Detection & Throttling

To reduce bandwidth and server load, the Pi should only send frames when something interesting is happening.

### Simple Frame Differencing
```python
import cv2
import numpy as np

prev_frame = None
motion_threshold = 5000  # number of changed pixels

def should_send_frame(frame: np.ndarray) -> bool:
    global prev_frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    if prev_frame is None:
        prev_frame = gray
        return True  # always send first frame

    diff = cv2.absdiff(prev_frame, gray)
    thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
    changed_pixels = cv2.countNonZero(thresh)
    prev_frame = gray

    return changed_pixels > motion_threshold
```

### Throttling Rules
- **Motion Detected**: Send at 5 FPS
- **No Motion**: Send 1 frame every 2 seconds (keep-alive)
- **Conversation Active**: Force 5 FPS during Listening/Thinking/Speaking states
- **Server Request**: Server can send `{"type": "request_frame"}` to force a capture

## 3. Video Streaming

### WebSocket Frame Messages
```json
{
  "type": "video_frame",
  "timestamp": 1713840000.0,
  "format": "jpeg_720p",
  "data": "base64_encoded_jpeg..."
}
```

### Bandwidth Management
| Scenario | FPS | Frame Size | Bandwidth |
|----------|-----|------------|-----------|
| Idle (no motion) | 0.5 | 75KB | ~300 Kbps |
| Active conversation | 5 | 75KB | ~3 Mbps |
| Party mode (many people) | 5 | 100KB | ~4 Mbps |

### Adaptive Quality
If Wi-Fi RSSI is weak (<-65dBm), reduce JPEG quality to 60 or resolution to 640×360.

## 4. Vision LLM Processing (Server)

### Model Selection
| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| `llava-phi3` | 3.8B | Fast | General scene description |
| `moondream2` | 1.6B | Very fast | Quick emotion/gesture checks |
| `llava-v1.6-mistral` | 7B | Medium | Detailed analysis |

### Prompting Strategy

#### Emotion Detection
```
You are looking through the eyes of a teddy bear doll at the people in front of you.
Describe the facial expression and emotional state of the person closest to the camera.
Return ONLY a JSON object: {"emotion": "happy|sad|angry|surprised|neutral|confused", "confidence": 0.0-1.0}
```

#### Gesture Recognition
```
You are looking through the eyes of a teddy bear doll.
What are the people in the image doing? Are they waving, pointing, dancing, sitting, or standing?
Return ONLY a JSON object: {"gestures": ["waving", "pointing"], "people_count": 2}
```

#### Scene Description
```
You are looking through the eyes of a teddy bear doll at a party.
Describe the scene in 1-2 sentences. How many people? What is the mood? Any notable objects?
Return ONLY a JSON object: {"people_count": 3, "mood": "festive", "notable_objects": ["cake", "balloons"], "description": "..."}
```

### Processing Frequency
- **Emotion**: Every 2 seconds during conversation
- **Gesture**: Every 1 second during conversation
- **Scene**: Every 5 seconds (or on significant motion)
- **Object**: On-demand (e.g., when user asks "Do you see the cake?")

### Caching
- Cache vision LLM results for 1 second to avoid redundant calls
- If frame is similar to previous (SSIM > 0.95), reuse last result

## 5. Vision Parser

The vision LLM returns structured JSON. A parser normalizes and validates this data:

```python
class VisionResult(BaseModel):
    emotion: str | None = None
    emotion_confidence: float = 0.0
    gestures: list[str] = []
    people_count: int = 0
    mood: str | None = None
    notable_objects: list[str] = []
    description: str = ""
    timestamp: float
```

### Emotion Mapping
Map detected emotions to servo expressions:
| Detected Emotion | Servo Expression | LED Color |
|------------------|------------------|-----------|
| happy, excited | smile, wide eyes | warm white |
| sad, tired | frown, droopy eyes | dim blue |
| angry, frustrated | furrowed brows | red |
| surprised | wide eyes, open mouth | bright white |
| neutral, calm | neutral face | soft green |
| confused | head tilt | yellow |

## 6. Privacy & Ethics

### Camera Indicator
- **Hardware**: LED near the camera lens that lights when streaming
- **Software**: Send `{"type": "camera_active", "active": true}` to web UI

### Consent Mode
- "Party Mode": Camera always on, vision processing active
- "Conversation Mode": Camera on only during active conversation
- "Privacy Mode": Camera off, audio-only interaction
- **Toggle**: Physical switch on doll or web UI command

### Data Retention
- Video frames are NOT stored on server (processed and discarded)
- Vision LLM results (JSON) may be logged for debugging (configurable)
- No cloud services; all processing is local (Ollama)

## 7. Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Capture → JPEG encode | <50ms | On Pi Zero 2 W |
| Frame upload latency | <100ms | Wi-Fi |
| Vision LLM inference | <1s | On server CPU |
| Total: scene → action | <2s | End-to-end |
| Frame rate (active) | 5 FPS | During conversation |
| Frame rate (idle) | 0.5 FPS | Keep-alive |
