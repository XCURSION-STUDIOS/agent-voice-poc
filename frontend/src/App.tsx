import { useEffect, useRef, useState } from "react";
import { AssistantStatus } from "./components/AssistantStatus";
import { VoiceButton } from "./components/VoiceButton";
import { VoiceClient, type VoiceStatus } from "./voiceClient";

type Message = { role: "user" | "assistant"; text: string };
type Tab = "voice" | "log" | "local" | "help";

export default function App() {
  const [status, setStatus] = useState<VoiceStatus>("disconnected");
  const [messages, setMessages] = useState<Message[]>([]);
  const [tab, setTab] = useState<Tab>("voice");
  const client = useRef<VoiceClient | null>(null);

  useEffect(() => {
    client.current = new VoiceClient({
      onStatus: setStatus,
      onTranscript: (role, text) => {
        setMessages((current) => [...current, { role, text }]);
        if (role === "user") setStatus("thinking");
      },
    });
    return () => void client.current?.disconnect();
  }, []);

  const toggleConversation = async () => {
    try {
      if (["disconnected", "error"].includes(status)) await client.current?.connect();
      else await client.current?.disconnect();
    } catch (error) {
      console.error(error);
      setStatus("error");
    }
  };

  return (
    <main className="app-shell">
      <aside className="rail" aria-label="Voice assistant navigation">
        <a className="mark" href="#voice" aria-label="Jarvis home">≫</a>
        <nav>
          <button className={`rail-item ${tab === "voice" ? "active" : ""}`} onClick={() => setTab("voice")} aria-pressed={tab === "voice"}><span>◉</span><small>voice</small></button>
          <button className={`rail-item ${tab === "log" ? "active" : ""}`} onClick={() => setTab("log")} aria-pressed={tab === "log"}><span>⌁</span><small>log</small></button>
        </nav>
        <div className="rail-bottom">
          <button className={`rail-item ${tab === "local" ? "active" : ""}`} onClick={() => setTab("local")} aria-pressed={tab === "local"}><span>⚙</span><small>local</small></button>
          <button className={`rail-item ${tab === "help" ? "active" : ""}`} onClick={() => setTab("help")} aria-pressed={tab === "help"}><span>?</span><small>help</small></button>
        </div>
      </aside>

      <header className="topbar">
        <p><span>+</span> local voice assistant</p>
        <span className="top-status">{status === "disconnected" ? "offline" : "online"}</span>
      </header>

      {tab === "voice" && <section className="voice-stage" id="voice">
        <div className="terminal-title"><span>jarvis://voice</span><span>deepgram → openai → configurable TTS</span></div>
        <div className={`signal ${status}`} aria-hidden="true"><i /><i /><i /><i /><i /></div>
        <p className="prompt">{status === "disconnected" ? "ready when you are." : "just talk. interrupt anytime."}</p>
        <AssistantStatus status={status} />
        <div className="command-row">
          <span className="command-mark" aria-hidden="true">›</span>
          <VoiceButton status={status} onClick={() => void toggleConversation()} />
          <span className="command-hint">mic is live after connect</span>
        </div>
        {messages.length > 0 && (
          <section className="log-preview" aria-label="Recent conversation">
            <div className="section-heading"><span>recent log</span><button type="button" onClick={() => setTab("log")}>view full log</button></div>
            <div className="transcript">
              {messages.slice(-3).map((message, index) => (
                <p key={`preview-${message.role}-${messages.length - 3 + index}`} className={message.role}>
                  <strong>{message.role === "user" ? "you" : "jarvis"}</strong><span>{message.text}</span>
                </p>
              ))}
            </div>
          </section>
        )}
      </section>
      }

      {tab === "log" && <section className="panel conversation" id="log" aria-label="Conversation transcript">
        <div className="section-heading"><span>full session log</span><span>{messages.length} entries</span></div>
        {messages.length === 0 ? <p className="empty-log">your conversation will appear here.</p> : (
          <div className="transcript full-transcript">
            {messages.map((message, index) => (
              <p key={`${message.role}-${index}`} className={message.role}>
                <strong>{message.role === "user" ? "you" : "jarvis"}</strong><span>{message.text}</span>
              </p>
            ))}
          </div>
        )}
      </section>
      }

      {tab === "local" && <section className="panel info-panel">
        <div className="section-heading"><span>local pipeline</span><span>connected services</span></div>
        <dl className="service-list">
          <div><dt>listen</dt><dd>Deepgram Nova · streaming STT</dd></div>
          <div><dt>think</dt><dd>OpenAI GPT-5.6 Luna · streaming LLM</dd></div>
          <div><dt>speak</dt><dd>Selected in .env · OpenAI or Deepgram</dd></div>
          <div><dt>transport</dt><dd>Small WebRTC · local only</dd></div>
        </dl>
      </section>}

      {tab === "help" && <section className="panel info-panel">
        <div className="section-heading"><span>quick help</span><span>voice controls</span></div>
        <ul className="help-list">
          <li><strong>start session</strong><span>allow microphone access, then speak naturally.</span></li>
          <li><strong>interrupt</strong><span>speak while Jarvis is answering; your new turn takes priority.</span></li>
          <li><strong>check quality</strong><span>use headphones to prevent feedback and false interruptions.</span></li>
        </ul>
      </section>}
      <footer>local only · no conversation is stored</footer>
    </main>
  );
}
