# Project Overview: Tedd-EH

## Vision
Transform a vintage animatronic doll into an interactive, AI-powered companion using a Raspberry Pi, server-side LLM processing via Ollama, and a web-based control interface. The system is designed to scale from a single doll to a fleet of animated characters.

## Core Concept
The doll becomes a distributed AI agent:
- **Edge (Doll)**: Lightweight Raspberry Pi (potentially Zero) handling audio capture, video capture, servo control, and network communication.
- **Server**: Powerful machine running Ollama with multiple LLMs for conversation, emotion detection, action planning, and voice synthesis.
- **Web UI**: Browser-based interface for monitoring, configuring, and manually interacting with one or more dolls.

## Key Design Constraints
1. **Minimal Edge Compute**: Raspberry Pi Zero has limited CPU/RAM; all heavy AI inference happens server-side.
2. **Low Latency**: Audio/video streams and command responses must feel natural (target <500ms for simple responses).
3. **Cross-Platform Server**: Must run on both Linux and FreeBSD.
4. **Python-First**: All application code written in Python 3.11+.
5. **Extensible**: Architecture must support adding new dolls, new capabilities (walking, appendages), and new LLM models without rewrites.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SERVER (Linux/FreeBSD)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Ollama     │  │   Ollama     │  │   Ollama     │  │   TTS Engine     │  │
│  │  (Chat LLM)  │  │ (Vision LLM) │  │ (Action LLM) │  │  (Piper/Coqui)   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────────────────┘  │
│         │                 │                 │                                 │
│  ┌──────┴─────────────────┴─────────────────┴────────────────────────────┐  │
│  │                     Tedd-EH Server (Python/FastAPI)                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │  Session    │  │   Audio     │  │   Video     │  │   Action    │  │  │
│  │  │  Manager    │  │  Pipeline   │  │  Pipeline   │  │  Planner    │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌─────────────────────────────────┴────────────────────────────────────┐  │
│  │                         Web Interface (React/Vue)                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                         WebSocket / gRPC
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EDGE (Raspberry Pi Zero/3/4)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  USB Mic     │  │  USB Webcam  │  │   Speakers   │  │  Servo Controller │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────────────────┘  │
│         │                 │                 │                                 │
│  ┌──────┴─────────────────┴─────────────────┴────────────────────────────┐  │
│  │                     Tedd-EH Client (Python/asyncio)                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │  Audio I/O   │  │  Video I/O   │  │  Servo Drv  │  │  Net Client │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Document Index
1. `01-project-overview.md` — This document
2. `02-hardware-specification.md` — Doll hardware, Raspberry Pi selection, sensors, actuators
3. `03-server-architecture.md` — Server-side design, Ollama integration, API design
4. `04-client-architecture.md` — Raspberry Pi client, audio/video capture, servo control
5. `05-web-interface.md` — Web UI design, real-time dashboards, manual controls
6. `06-audio-pipeline.md` — Speech-to-text, TTS, audio streaming, noise cancellation
7. `07-video-pipeline.md` — Video capture, emotion detection, gesture recognition
8. `08-conversation-engine.md` — Natural dialogue flow, context management, interruption handling
9. `09-multi-doll-orchestration.md` — Scaling to multiple dolls, load balancing, doll-to-doll interaction
10. `10-development-roadmap.md` — Phased development plan, milestones, testing strategy
