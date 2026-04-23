# Server Architecture

## Overview
The server is the "brain" of the operation. It runs on Linux or FreeBSD, hosts Ollama for LLM inference, and exposes APIs for the doll clients and the web interface. All heavy compute (STT, LLM, vision, TTS) happens here.

## Technology Stack
- **Runtime**: Python 3.11+
- **Web Framework**: FastAPI (async, OpenAPI auto-docs, WebSocket support)
- **Process Manager**: asyncio + uvloop (on Linux)
- **Message Broker**: Redis (for multi-doll pub/sub, session state, job queues)
- **Database**: SQLite (single-server) or PostgreSQL (multi-server)
- **LLM Runtime**: Ollama (local, OpenAI-compatible API)
- **TTS**: Piper (local, fast) or Coqui TTS (higher quality, slower)
- **STT**: Whisper (via faster-whisper or whisper.cpp through Ollama if available)
- **Container**: Optional Docker/Podman for deployment

## Directory Layout (Server)
```
teddy-server/
├── pyproject.toml
├── README.md
├── src/
│   └── teddy_server/
│       ├── __init__.py
│       ├── main.py              # FastAPI app entrypoint
│       ├── config.py            # Pydantic settings (env vars, .env)
│       ├── api/
│       │   ├── __init__.py
│       │   ├── dolls.py         # CRUD + status for dolls
│       │   ├── sessions.py      # Conversation session endpoints
│       │   ├── websocket.py     # WebSocket handlers for real-time comms
│       │   └── webui.py         # Static files + SPA fallback
│       ├── core/
│       │   ├── __init__.py
│       │   ├── session_manager.py
│       │   ├── audio_pipeline.py
│       │   ├── video_pipeline.py
│       │   ├── action_planner.py
│       │   └── conversation_engine.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── doll.py          # Pydantic models for doll state
│       │   ├── session.py       # Session, message, context models
│       │   └── events.py        # WebSocket / SSE event schemas
│       ├── services/
│       │   ├── __init__.py
│       │   ├── ollama_client.py # Async HTTP client for Ollama
│       │   ├── tts_service.py   # Piper / Coqui wrapper
│       │   ├── stt_service.py   # Whisper wrapper
│       │   └── vision_service.py# Vision LLM wrapper
│       └── utils/
│           ├── __init__.py
│           └── audio_utils.py   # PCM encoding, resampling, VAD
├── tests/
│   └── ...
└── scripts/
    └── setup_ollama.sh          # Pull required models
```

## Ollama Integration

### Required Models
| Model | Role | Size | Quantization | Notes |
|-------|------|------|--------------|-------|
| `llama3.2` or `phi4` | General chat | 3B–14B | Q4_K_M | Fast, good for dialogue |
| `llava-phi3` or `moondream2` | Vision | 3B–8B | Q4_K_M | Image understanding |
| `qwen2.5-coder` or `deepseek-coder` | Action planning | 7B | Q4_K_M | JSON generation for actions |
| `nomic-embed-text` | Embeddings | 137M | N/A | RAG / memory retrieval |

### Ollama Client Design
- **Library**: `httpx` (async) with retries and connection pooling
- **API**: OpenAI-compatible `/v1/chat/completions` and `/v1/embeddings`
- **Streaming**: Use SSE streaming for chat to reduce perceived latency
- **Batching**: Batch STT and vision requests where possible
- **Health Check**: Poll `/api/tags` and `/api/ps` to monitor model loading

## API Design

### REST Endpoints
```
GET    /api/v1/dolls              → List all registered dolls
POST   /api/v1/dolls              → Register a new doll
GET    /api/v1/dolls/{id}         → Get doll status
DELETE /api/v1/dolls/{id}         → Unregister doll
GET    /api/v1/dolls/{id}/logs    → Get recent event logs

GET    /api/v1/sessions           → List active sessions
POST   /api/v1/sessions           → Start a new session
GET    /api/v1/sessions/{id}      → Get session state
DELETE /api/v1/sessions/{id}      → End session
POST   /api/v1/sessions/{id}/text → Send text to doll (manual override)
```

### WebSocket Endpoints
```
/ws/doll/{doll_id}     → Doll client connects here (binary audio + JSON events)
/ws/operator           → Web UI operator connects here (control + monitoring)
/ws/audience/{token}   → Optional: audience view (read-only video + audio out)
```

### Protocol (Doll ↔ Server WebSocket)
All messages are JSON with a `type` field. Binary audio frames are sent as WebSocket binary messages interleaved with JSON control messages.

**Client → Server:**
```json
{"type": "audio_chunk", "timestamp": 1713840000.0, "format": "pcm_s16le_16khz_mono"}
{"type": "video_frame", "timestamp": 1713840000.0, "format": "jpeg_720p"}
{"type": "sensor_data", "timestamp": 1713840000.0, "data": {"battery": 3.8, "wifi_rssi": -45}}
{"type": "ping"}
```

**Server → Client:**
```json
{"type": "audio_response", "timestamp": 1713840000.0, "format": "pcm_s16le_22khz_mono", "duration_ms": 2500}
{"type": "servo_command", "timestamp": 1713840000.0, "commands": [{"channel": 0, "angle": 45, "speed_ms": 100}]}
{"type": "led_command", "timestamp": 1713840000.0, "state": {"eye_left": "blue", "eye_right": "blue"}}
{"type": "pong"}
```

## Session Manager

### Session Lifecycle
1. **Idle**: Doll is connected but no active conversation.
2. **Listening**: VAD detected voice; audio is streaming to server.
3. **Thinking**: STT complete; LLM is generating response.
4. **Speaking**: TTS audio is streaming to doll; servos are animating.
5. **Interruption**: New VAD while speaking → abort current, go to Listening.

### Context Window
- Keep last N messages (e.g., 20) in memory per session.
- Use `nomic-embed-text` to embed messages for long-term memory retrieval.
- Store summaries in SQLite/PostgreSQL for persistence across reboots.

### Multi-Modal Context
Each turn in the context includes:
- `role`: `user` | `assistant` | `system`
- `content`: text content
- `image`: optional base64 JPEG (last frame before user spoke)
- `timestamp`: Unix float
- `emotion_detected`: optional string from vision pipeline

## Audio Pipeline (Server-Side)

### Flow
```
Doll (PCM 16kHz mono) → WebSocket → VAD → Buffer → STT (Whisper) → Text → LLM
```

### Voice Activity Detection (VAD)
- **Library**: `silero-vad` or `webrtcvad`
- **Config**: 30ms frames, threshold 0.5, padding 300ms
- **Behavior**: Stream audio to server continuously; server runs VAD and only buffers speech segments.

### Speech-to-Text (STT)
- **Engine**: `faster-whisper` (local) or Ollama-compatible Whisper model
- **Model**: `base` or `small` for speed; `medium` if server has GPU
- **Language**: Auto-detect or configurable per doll
- **Latency Target**: <2s end-to-end for a 5-second utterance

### Text-to-Speech (TTS)
- **Engine**: Piper (fast, local, low resource)
- **Voice**: Download a friendly, expressive voice (e.g., `en_US-lessac-medium`)
- **Output Format**: PCM 22kHz mono, 16-bit
- **Streaming**: Generate audio in chunks and stream to doll as soon as first chunk is ready
- **Lip Sync**: Server sends `servo_command` with mouth angles timed to phoneme boundaries (approximated from text length)

## Video Pipeline (Server-Side)

### Flow
```
Doll (JPEG 720p) → WebSocket → Vision LLM → Emotion / Gesture / Scene Description
```

### Frame Rate
- Capture at 5–10 FPS (sufficient for scene understanding; reduces bandwidth and compute)
- Only send frames when scene may have changed (motion detection on Pi, or periodic)

### Vision Tasks
1. **Emotion Detection**: "Describe the facial expression of the person in front of you."
2. **Gesture Recognition**: "Is the person waving, pointing, or holding something?"
3. **Scene Description**: "How many people are in the room? What is the lighting?"
4. **Object Detection**: "Is there a cake on the table?" (for party context)

### Prompting Strategy
- Use a structured prompt template that asks the vision model to return JSON:
```json
{
  "people_count": 2,
  "dominant_emotion": "happy",
  "gestures": ["waving"],
  "notable_objects": ["balloons", "cake"],
  "lighting": "bright indoor",
  "description": "Two children are smiling and waving at the camera."
}
```

## Action Planner

### Role
A dedicated LLM call (or structured prompt to the main LLM) that decides:
- What servos to move and when
- What LED colors to set
- Whether to play a sound effect
- Whether to trigger a "special action" (dance, walk, etc.)

### Input
- Current conversation text (last assistant message)
- Detected emotion from vision
- Current servo positions
- Doll capabilities (which servos are installed)

### Output (JSON)
```json
{
  "actions": [
    {"type": "servo", "channel": 0, "angle": 60, "delay_ms": 0, "speed_ms": 80},
    {"type": "servo", "channel": 3, "angle": 110, "delay_ms": 100, "speed_ms": 150},
    {"type": "led", "target": "eyes", "color": "warm_white", "delay_ms": 0},
    {"type": "expression", "name": "happy_blink", "delay_ms": 500}
  ],
  "audio_sync": {
    "mouth_channel": 0,
    "open_angle": 70,
    "close_angle": 30,
    "syllables_per_second": 4.5
  }
}
```

## Configuration

### Environment Variables
```bash
TEDDY_SERVER_HOST=0.0.0.0
TEDDY_SERVER_PORT=8000
TEDDY_OLLAMA_URL=http://localhost:11434
TEDDY_REDIS_URL=redis://localhost:6379
TEDDY_DB_URL=sqlite:///data/teddy.db
TEDDY_TTS_ENGINE=piper
TEDDY_TTS_VOICE=en_US-lessac-medium
TEDDY_STT_MODEL=base
TEDDY_LOG_LEVEL=INFO
```

## Deployment

### Native (Linux / FreeBSD)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[server]"
python -m teddy_server.main
```

### Docker
```bash
docker build -t teddy-server .
docker run -p 8000:8000 --gpus all teddy-server
```

### FreeBSD Notes
- Ollama does not officially support FreeBSD; may need to build from source or run in a Linux jail.
- Use `pkg install py311-pip` and `pkg install redis`.
- Prefer `kqueue` over `epoll` for asyncio (handled by Python automatically).
