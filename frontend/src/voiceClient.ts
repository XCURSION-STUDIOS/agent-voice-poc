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

type Callbacks = {
  onStatus: (status: VoiceStatus) => void;
  onTranscript: (role: "user" | "assistant", text: string) => void;
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
