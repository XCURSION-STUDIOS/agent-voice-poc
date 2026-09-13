# Jarvis Voice POC

A deliberately small, provider-configurable, real-time voice assistant built on Pipecat. It is a modular `WebRTC → streaming STT → streaming LLM → streaming TTS → WebRTC` pipeline—not OpenAI Realtime. Defaults: `gpt-5.6-luna`, Deepgram Nova STT, and OpenAI `gpt-4o-mini-tts` at 24 kHz.

## Architectural decisions

- **Transport:** Pipecat SmallWebRTCTransport. It is Pipecat's low-latency direct browser transport intended for local development and demos.
- **Defaults:** Deepgram streaming STT, OpenAI `gpt-5.6-luna` for the normal streaming LLM API, and OpenAI `gpt-4o-mini-tts` for speech. Each is selected only in `backend/app/pipeline/providers.py` through environment configuration.
- **Conversation feel:** Pipecat's `SileroVADAnalyzer`, universal LLM context aggregator, and user-turn strategy own turn completion and barge-in cancellation. No custom audio, VAD, or interruption loop is implemented.
- **Context:** Pipecat's in-session `LLMContext` retains the conversation and disappears on disconnect.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node 20+
- Deepgram and OpenAI API keys

## Run locally

```powershell
Copy-Item backend/.env.example backend/.env
# Fill in the two API keys in backend/.env

cd backend
uv sync
uv run python -m app.main --transport webrtc
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite address (normally http://localhost:5173), allow microphone access, then choose **Start conversation**. Use headphones while testing barge-in to avoid speaker audio being picked up as an interruption.

## Provider configuration

`.env` is the provider boundary. The supported values are `STT_PROVIDER=deepgram`, `LLM_PROVIDER=openai`, and `TTS_PROVIDER=openai` or `TTS_PROVIDER=deepgram`. OpenAI TTS is the quality-test default; Deepgram remains available with the existing API key for a direct comparison. Add a service in `backend/app/pipeline/providers.py`; the transport, VAD, browser client, and pipeline layout do not change.

To switch back to Deepgram Aura, set `TTS_PROVIDER=deepgram` and choose a `DEEPGRAM_TTS_VOICE`. To tune the OpenAI option, change `OPENAI_TTS_VOICE` or `OPENAI_TTS_INSTRUCTIONS`, then restart the backend.

## Measurement

Pipecat's worker is started with both metrics and usage metrics enabled. `MetricsLogObserver` logs LLM/TTS TTFB, processing time, LLM tokens, and TTS characters; `UserBotLatencyObserver` logs speech-end to first bot audio plus the chronological service breakdown. The browser receives the same RTVI metrics and can be extended to persist a session cost report once real provider pricing is chosen. `backend/app/metrics/latency.py` is a provider-neutral timing ledger for any additional browser-arrival instrumentation.

## Scope deliberately excluded

No authentication, persistence, tools, external agents, databases, LiveKit/Daily, deployment, or OpenAI Realtime are part of this POC.
