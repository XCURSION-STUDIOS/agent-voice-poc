import { PipecatClient } from "@pipecat-ai/client-js";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";

export type VoiceStatus =
  | "disconnected"
  | "connecting"
  | "listening"
  | "thinking"
  | "speaking"
  | "interrupted"
  | "error";

export type ToolTrace = {
  id: string;
  name: string;
  arguments?: Record<string, unknown>;
  result?: unknown;
  status: "started" | "running" | "completed" | "cancelled";
  startedAt: number;
  finishedAt?: number;
};

type Callbacks = {
  onStatus: (status: VoiceStatus) => void;
  onTranscript: (role: "user" | "assistant", text: string) => void;
  onToolTrace: (trace: ToolTrace) => void;
};

/** Browser-only bridge. It knows WebRTC, never provider credentials. */
export class VoiceClient {
  private client: PipecatClient;
  private audio = new Audio();

  constructor(private callbacks: Callbacks) {
    this.audio.autoplay = true;
    this.client = new PipecatClient({
      transport: new SmallWebRTCTransport(),
      enableCam: false,
      enableMic: true,
      callbacks: {
        onTransportStateChanged: (state: string) => {
          if (state === "connecting") callbacks.onStatus("connecting");
        },
        onBotReady: () => callbacks.onStatus("listening"),
        onDisconnected: () => callbacks.onStatus("disconnected"),
        onError: () => callbacks.onStatus("error"),
        onUserStartedSpeaking: () => callbacks.onStatus("listening"),
        onUserStoppedSpeaking: () => callbacks.onStatus("thinking"),
        onBotStartedSpeaking: () => callbacks.onStatus("speaking"),
        onBotStoppedSpeaking: () => callbacks.onStatus("listening"),
        onTrackStarted: (track, participant) => {
          // The local microphone is also a WebRTC audio track. Playing it back
          // creates the echo the user hears; only render the bot's remote track.
          if (participant?.local || track.kind !== "audio") return;
          this.audio.srcObject = new MediaStream([track]);
          void this.audio.play();
        },
        onTrackStopped: (track, participant) => {
          if (participant?.local || track.kind !== "audio") return;
          this.audio.pause();
          this.audio.srcObject = null;
        },
        onUserTranscript: (data: { text?: string; final?: boolean }) => {
          if (data.final && data.text) callbacks.onTranscript("user", data.text);
        },
        onBotOutput: (data: { text?: string; spoken?: boolean }) => {
          if (data.spoken && data.text) callbacks.onTranscript("assistant", data.text);
        },
        onLLMFunctionCallStarted: (data: { function_name?: string }) => {
          if (!data.function_name) return;
          callbacks.onToolTrace({
            id: `pending-${Date.now()}`,
            name: data.function_name,
            status: "started",
            startedAt: Date.now(),
          });
        },
        onLLMFunctionCallInProgress: (data: {
          function_name?: string;
          tool_call_id: string;
          arguments?: Record<string, unknown>;
        }) => {
          if (!data.function_name) return;
          callbacks.onToolTrace({
            id: data.tool_call_id,
            name: data.function_name,
            arguments: data.arguments,
            status: "running",
            startedAt: Date.now(),
          });
        },
        // Older RTVI servers emit the legacy function-call event instead of
        // the newer started/in-progress pair. Keep it as a compatibility path
        // so tool activity remains visible across Pipecat versions.
        onLLMFunctionCall: (data: {
          function_name?: string;
          tool_call_id: string;
          args: Record<string, unknown>;
        }) => {
          if (!data.function_name) return;
          callbacks.onToolTrace({
            id: data.tool_call_id,
            name: data.function_name,
            arguments: data.args,
            status: "running",
            startedAt: Date.now(),
          });
        },
        onLLMFunctionCallStopped: (data: {
          function_name?: string;
          tool_call_id: string;
          cancelled: boolean;
          result?: unknown;
        }) => {
          if (!data.function_name) return;
          callbacks.onToolTrace({
            id: data.tool_call_id,
            name: data.function_name,
            result: data.result,
            status: data.cancelled ? "cancelled" : "completed",
            startedAt: Date.now(),
            finishedAt: Date.now(),
          });
        },
      },
    });
  }

  async connect() {
    this.callbacks.onStatus("connecting");
    // `enableMic: true` selects the default mic, but initDevices() is what
    // requests browser permission and turns the local media track on.
    await this.client.initDevices();
    this.client.enableMic(true);
    // SmallWebRTC's official direct signaling endpoint for the self-hosted runner.
    await this.client.connect({ webrtcUrl: "/api/offer" });
  }

  async disconnect() {
    await this.client.disconnect();
    this.audio.pause();
    this.audio.srcObject = null;
  }
}
