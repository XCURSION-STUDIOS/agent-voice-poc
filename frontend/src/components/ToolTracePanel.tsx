import type { ToolTrace } from "../voiceClient";

function formatValue(value: unknown) {
  if (value === undefined) return "waiting for payload";
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function statusLabel(status: ToolTrace["status"]) {
  return status === "running" ? "running" : status;
}

export function ToolTracePanel({ traces }: { traces: ToolTrace[] }) {
  return (
    <section className="panel tools-panel" aria-label="Tool execution trace">
      <div className="section-heading">
        <span>live tool trace</span>
        <span>{traces.length} calls</span>
      </div>
      {traces.length === 0 ? (
        <div className="tool-empty">
          <span className="tool-empty-orbit" aria-hidden="true" />
          <p>tool activity will appear here.</p>
          <small>Ask Jarvis to check your calendar or update a task.</small>
        </div>
      ) : (
        <div className="tool-timeline">
          {traces.map((trace, index) => (
            <article className={`tool-run ${trace.status}`} key={trace.id}>
              <div className="tool-node" aria-hidden="true"><span /></div>
              {index < traces.length - 1 && <div className="tool-connector" aria-hidden="true" />}
              <div className="tool-card">
                <div className="tool-card-header">
                  <div><span className="tool-kicker">specialist tool</span><h3>{trace.name}</h3></div>
                  <span className="tool-status">{statusLabel(trace.status)}</span>
                </div>
                <div className="tool-step"><span>→ args</span><pre>{formatValue(trace.arguments)}</pre></div>
                <div className="tool-step"><span>← result</span><pre>{formatValue(trace.result)}</pre></div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
