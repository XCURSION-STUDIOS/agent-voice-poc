import type { VoiceStatus } from "../voiceClient";

const labels: Record<VoiceStatus, string> = {
  disconnected: "Disconnected",
  connecting: "Connecting",
  listening: "Listening",
  thinking: "Thinking",
  speaking: "Speaking",
  interrupted: "Interrupted — listening",
  error: "Connection error",
};

export function AssistantStatus({ status }: { status: VoiceStatus }) {
  return (
    <p className={`status status-${status}`} aria-live="polite">
      <span className="status-dot" aria-hidden="true" />
      {labels[status]}
    </p>
  );
}
