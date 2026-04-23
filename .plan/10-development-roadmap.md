# Development Roadmap

## Overview
This roadmap breaks the project into manageable phases, from proof-of-concept to a fully animated, multi-doll party system. Each phase builds on the previous one and has clear deliverables and success criteria.

## Phase 0: Foundation (Weeks 1–2)
**Goal**: Set up the project structure, development environment, and basic communication.

### Deliverables
- [ ] Monorepo structure with `teddy-server`, `teddy-client`, `teddy-webui`
- [ ] `pyproject.toml` for each component with dependencies
- [ ] Basic FastAPI server with health check endpoint
- [ ] Basic WebSocket echo server (client connects, sends ping, receives pong)
- [ ] Mock client that runs on any Linux machine (no Pi hardware)
- [ ] Web UI skeleton (single HTML page, connects to WebSocket)

### Success Criteria
- Server starts without errors.
- Mock client connects to server and stays connected.
- Web UI shows connection status.

## Phase 1: Audio Pipeline (Weeks 3–4)
**Goal**: Doll can hear and speak.

### Deliverables
- [ ] Audio capture on Pi (microphone → PCM → WebSocket)
- [ ] Audio playback on Pi (WebSocket → PCM → speakers)
- [ ] Server-side VAD (`silero-vad`)
- [ ] Server-side STT (`faster-whisper`)
- [ ] Server-side TTS (`piper`)
- [ ] Basic conversation: speak → STT → echo text → TTS → play
- [ ] Web UI can send text and hear response

### Success Criteria
- End-to-end latency: speak → hear response < 5 seconds.
- Audio quality is intelligible.
- No crashes during 10-minute continuous test.

## Phase 2: Servo Control & Expressions (Weeks 5–6)
**Goal**: Doll can move its mouth and face.

### Deliverables
- [ ] PCA9685 servo driver integration on Pi
- [ ] Servo controller abstraction (set angle, run sequence)
- [ ] Mouth lip-sync (timed to TTS audio duration)
- [ ] Basic expressions: neutral, happy, sad, surprised, angry
- [ ] Web UI servo sliders for manual control
- [ ] "Expression" buttons in Web UI

### Success Criteria
- Servos move smoothly (no jitter).
- Mouth opens/closes in sync with speech (±200ms).
- Expressions are recognizable.
- Manual control from Web UI works in real-time.

## Phase 3: Video Pipeline & Vision (Weeks 7–8)
**Goal**: Doll can see and react to its environment.

### Deliverables
- [ ] Camera capture on Pi (JPEG encoding)
- [ ] Video streaming to server (WebSocket)
- [ ] Server-side vision LLM integration (`llava-phi3`)
- [ ] Emotion detection from video frames
- [ ] Gesture recognition (waving, pointing)
- [ ] Scene description (people count, mood, objects)
- [ ] Vision results feed into conversation context

### Success Criteria
- Frame capture → vision result < 2 seconds.
- Emotion detection accuracy > 70% (manual test with 10 expressions).
- Doll comments on what it sees (e.g., "I see a cake!")

## Phase 4: Conversation Engine (Weeks 9–10)
**Goal**: Doll feels alive and responsive.

### Deliverables
- [ ] Conversation state machine (IDLE → LISTENING → THINKING → SPEAKING)
- [ ] Interruption handling (user speaks while doll is speaking)
- [ ] Personality engine (Tedd-EH personality)
- [ ] Context management (last 20 messages, summarization)
- [ ] Vision integration into prompts (emotion-aware responses)
- [ ] Action planner (servo commands based on text + emotion)

### Success Criteria
- Natural conversation flow (no awkward pauses > 3 seconds).
- Interruption works 90% of the time.
- Personality is consistent and engaging.
- Doll reacts to emotions and gestures appropriately.

## Phase 5: Web Interface & Manual Control (Weeks 11–12)
**Goal**: Full web-based control and monitoring.

### Deliverables
- [ ] Dashboard with all connected dolls
- [ ] Live video feed in Web UI
- [ ] Chat interface (text + voice)
- [ ] Manual servo control panel
- [ ] Settings page (model selection, prompts, configuration)
- [ ] Mobile-responsive design

### Success Criteria
- Web UI loads in < 2 seconds.
- Video feed is smooth (> 2 FPS).
- All manual controls work without lag.
- Works on mobile browser.

## Phase 6: Multi-Doll Orchestration (Weeks 13–14)
**Goal**: Multiple dolls interact with each other.

### Deliverables
- [ ] Doll registration and discovery
- [ ] Shared context bus (Redis)
- [ ] Doll-to-doll overhearing
- [ ] Turn-taking enforcement
- [ ] Coordinated actions (group wave, sequential actions)
- [ ] Show controller (scripted performances)
- [ ] Multi-doll dashboard in Web UI

### Success Criteria
- 3 dolls can hold a coherent group conversation.
- Coordinated actions are synchronized (±500ms).
- Show script plays without errors.

## Phase 7: Hardware Integration & Refinement (Weeks 15–16)
**Goal**: Doll is physically robust and ready for parties.

### Deliverables
- [ ] Physical integration of Pi, camera, mic, speakers, servos into doll
- [ ] Power management (battery, charging, sleep mode)
- [ ] Wi-Fi auto-connect and mDNS discovery
- [ ] Boot-to-ready in < 30 seconds
- [ ] Error recovery (watchdog, auto-restart)
- [ ] Stress testing (4-hour continuous operation)

### Success Criteria
- Doll boots and connects automatically.
- Battery lasts > 2 hours.
- No crashes during 4-hour test.
- All hardware fits inside doll cavity.

## Phase 8: Advanced Features (Weeks 17–20)
**Goal**: Make it the life of the party.

### Deliverables
- [ ] Walking mechanism (if feasible)
- [ ] Additional appendages (ears, tail)
- [ ] LED eyes (NeoPixel or RGB)
- [ ] Sound effects and music playback
- [ ] Party games (trivia, Simon Says, charades)
- [ ] Long-term memory (vector DB, RAG)
- [ ] Voice cloning (custom voice for each doll)

### Success Criteria
- Walking is stable (if implemented).
- Party games are fun and engaging.
- Long-term memory works across sessions.
- Custom voices are recognizable.

## Testing Strategy

### Unit Tests
- Run on every commit (CI/CD).
- Coverage target: 80% for server, 70% for client.
- Mock all external dependencies (Ollama, hardware).

### Integration Tests
- Run before each release.
- End-to-end tests with mock client.
- Audio quality tests (PESQ or manual listening).
- Vision accuracy tests (labeled dataset).

### Hardware Tests
- Run on actual Pi hardware.
- Servo movement tests (range, speed, noise).
- Audio loopback tests (mic → server → speaker).
- Video quality tests (resolution, latency).
- Battery drain tests.

### Load Tests
- Simulate 10 concurrent dolls.
- Measure server CPU, RAM, GPU usage.
- Identify bottlenecks (STT, LLM, TTS).

## CI/CD Pipeline

### GitHub Actions (or similar)
```yaml
name: CI
on: [push, pull_request]
jobs:
  test-server:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -e ".[dev]"
      - run: pytest tests/server --cov=teddy_server --cov-report=xml
  test-client:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[dev]"
      - run: pytest tests/client --cov=teddy_client --cov-report=xml
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: pip install ruff black mypy
      - run: ruff check .
      - run: black --check .
      - run: mypy src/
```

## Documentation

### User Documentation
- `docs/setup.md`: How to set up the server and flash the Pi.
- `docs/hardware.md`: Step-by-step hardware assembly guide.
- `docs/usage.md`: How to use the Web UI and interact with the doll.
- `docs/troubleshooting.md`: Common issues and solutions.

### Developer Documentation
- `docs/architecture.md`: High-level architecture overview.
- `docs/api.md`: REST and WebSocket API reference.
- `docs/protocol.md`: Doll-server communication protocol.
- `docs/contributing.md`: How to contribute code.

## Milestones

| Milestone | Date | Description |
|-----------|------|-------------|
| M1: Hello World | Week 2 | Server + mock client + Web UI skeleton |
| M2: Talking Doll | Week 4 | Audio pipeline complete; doll speaks |
| M3: Animated Doll | Week 6 | Servos + expressions; doll moves |
| M4: Seeing Doll | Week 8 | Vision pipeline; doll reacts to environment |
| M5: Living Doll | Week 10 | Conversation engine; doll feels alive |
| M6: Controllable Doll | Week 12 | Full Web UI; manual control |
| M7: Social Doll | Week 14 | Multi-doll orchestration |
| M8: Party Doll | Week 16 | Hardware integrated; ready for parties |
| M9: Star Doll | Week 20 | Advanced features; life of the party |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Pi Zero 2 W too slow for video encoding | Medium | High | Use USB webcam with MJPEG; reduce resolution |
| Wi-Fi latency too high for real-time | Medium | High | Use 5GHz if available; reduce audio quality |
| Servo noise ruins audio | Medium | Medium | Isolate servos mechanically; noise gate in software |
| Ollama models too slow on CPU | High | High | Use smaller models; upgrade server hardware; use GPU |
| Doll cavity too small for hardware | Medium | High | Use Pi Zero (smallest); 3D-print custom brackets |
| Battery life too short | Medium | Medium | Use larger battery; reduce CPU frequency; sleep mode |
| Whisper hallucinates / poor STT | Medium | Medium | Use VAD filtering; post-process with LLM |
| Vision LLM inaccurate | Medium | Medium | Use multiple frames; ensemble models; fallback prompts |
