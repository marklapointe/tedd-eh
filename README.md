# Tedd-EH

Bring a vintage animatronic doll to life with a Raspberry Pi, AI, and a whole lot of personality.

This project is an AI-powered doll orchestration system. A Raspberry Pi (even a Pi Zero) inside the doll streams audio and video to a server running Large Language Models (via Ollama). The server handles speech-to-text, conversation, text-to-speech, and vision processing, then sends commands back to the doll for movement, expressions, and speech.

## Quick Start

The fastest way to get running on Ubuntu:

```bash
make run
```

This single command will:
1. Create a Python virtual environment (`.venv/`)
2. Install all server dependencies
3. Start the Tedd-EH Server on [http://localhost:8000](http://localhost:8000)

Then open your browser to:
- **Dashboard:** [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

## Prerequisites

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip make git
```

Python 3.11 or newer is required.

### macOS

```bash
brew install python@3.12 make git
```

### FreeBSD

```bash
pkg install python312 py312-pip gmake git
```

> Note: On FreeBSD, use `gmake` instead of `make`.

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd teddy
   ```

2. **Set up the environment and install dependencies:**
   ```bash
   make install
   ```

   This creates a `.venv/` virtual environment and installs the `teddy-server` package in editable mode with all development dependencies.

## Running

### Start the Server

```bash
make run
```

The server starts on `0.0.0.0:8000` with auto-reload enabled for development.

### Start the Server (without reinstalling)

If you already ran `make install` and just want to start the server:

```bash
make run-server
```

### Run a Mock Doll Client

To test the server without physical hardware, start a mock doll that connects via WebSocket:

```bash
make run-mock-client
```

### Run a Full Demo (server + mock client)

```bash
make run-demo
```

This starts the server in the background and then connects a mock doll client.

## Available Make Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make venv` | Create the Python virtual environment |
| `make install` | Install server dependencies into `.venv` |
| `make install-dev` | Install all dev dependencies (same as install) |
| `make run` | **Build env + start the server** |
| `make run-server` | Start the server only |
| `make run-mock-client` | Start a mock doll client |
| `make run-demo` | Start server + mock client together |
| `make test` | Run the test suite |
| `make test-cov` | Run tests with coverage report |
| `make lint` | Run the linter (ruff) |
| `make format` | Auto-format code with ruff |
| `make clean` | Remove `.venv/` and all build artifacts |

## Project Structure

```
teddy/
├── Makefile                  # Build automation
├── LICENSE                   # BSD-3-Clause license
├── README.md                 # This file
├── .plan/                    # Architecture & planning documents
│   ├── 01-project-overview.md
│   ├── 02-hardware-specification.md
│   ├── 03-server-architecture.md
│   ├── 04-client-architecture.md
│   ├── 05-web-interface.md
│   ├── 06-audio-pipeline.md
│   ├── 07-video-pipeline.md
│   ├── 08-conversation-engine.md
│   ├── 09-multi-doll-orchestration.md
│   └── 10-development-roadmap.md
├── teddy-server/             # FastAPI server (Python)
│   ├── pyproject.toml
│   ├── README.md
│   ├── src/teddy_server/     # Server source code
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── api/              # REST API routes
│   │   ├── core/             # Doll registry, session manager
│   │   ├── models/           # Pydantic data models
│   │   ├── services/         # WebSocket handlers
│   │   ├── static/           # Web dashboard (HTML/CSS/JS)
│   │   └── mock_client.py    # Mock doll for testing
│   └── tests/                # pytest test suite
└── teddy-webui/              # Future web UI components
```

## Server Architecture

The `teddy-server` is a FastAPI application that provides:

- **REST API** for doll registration, session management, and control commands
- **WebSocket endpoints** for real-time communication with dolls and the operator dashboard
- **Web Dashboard** served at `/static/index.html` for monitoring and manual control
- **Ollama integration** (planned) for LLM-powered conversation and vision

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | API info and links |
| `GET /docs` | Interactive OpenAPI documentation |
| `GET /dashboard` | Dashboard redirect |
| `GET /static/index.html` | Web control dashboard |
| `GET /api/health` | Health check |
| `GET /api/dolls` | List registered dolls |
| `POST /api/dolls` | Register a new doll |
| `POST /api/sessions` | Create a conversation session |
| `WS /ws/doll/{doll_id}` | Doll client WebSocket |
| `WS /ws/operator` | Operator dashboard WebSocket |

## Development

### Running Tests

```bash
make test
```

### Linting and Formatting

```bash
make lint
make format
```

### Manual Setup (without Make)

If you prefer not to use `make`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
cd teddy-server
pip install -e ".[dev]"
python -m uvicorn teddy_server.main:app --reload --host 0.0.0.0 --port 8000
```

## Hardware (Future)

The doll client will run on a Raspberry Pi Zero 2 W (or better) with:
- USB microphone
- Mini webcam
- Audio amplifier + speaker
- PCA9685 servo driver for animatronics
- LiPo battery + boost converter

See `.plan/02-hardware-specification.md` for the full BOM and wiring details.

## Roadmap

This project is in early development. See `.plan/10-development-roadmap.md` for the full 9-phase roadmap, including:

1. Foundation (server skeleton, API, tests) -- **Current phase**
2. Audio pipeline (STT, TTS, VAD)
3. Servo control and expressions
4. Video pipeline and vision LLM
5. Conversation engine and personality
6. Web UI polish
7. Multi-doll orchestration
8. Hardware integration
9. Advanced features (walking, show scripts)

## License

BSD-3-Clause. See [LICENSE](LICENSE) for details.
