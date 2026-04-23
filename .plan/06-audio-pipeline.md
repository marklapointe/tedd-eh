# Audio Pipeline

## Overview
The audio pipeline handles everything related to sound: capturing the user's voice, detecting when they are speaking, converting speech to text, generating responses as speech, and synchronizing mouth movements. All heavy processing happens on the server; the Pi only captures and plays raw PCM.

## Pipeline Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Microphone │────▶│  Pre-process │────▶│     VAD     │────▶│   Buffer    │
│  (Pi, 16kHz) │     │ (gain, HPF)  │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐
│   Speaker   │◀────│   Playback   │◀────│  TTS Engine  │◀────│     LLM     │
│ (Pi, 22kHz) │     │  (buffered)  │     │   (Piper)    │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   ▲
                                                                   │
                                                            ┌──────┴──────┐
                                                            │     STT     │
                                                            │  (Whisper)  │
                                                            └─────────────┘
```

## 1. Audio Capture (Pi)

### Configuration
- **Sample Rate**: 16,000 Hz (Whisper's native rate)
- **Bit Depth**: 16-bit signed integer (PCM)
- **Channels**: Mono
- **Frame Size**: 20ms (320 samples = 640 bytes)
- **Device**: ALSA `default` or `plughw:1,0`

### Implementation
```python
import sounddevice as sd

stream = sd.RawInputStream(
    samplerate=16000,
    dtype='int16',
    channels=1,
    blocksize=320,  # 20ms
    callback=audio_callback
)
```

### Pre-Processing (Server)
- **High-Pass Filter**: 80Hz cutoff to remove rumble
- **Noise Gate**: -40dB threshold to suppress background hum
- **Automatic Gain Control (AGC)**: Normalize to -12dB RMS
- **Resampling**: Not needed if capture is already 16kHz

## 2. Voice Activity Detection (VAD)

### Options
| Engine | Speed | Accuracy | Resource | Notes |
|--------|-------|----------|----------|-------|
| `webrtcvad` | Very fast | Good | Low | 10/20/30ms frames only |
| `silero-vad` | Fast | Excellent | Medium | ONNX, works at any frame size |
| `snakers4/silero-vad` (PyTorch) | Medium | Excellent | High | Best quality, more RAM |

### Choice: `silero-vad` (ONNX)
- Good balance of speed and accuracy
- Works with 30ms frames
- ~5MB model, loads in <1s

### VAD Logic
```python
class VADProcessor:
    def __init__(self):
        self.model = silero_vad.load_silero_vad(onnx=True)
        self.threshold = 0.5
        self.speech_pad_ms = 300  # padding before/after speech
        self.min_speech_duration_ms = 250
        self.max_speech_duration_s = 30  # force split after 30s

    def process(self, pcm_chunk: bytes) -> list[bytes]:
        """Returns list of complete speech segments."""
        ...
```

### Behavior
- Stream audio continuously from Pi
- Run VAD on server in real-time
- When speech segment is complete (silence >500ms), send to STT
- If speech exceeds 30 seconds, force-split and process

## 3. Speech-to-Text (STT)

### Engine: `faster-whisper`
- **Model**: `base` (74M params) for speed; `small` (244M) if GPU available
- **Compute**: CPU on server (Pi too slow)
- **Language**: Auto-detect or fixed per doll config
- **Beam Size**: 5
- **Best-of**: 5
- **Condition on Previous Text**: True (for context)

### Latency Optimization
- **Chunked Inference**: Process VAD segments as they complete
- **VAD + Whisper Alignment**: Use VAD timestamps to trim silence
- **Temperature Fallback**: 0.0 → 0.2 → 0.4 if decoding fails
- **No Condition on Previous Text**: For first utterance to avoid hallucination

### Implementation
```python
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")

segments, info = model.transcribe(
    audio_np_array,
    beam_size=5,
    best_of=5,
    condition_on_previous_text=True,
    vad_filter=True,  # built-in VAD as safety net
    vad_parameters=dict(min_silence_duration_ms=500)
)
text = " ".join([s.text for s in segments])
```

### Expected Latency
| Utterance Length | CPU (i5) | GPU (RTX 3060) |
|------------------|----------|----------------|
| 2 seconds | 300ms | 80ms |
| 5 seconds | 600ms | 150ms |
| 10 seconds | 1.2s | 300ms |

## 4. Text-to-Speech (TTS)

### Engine: Piper
- **Speed**: Real-time factor >10x on CPU
- **Quality**: Natural, expressive
- **Size**: ~50MB per voice
- **Format**: ONNX models

### Voice Selection
| Voice | Gender | Style | Size |
|-------|--------|-------|------|
| `en_US-lessac-medium` | Female | Neutral | 50MB |
| `en_US-ryan-high` | Male | Warm | 100MB |
| `en_GB-southern_english_female-medium` | Female | Friendly | 50MB |

### Implementation
```python
from piper import PiperVoice

voice = PiperVoice.load("en_US-lessac-medium.onnx")
synthesized = voice.synthesize_stream_raw("Hello there!")
# Returns generator of PCM 16-bit 22050Hz mono chunks
```

### Streaming TTS
- Start streaming audio chunks to Pi as soon as first chunk is synthesized
- Do not wait for full synthesis
- Target: first audio byte within 200ms of receiving text

### Lip Sync
- Approximate syllable count from text: `len(text.split()) * 1.2`
- Calculate mouth open/close timing based on audio duration
- Send servo commands interleaved with audio chunks

```python
def generate_lip_sync(text: str, audio_duration_ms: int) -> list[ServoCommand]:
    syllables = estimate_syllables(text)
    spm = syllables / (audio_duration_ms / 1000)
    # Generate mouth angles timed to syllable boundaries
    ...
```

## 5. Audio Playback (Pi)

### Configuration
- **Sample Rate**: 22,050 Hz (Piper's output rate)
- **Bit Depth**: 16-bit signed integer
- **Channels**: Mono
- **Buffer**: 200ms (4410 samples) to absorb network jitter

### Implementation
```python
import sounddevice as sd
import numpy as np

playback_buffer = np.array([], dtype=np.int16)

stream = sd.RawOutputStream(
    samplerate=22050,
    dtype='int16',
    channels=1,
    blocksize=441,  # 20ms
    callback=playback_callback
)

def playback_callback(outdata, frames, time, status):
    if len(playback_buffer) >= frames:
        outdata[:] = playback_buffer[:frames].reshape(-1, 1)
        playback_buffer = playback_buffer[frames:]
    else:
        outdata[:len(playback_buffer)] = playback_buffer.reshape(-1, 1)
        outdata[len(playback_buffer):] = 0
        playback_buffer = np.array([], dtype=np.int16)
```

### Interruption Handling
- When new `audio_response` arrives while playing:
  1. Clear playback buffer
  2. Stop current audio output
  3. Start new audio stream
  4. Send "mouth close" servo command

## 6. Noise Cancellation (Optional)

### Echo Cancellation
- Not needed if speaker and mic are physically separated inside the doll
- If feedback occurs, implement simple AEC with `speexdsp` or `webrtc-audio-processing`

### Background Noise Suppression
- `rnnoise` (Xiph) for real-time noise suppression
- Run on server before VAD
- ~1ms latency, very low CPU

## 7. Audio Formats & Encoding

### Pi → Server
- Raw PCM s16le, 16kHz, mono
- No compression (CPU cost on Pi)
- Frame size: 20ms (640 bytes)

### Server → Pi
- Raw PCM s16le, 22kHz, mono
- No compression
- Chunk size: variable (as generated by TTS)

### Browser → Server (Web UI)
- Opus in WebM container (MediaRecorder default)
- Server decodes to PCM using `ffmpeg` or `libopus`

## 8. Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Capture → STT text | <2s for 5s utterance | VAD + Whisper |
| STT text → first TTS byte | <1s | LLM + Piper streaming |
| Total user speaks → doll speaks | <3s | End-to-end |
| Audio streaming latency | <100ms | Network + buffer |
| Mouth sync accuracy | ±100ms | Approximate is acceptable |
