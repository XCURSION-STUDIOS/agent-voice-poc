# Jarvis Voice POC

A deliberately small, provider-configurable, real-time voice assistant built on Pipecat. It is a modular `WebRTC → streaming STT → streaming LLM → streaming TTS → WebRTC` pipeline—not OpenAI Realtime. Defaults: `gpt-5.6-luna`, Deepgram Nova STT, and OpenAI `gpt-4o-mini-tts` at 24 kHz.

## Architectural decisions

- **Transport:** Pipecat SmallWebRTCTransport. It is Pipecat's low-latency direct browser transport intended for local development and demos.
- **Defaults:** Deepgram streaming STT, OpenAI `gpt-5.6-luna` for the normal streaming LLM API, and OpenAI `gpt-4o-mini-tts` for speech. Each is selected only in `backend/app/pipeline/providers.py` through environment configuration.
- **Conversation feel:** Pipecat's `SileroVADAnalyzer`, universal LLM context aggregator, and user-turn strategy own turn completion and barge-in cancellation. No custom audio, VAD, or interruption loop is implemented.
- **Context:** Pipecat's in-session `LLMContext` retains the conversation and disappears on disconnect.
- **Calendar specialist:** Calendar tools are registered on a per-session `CalendarAgent`. When
  `NOTION_API_KEY` and `NOTION_DATABASE_ID` are configured, it reads and creates records in the Content Calendar data source using the `Film date` property used by the database's Calendar view.
- **Live clock:** The `get_current_datetime` tool provides the current date and time in `USER_TIMEZONE`. The assistant uses it for "today", "now", tomorrow, and other relative-date requests instead of guessing.
- Spoken calendar times without an explicit offset are interpreted in `USER_TIMEZONE` before being sent to Notion, so saying “12 PM” does not silently become a UTC time.

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

Set the timezone used for calendar interpretation and current-time answers with an IANA timezone name, for example:

```powershell
USER_TIMEZONE=Asia/Singapore
```

After changing it, restart the backend.

## Test the calendar agent directly

You can test Notion event creation without starting the voice client:

```powershell
cd backend
uv sync
uv run python -m scripts.test_calendar_agent
```

The script previews the event, checks for conflicts, and asks for confirmation before writing. For a non-interactive test, pass `--title`, `--start`, `--end`, and `--yes`.

Example:

```powershell
uv run python -m scripts.test_calendar_agent `
  --title "Record YouTube video" `
  --start "2026-09-21T14:00:00+08:00" `
  --end "2026-09-21T15:00:00+08:00"
```

## Todo agent

The voice assistant can also work with the existing Todo List database. Try commands such as:

- “Add buy groceries to my todo list.”
- “What tasks are still not started?”
- “Mark the groceries task as done.”
- “Change the priority of the video task to high.”
- “Add a note to the groceries task: get oat milk too.”
- “Remove the duplicate task.”

The Todo agent uses `Task name`, `Status`, `Details`, `Due date`, `Priority`, `Category/Project`, and `Estimated time`. It asks for confirmation before completing or archiving a task, and it identifies matching tasks before modifying one.

You can also test it directly:

```powershell
cd backend
uv run python -m scripts.test_task_agent list
uv run python -m scripts.test_task_agent create --title "Buy groceries" --priority High
```

Use the page ID printed by `list` for later operations:

```powershell
uv run python -m scripts.test_task_agent complete --task-id PAGE_ID
uv run python -m scripts.test_task_agent note --task-id PAGE_ID --note "Buy oat milk too"
uv run python -m scripts.test_task_agent archive --task-id PAGE_ID
```

## Measurement

Pipecat's worker is started with both metrics and usage metrics enabled. `MetricsLogObserver` logs LLM/TTS TTFB, processing time, LLM tokens, and TTS characters; `UserBotLatencyObserver` logs speech-end to first bot audio plus the chronological service breakdown. The browser receives the same RTVI metrics and can be extended to persist a session cost report once real provider pricing is chosen. `backend/app/metrics/latency.py` is a provider-neutral timing ledger for any additional browser-arrival instrumentation.

## Scope deliberately excluded

Authentication, durable reminder delivery, rescheduling, and batch schedule optimization are still future work.
