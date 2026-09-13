import type { VoiceStatus } from "../voiceClient";

export function VoiceButton({
  status,
  onClick,
}: {
  status: VoiceStatus;
  onClick: () => void;
}) {
  const connected = !["disconnected", "error"].includes(status);
  return (
    <button className="voice-button" onClick={onClick} disabled={status === "connecting"}>
      <span aria-hidden="true">{connected ? "■" : "●"}</span>
      {connected ? "end session" : "start session"}
    </button>
  );
}
