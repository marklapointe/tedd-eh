# Client Architecture (Raspberry Pi)

## Overview
The client runs on the Raspberry Pi inside the doll. It is intentionally lightweight: it captures audio and video, streams them to the server, receives commands (audio + servo), and executes them. All "intelligence" lives on the server.

## Technology Stack
- **Runtime**: Python 3.11+ (Raspberry Pi OS Lite, 64-bit)
- **Async Framework**: `asyncio` (stdlib)
- **WebSocket Client**: `websockets` (pure Python, no heavy deps)
- **Audio I/O**: `sounddevice` (PortAudio wrapper) or `pyaudio`
- **Video I/O**: `picamera2` (libcamera, Pi-native) or `opencv-python` (USB webcam)
- **Servo Control**: `adafruit-circuitpython-servokit` (PCA9685) or `gpiozero` (direct PWM)
- **Configuration**: `pydantic-settings` with a YAML config file on SD card

## Directory Layout (Client)
```
teddy-client/
├── pyproject.toml
├── README.md
├── config.yaml                  # Doll identity, server URL, hardware map
├── src/
│   └── teddy_client/
│       ├── __init__.py
│       ├── main.py              # Entrypoint, lifecycle manager
│       ├── config.py            # Pydantic settings from YAML + env
│       ├── network.py           # WebSocket connection, reconnection, heartbeat
│       ├── audio_io.py          # Microphone capture, speaker playback
│       ├── video_io.py          # Camera capture, frame encoding
│       ├── servo_controller.py  # PCA9685 / GPIO servo abstraction
│       ├── led_controller.py    # Optional: NeoPixel / GPIO LED control
│       └── sensor_io.py         # Battery monitor, Wi-Fi RSSI, temperature
├── systemd/
│   └── teddy-client.service     # Auto-start on boot
└── scripts/
    └── install.sh               # One-shot setup for Pi
```

## Hardware Abstraction Layer

### Servo Controller (`servo_controller.py`)
```python
class ServoController:
    def __init__(self, config: ServoConfig):
        self.driver = PCA9685(...)  # or MockDriver for dev
        self.channels = config.channels  # dict[int, ServoChannel]

    async def set_angle(self, channel: int, angle: float, speed_ms: int = 0):
        """Move servo to angle over speed_ms milliseconds."""
        ...

    async def run_sequence(self, sequence: list[ServoCommand]):
        """Run a timed sequence of servo commands."""
        ...

    async def home_all(self):
        """Return all servos to neutral positions."""
        ...
```

### Audio I/O (`audio_io.py`)
```python
class AudioIO:
    def __init__(self, config: AudioConfig):
        self.mic_stream = sounddevice.RawInputStream(...)
        self.speaker_stream = sounddevice.RawOutputStream(...)

    async def read_chunk(self) -> bytes:
        """Read a chunk of PCM audio from the microphone."""
        ...

    async def play_chunk(self, chunk: bytes):
        """Write a chunk of PCM audio to the speakers."""
        ...

    async def stop_playback(self):
        """Abort current playback (for interruption handling)."""
        ...
```

### Video I/O (`video_io.py`)
```python
class VideoIO:
    def __init__(self, config: VideoConfig):
        self.camera = picamera2.Picamera2()  # or cv2.VideoCapture(...)

    async def capture_frame(self) -> bytes:
        """Capture a single JPEG-encoded frame."""
        ...

    async def start_preview(self):
        """Optional: start a local preview window (for debugging)."""
        ...
```

## Network Protocol

### Connection
- Connects to `wss://{server_host}/ws/doll/{doll_id}`
- Sends `Authorization: Bearer {token}` header (token from config.yaml)
- Automatic reconnection with exponential backoff (1s, 2s, 4s, 8s, max 60s)

### Heartbeat
- Client sends `{"type": "ping"}` every 15 seconds
- Server responds with `{"type": "pong"}`
- If no pong within 5 seconds, reconnect

### Audio Streaming
- **Capture**: 16kHz, 16-bit, mono, 20ms frames (640 bytes)
- **Playback**: 22kHz, 16-bit, mono, variable chunk size
- **Buffering**: Client maintains a 200ms playback buffer to absorb jitter
- **Interruption**: On receiving new `audio_response` while playing, stop current playback and start new (or queue if `queue=true`)

### Video Streaming
- **Capture**: 720p JPEG, quality 85, ~5 FPS
- **Throttling**: Only send a frame if motion detected (simple frame diff on Pi) or every 2 seconds minimum
- **Bandwidth**: Target <500 Kbps for video

### Command Execution
- Servo commands are executed immediately upon receipt
- If a command has `delay_ms`, schedule it with `asyncio.call_later`
- LED commands are applied instantly

## Configuration (`config.yaml`)
```yaml
doll:
  id: "teddy-01"
  name: "Tedd-EH"
  token: "super-secret-jwt-token"
  capabilities:
    - mouth
    - eyes
    - eyelids
    - head_tilt
    - head_pan
    - left_arm
    - right_arm

server:
  host: "teddy-server.local"
  port: 8000
  use_ssl: false
  reconnect_interval: 5

audio:
  mic_device: "default"
  speaker_device: "default"
  capture_rate: 16000
  capture_channels: 1
  playback_rate: 22050
  playback_channels: 1
  chunk_ms: 20

video:
  camera_type: "picamera2"  # or "usb"
  resolution: [1280, 720]
  fps: 5
  jpeg_quality: 85
  motion_threshold: 5000  # pixel diff threshold

servos:
  driver: "pca9685"
  i2c_bus: 1
  i2c_address: 0x40
  frequency: 50
  channels:
    0: { name: "mouth", min_angle: 0, max_angle: 90, neutral: 30 }
    1: { name: "eyes", min_angle: 0, max_angle: 180, neutral: 90 }
    2: { name: "eyelids", min_angle: 0, max_angle: 90, neutral: 0 }
    3: { name: "head_tilt", min_angle: 45, max_angle: 135, neutral: 90 }
    4: { name: "head_pan", min_angle: 0, max_angle: 180, neutral: 90 }
    5: { name: "left_arm", min_angle: 0, max_angle: 180, neutral: 90 }
    6: { name: "right_arm", min_angle: 0, max_angle: 180, neutral: 90 }

sensors:
  battery_adc: true
  battery_adc_channel: 0
  temperature: true
```

## Boot & Service Management

### systemd Service
```ini
[Unit]
Description=Tedd-EH Client
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=simple
User=teddy
WorkingDirectory=/opt/teddy-client
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/teddy-client/.venv/bin/python -m teddy_client.main --config /opt/teddy-client/config.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Boot Sequence
1. systemd starts `teddy-client.service`
2. Client reads `config.yaml`
3. Initializes hardware (servos to neutral, camera, audio)
4. Connects to server WebSocket
5. Sends `{"type": "register", "capabilities": [...]}`
6. Enters main loop: capture → stream → execute commands

## Error Handling & Resilience

### Network Loss
- Log disconnection, set servos to neutral (safe position)
- Retry connection every 5 seconds
- If disconnected >5 minutes, enter "sleep mode" (dim eyes, low power)

### Hardware Failure
- If camera fails: continue audio-only, notify server
- If microphone fails: continue video + servo-only, notify server
- If servo driver fails: continue audio + video, notify server
- If audio output fails: log error, continue other functions

### Watchdog
- Use `systemd-watchdog` or a simple asyncio task that reboots the Pi if the main loop hangs for >60 seconds

## Development & Testing

### Mock Mode
Run the client on any Linux machine without Pi hardware:
```bash
TEDDY_MOCK_HARDWARE=1 python -m teddy_client.main --config config.mock.yaml
```
Mock mode:
- Uses a WAV file as microphone input
- Saves speaker output to WAV file
- Uses a static JPEG as camera feed
- Prints servo commands to stdout instead of moving hardware

### Local Server Test
```bash
# Terminal 1: start server
python -m teddy_server.main

# Terminal 2: start mock client
python -m teddy_client.main --config config.mock.yaml --server ws://localhost:8000
```
