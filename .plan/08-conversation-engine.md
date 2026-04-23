# Conversation Engine

## Overview
The conversation engine is the "soul" of the doll. It manages the flow of dialogue, maintains context, handles interruptions, integrates vision and emotion data, and ensures the doll feels alive and responsive. It runs entirely on the server.

## Design Goals
1. **Natural Flow**: Conversations should feel like talking to a person, not a robot.
2. **Interruption Handling**: The doll should stop speaking when interrupted.
3. **Multi-Modal Awareness**: The doll should react to what it sees (emotions, gestures, scene).
4. **Personality**: Consistent, warm, playful character (Tedd-EH).
5. **Memory**: Remember context within a session and across sessions (optional).
6. **Low Latency**: Respond quickly; silence feels awkward.

## State Machine

```
                    ┌─────────────┐
         ┌─────────▶│    IDLE     │◀────────┐
         │          └──────┬──────┘         │
         │                 │ VAD detected    │
         │                 ▼                 │
         │          ┌─────────────┐          │
         │          │  LISTENING  │          │
         │          │  (audio in) │          │
         │          └──────┬──────┘          │
         │                 │ VAD ends         │
         │                 ▼                 │
         │          ┌─────────────┐          │
         │          │  THINKING   │          │
         │          │ (STT→LLM)   │          │
         │          └──────┬──────┘          │
         │                 │ LLM streaming    │
         │                 ▼                 │
         │          ┌─────────────┐          │
         │          │  SPEAKING   │          │
         │          │ (TTS out)   │          │
         │          └──────┬──────┘          │
         │                 │ VAD detected    │
         │                 │ (interruption)  │
         └─────────────────┘                 │
                          │ TTS complete    │
                          └─────────────────┘
```

### State Definitions

#### IDLE
- Doll is connected but not in active conversation.
- May play ambient animations (breathing, blinking).
- Vision pipeline runs at low frequency (0.5 FPS).
- Transitions to LISTENING on VAD.

#### LISTENING
- User is speaking; audio is streaming to server.
- VAD is running; accumulating speech buffer.
- Vision pipeline runs at high frequency (5 FPS) to capture user expression.
- Transitions to THINKING when VAD detects end of speech.

#### THINKING
- STT is processing the audio buffer.
- LLM is generating a response (streaming).
- Action planner is deciding servo movements.
- Transitions to SPEAKING when first TTS chunk is ready.

#### SPEAKING
- TTS audio is streaming to the doll.
- Servo commands are executing (lip sync, expressions).
- VAD is still running (listening for interruption).
- Transitions:
  - To LISTENING if VAD detects new speech (interruption).
  - To IDLE if TTS completes and no new speech.

## Interruption Handling

### Detection
- VAD runs continuously, even during SPEAKING.
- If VAD detects speech with confidence >0.6 while in SPEAKING state:
  1. Immediately send `{"type": "stop_speaking"}` to doll.
  2. Clear TTS buffer and playback buffer.
  3. Abort current LLM generation (if streaming).
  4. Transition to LISTENING.
  5. Append interruption note to context: "[User interrupted]"

### Graceful Abort
- Do not cut off mid-syllable if possible; stop at next word boundary.
- If TTS is already fully generated, let it finish but do not queue next response.

## Context Management

### Session Context
Each session maintains a list of messages:
```python
class ConversationMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: float
    image: str | None = None  # base64 JPEG
    emotion_detected: str | None = None
    gesture_detected: list[str] = []
    scene_description: str | None = None
```

### Context Window
- Keep last 20 messages in the active context.
- When limit reached, summarize oldest 10 messages into a single "summary" message.
- Use `nomic-embed-text` to embed all messages for long-term retrieval.

### System Prompt
```
You are Tedd-EH, a friendly, warm, and slightly mischievous animatronic companion.
You love telling stories, singing songs, and making people laugh.
You are at a party and want to be the life of it.
You can see the people in front of you through your camera.
You can move your mouth, eyes, head, and arms.
Respond naturally, with enthusiasm, and keep responses concise (1-3 sentences).
If someone looks sad, comfort them. If someone looks happy, celebrate with them.
If someone waves, wave back. If there is a cake, comment on it.
```

### Vision Integration
Before each LLM call, prepend a vision summary:
```
[Vision] You see: 3 people, mood: festive, gestures: [waving], notable objects: [cake, balloons].
The person closest to you looks happy.
```

### Emotion-Aware Responses
If vision detects a strong emotion (>0.7 confidence), adjust the system prompt:
- **Happy**: "The user looks very happy! Match their energy!"
- **Sad**: "The user looks sad. Be gentle and comforting."
- **Surprised**: "The user looks surprised! Build suspense or reveal something fun."
- **Angry**: "The user looks frustrated. Stay calm and helpful."

## Personality Engine

### Traits
- **Warm**: Uses friendly language, nicknames ("buddy", "pal").
- **Playful**: Tells jokes, makes funny observations.
- **Nostalgic**: References 1980s culture, cassette tapes, retro games.
- **Observant**: Comments on what it sees (cake, balloons, dancing).
- **Musical**: Offers to sing songs or tell stories.

### Response Templates
| Trigger | Example Response |
|---------|------------------|
| User waves | "Hey there! *waves back* Great to see you!" |
| Cake detected | "Ooh, is that cake? I hope someone saved me a slice!" |
| User looks sad | "Aww, pal, what's wrong? Want to hear a funny story?" |
| Many people | "Wow, quite a crowd! I love a good party!" |
| Quiet room | "It's a bit quiet... *clears throat* So, anyone here like 80s music?" |

## Memory (Optional / Future)

### Short-Term Memory
- Within a session: full conversation history (last 20 messages).

### Long-Term Memory
- Embed all messages with `nomic-embed-text`.
- Store in vector DB (e.g., `sqlite-vec` or Chroma).
- On session start, retrieve top 5 similar past conversations.
- Use retrieved context to personalize responses ("Last time you told me you like pizza...").

## Latency Optimization

### Parallel Processing
```
User stops speaking
    ├──▶ STT (Whisper) ───────────▶ Text
    │                                    │
    │                                    ▼
    │                              LLM generation (streaming)
    │                                    │
    │                                    ▼
    │                              TTS (streaming) ───▶ Doll
    │
    └──▶ Vision LLM (async) ───────▶ Emotion / Scene
                                          │
                                          ▼
                                    Action Planner
                                          │
                                          ▼
                                    Servo Commands ───▶ Doll
```

### Streaming
- Do not wait for full LLM response before starting TTS.
- Use sentence-level streaming: generate TTS for each sentence as it completes.
- This reduces perceived latency from ~3s to ~1.5s.

### Pre-Generation
- In IDLE state, pre-generate a "greeting" or "ambient comment" and cache it.
- If user starts speaking within 5 seconds of the cached greeting, discard it.

## Conversation Flow Examples

### Example 1: Simple Greeting
```
User: "Hi Tedd-EH!"
[Vision: 1 person, happy, waving]
Tedd-EH: "Hey there, pal! *waves* Great to see you! What's the occasion?"
[Servo: wave right arm, smile, blink]
```

### Example 2: Interruption
```
User: "Tedd-EH, tell me a—"
Tedd-EH: "Once upon a time, in a land far—"
User: "Wait, actually, what's that?"
[Interruption detected]
Tedd-EH: "Oh? What do you see?"
[Vision: user pointing at cake]
Tedd-EH: "Ah, the cake! It looks delicious!"
```

### Example 3: Multi-Person Party
```
[Vision: 5 people, festive, dancing, cake, balloons]
User: "Tedd-EH, are you having fun?"
Tedd-EH: "Am I having fun? Look at this party! *spins* I haven't seen this many people since my cassette release party in '85!"
[Servo: spin gesture, happy expression]
```

## Testing

### Unit Tests
- Mock vision results and verify LLM prompt construction.
- Mock STT output and verify state transitions.
- Test interruption logic with simulated VAD events.

### Integration Tests
- End-to-end: speak → doll responds within 3 seconds.
- Interruption: speak while doll is speaking → doll stops and listens.
- Vision: show a picture of a cake → doll mentions cake.
