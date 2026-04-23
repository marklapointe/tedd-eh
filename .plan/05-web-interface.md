# Web Interface

## Overview
A browser-based interface for interacting with the doll(s) during development, testing, and manual override. It connects to the server via WebSocket and REST API, providing real-time monitoring, manual control, and conversation history.

## Technology Stack
- **Frontend**: Vanilla JavaScript or lightweight framework (e.g., Preact, Alpine.js) — keep it simple, no build step required for MVP
- **Styling**: Tailwind CSS (via CDN) or plain CSS
- **Real-Time**: WebSocket (native browser API)
- **Video**: HTML5 `<video>` or `<img>` for MJPEG stream
- **Audio**: Web Audio API for playback, MediaRecorder API for capture

## Directory Layout (Web UI)
```
teddy-webui/
├── index.html              # Main dashboard
├── doll.html               # Single doll detail view
├── settings.html           # Server settings, model config
├── css/
│   └── main.css
├── js/
│   ├── api.js              # REST API wrapper
│   ├── ws.js               # WebSocket manager
│   ├── audio.js            # Browser audio I/O
│   ├── video.js            # Video stream renderer
│   └── ui.js               # DOM manipulation, event handlers
└── assets/
    └── teddy-icon.svg
```

## Pages

### Dashboard (`index.html`)
Grid view of all connected dolls.

**Elements:**
- **Doll Cards**: One card per doll showing:
  - Name + ID
  - Live thumbnail (last video frame)
  - Status badge (Idle, Listening, Thinking, Speaking, Offline)
  - Battery level (if reported)
  - Wi-Fi signal strength
  - Quick actions: "Talk", "Mute", "Reboot"
- **Server Status**: Ollama model list, GPU/CPU load, active sessions count
- **Global Controls**: "Mute All", "Send Message to All", "Emergency Stop"

### Doll Detail (`doll.html?id={doll_id}`)
Full control panel for a single doll.

**Layout (3-column):**
```
┌─────────────────┬─────────────────┬─────────────────┐
│   Video Feed    │  Chat / Logs    │  Manual Controls│
│   (live)        │  (scrollable)   │  (servo sliders)│
│                 │                 │                 │
│  [snapshot]     │  User: Hello!   │  Mouth: [====]  │
│                 │  Doll: Hi!    │  Eyes:  [====]  │
│                 │  [timestamp]    │  Head:  [====]  │
│                 │                 │  Arms:  [====]  │
│                 │                 │                 │
│                 │  [text input]   │  [Expression]   │
│                 │  [send] [mic]   │  [Walk] [Dance] │
└─────────────────┴─────────────────┴─────────────────┘
```

**Video Feed:**
- Displays MJPEG stream or WebSocket-received JPEG frames
- Click to toggle fullscreen
- "Snapshot" button saves current frame as PNG

**Chat / Logs:**
- Conversation history (user ↔ doll)
- System events (connection, errors, servo commands)
- Text input to manually send a message to the doll
- Microphone button to speak to the doll (browser → server → doll)

**Manual Controls:**
- Sliders for each servo channel (0–180°)
- "Home All" button
- "Expression" buttons: Happy, Sad, Surprised, Sleepy, Angry
- "Action" buttons: Wave Left, Wave Right, Nod, Shake Head, Dance, Walk
- LED color picker (if supported)

### Settings (`settings.html`)
- Ollama model selection per task (chat, vision, action, STT)
- TTS voice selection
- Global prompt templates (system prompt, personality)
- Doll registration / capability editing
- Server logs viewer (last 1000 lines)

## WebSocket Protocol (Browser ↔ Server)

### Connection
```javascript
const ws = new WebSocket('wss://teddy-server.local/ws/operator');
ws.onopen = () => {
  ws.send(JSON.stringify({type: 'auth', token: 'operator-jwt'}));
};
```

### Messages (Server → Browser)
```json
{"type": "doll_status", "doll_id": "teddy-01", "status": "speaking", "battery": 3.8, "rssi": -45}
{"type": "video_frame", "doll_id": "teddy-01", "timestamp": 1713840000.0, "data": "base64jpeg..."}
{"type": "audio_chunk", "doll_id": "teddy-01", "timestamp": 1713840000.0, "data": "base64pcm..."}
{"type": "conversation", "doll_id": "teddy-01", "role": "assistant", "text": "Hello there!"}
{"type": "servo_update", "doll_id": "teddy-01", "channel": 0, "angle": 45}
{"type": "log", "level": "INFO", "message": "Doll teddy-01 connected"}
```

### Messages (Browser → Server)
```json
{"type": "text_message", "doll_id": "teddy-01", "text": "Tell me a joke!"}
{"type": "servo_command", "doll_id": "teddy-01", "channel": 0, "angle": 60, "speed_ms": 100}
{"type": "expression", "doll_id": "teddy-01", "name": "happy"}
{"type": "action", "doll_id": "teddy-01", "name": "wave_left"}
{"type": "mute", "doll_id": "teddy-01", "duration_ms": 30000}
{"type": "reboot", "doll_id": "teddy-01"}
```

## Audio in the Browser

### Speaking to the Doll
1. User clicks microphone button
2. Browser requests `navigator.mediaDevices.getUserMedia({audio: true})`
3. MediaRecorder captures audio as WebM/Opus
4. Browser sends `audio_chunk` messages (or a single `audio_blob` message) to server
5. Server processes STT → LLM → TTS → streams back to doll

### Hearing the Doll
- When browser receives `audio_chunk` from server, decode PCM and play via Web Audio API
- Useful for remote monitoring or testing without being near the doll

## Mobile Support
- Responsive CSS: stack columns on narrow screens
- Touch-friendly sliders and buttons (min 44px tap target)
- Optional: PWA manifest for "Add to Home Screen"

## Security
- All WebSocket and HTTP traffic over WSS/HTTPS
- JWT tokens for operator authentication
- Role-based access: `operator` (full control) vs `viewer` (read-only)
- CORS configured to allow only same-origin or specified domains
