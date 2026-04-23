# Multi-Doll Orchestration

## Overview
While a single doll is charming, the real magic happens when multiple dolls interact with each other and with a room full of people. This document describes how to scale from one doll to many, manage their interactions, and create coordinated performances.

## Scenarios

### Scenario 1: The Party
- 3–5 dolls placed around a room.
- Each doll can see and hear its local area.
- Dolls can "overhear" each other and join conversations.
- Coordinated group responses (singing together, telling a story in rounds).

### Scenario 2: The Show
- 2 dolls on a "stage" (table).
- Scripted dialogue with improvisation.
- One doll is the "straight man," the other is the "comic."
- Audience can shout questions; dolls respond.

### Scenario 3: The Parade
- Dolls on mobile platforms (walking).
- Follow a leader doll.
- Respond to crowd as they pass.

## Architecture

### Single Server, Multiple Dolls
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             TEDD-EH SERVER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  Doll A     │  │  Doll B     │  │  Doll C     │  │  Orchestrator   │  │
│  │  Session    │  │  Session    │  │  Session    │  │                 │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────────────────┘  │
│         │                │                │                                 │
│  ┌──────┴────────────────┴────────────────┴─────────────────────────────┐  │
│  │                         Shared Context Bus (Redis)                   │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Orchestrator Service
A dedicated service that monitors all doll sessions and decides when dolls should interact.

```python
class Orchestrator:
    def __init__(self, redis: Redis):
        self.dolls: dict[str, DollSession] = {}
        self.redis = redis

    async def on_doll_speak(self, doll_id: str, text: str):
        """Called when any doll speaks. Broadcast to others."""
        for other_id, session in self.dolls.items():
            if other_id != doll_id:
                await session.inject_context(
                    f"[Overheard] {self.dolls[doll_id].name} said: '{text}'"
                )

    async def coordinate_action(self, action_name: str, doll_ids: list[str]):
        """Trigger a synchronized action across multiple dolls."""
        await asyncio.gather(*[
            self.dolls[did].trigger_action(action_name)
            for did in doll_ids
        ])
```

## Doll-to-Doll Communication

### Overhearing
- When Doll A speaks, the server broadcasts the text to all other dolls as a "system" message.
- Other dolls can choose to respond (or not) based on relevance.
- Example:
  ```
  Doll A: "I love cake!"
  Doll B (overhears): "Me too! Chocolate or vanilla?"
  Doll C (overhears): "*drools*"
  ```

### Direct Addressing
- A doll can address another by name: "Hey Doll-02, what do you think?"
- The server parses the text and routes the "question" to the addressed doll.
- The addressed doll gets a priority boost in its response queue.

### Turn-Taking
- The orchestrator enforces a "no talking over each other" rule.
- If two dolls try to speak simultaneously, the orchestrator delays one by 1–2 seconds.
- Natural turn-taking: "You go first, Doll-02."

## Coordinated Actions

### Group Expressions
```python
async def group_expression(expression: str, doll_ids: list[str]):
    """All dolls show the same expression simultaneously."""
    await orchestrator.coordinate_action(f"expression:{expression}", doll_ids)
```

### Sequential Actions
```python
async def sequential_wave(doll_ids: list[str], delay_ms: int = 500):
    """Dolls wave one after another (the wave)."""
    for did in doll_ids:
        await orchestrator.dolls[did].trigger_action("wave")
        await asyncio.sleep(delay_ms / 1000)
```

### Chorus / Singing
- Pre-scripted lyrics split across dolls.
- Server sends each doll its lines with precise timing.
- Dolls lip-sync to their assigned parts.

## Load Balancing

### Ollama Model Management
- Each doll session may use the same LLM models.
- Ollama keeps models loaded in memory; concurrent requests are queued.
- If server has GPU, batch requests when possible.
- If CPU-only, limit concurrent LLM calls to avoid thrashing.

### Session Isolation
- Each doll has its own conversation context.
- Vision LLM calls are independent per doll.
- TTS generation is independent per doll.

### Resource Limits
| Resource | Limit | Action |
|----------|-------|--------|
| Concurrent LLM calls | 4 | Queue additional requests |
| Concurrent TTS calls | 8 | Piper is fast; usually not a bottleneck |
| Concurrent STT calls | 4 | Whisper is the heaviest |
| Total dolls | 20 | Beyond this, consider multiple servers |

## Scaling Beyond One Server

### Multi-Server Setup
If the party grows beyond ~20 dolls:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Server 1   │◀───▶│   Redis     │◀───▶│  Server 2   │
│ (Dolls 1-10)│     │  (Pub/Sub)  │     │ (Dolls 11-20)│
└─────────────┘     └─────────────┘     └─────────────┘
```

- Redis acts as the shared context bus.
- Dolls connect to their assigned server (round-robin or by room).
- Cross-server doll communication goes through Redis.

## Configuration

### Doll Roles
Each doll can have a role that affects its personality and behavior:
```yaml
dolls:
  - id: teddy-01
    name: "Tedd-EH"
    role: "host"
    personality: "warm, welcoming, tells jokes"
  - id: teddy-02
    name: "Grubby"
    role: "sidekick"
    personality: "silly, clumsy, loves food"
  - id: teddy-03
    name: "Newton"
    role: "intellectual"
    personality: "smart, trivia-loving, slightly nerdy"
```

### Room Configuration
```yaml
rooms:
  - name: "living_room"
    dolls: ["teddy-01", "teddy-02"]
    mode: "party"
  - name: "stage"
    dolls: ["teddy-01", "teddy-02", "teddy-03"]
    mode: "show"
    script: "birthday_show.json"
```

## Web UI for Multi-Doll

### Dashboard
- Grid view of all dolls across all rooms.
- Color-coded by room.
- Group controls: "Mute All", "Make All Wave", "Start Show".

### Show Controller
- Upload a JSON script with timed actions.
- Play / Pause / Stop buttons.
- Live editing of scripts.

### Script Format
```json
{
  "name": "Birthday Song",
  "duration_ms": 60000,
  "tracks": [
    {
      "doll_id": "teddy-01",
      "events": [
        {"time_ms": 0, "action": "speak", "text": "Happy birthday to you!"},
        {"time_ms": 2000, "action": "servo", "channel": 5, "angle": 180},
        {"time_ms": 4000, "action": "expression", "name": "happy"}
      ]
    },
    {
      "doll_id": "teddy-02",
      "events": [
        {"time_ms": 0, "action": "speak", "text": "Happy birthday to you!"},
        {"time_ms": 3000, "action": "servo", "channel": 5, "angle": 180}
      ]
    }
  ]
}
```

## Security & Isolation

### Doll Authentication
- Each doll has a unique JWT token.
- Tokens are scoped to a specific server and room.
- Compromised doll token cannot access other rooms.

### Rate Limiting
- Per-doll rate limits on LLM calls (prevent runaway loops).
- Global rate limit on total concurrent sessions.

### Privacy
- Dolls in different rooms cannot overhear each other by default.
- Cross-room communication requires explicit configuration.
