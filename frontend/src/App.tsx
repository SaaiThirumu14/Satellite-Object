import { FormEvent, useEffect, useState } from "react";

type Alert = {
  object1_id: string;
  object2_id: string;
  tca: string;
  time_to_tca_seconds: number;
  minimum_separation: number;
  risk_level: string;
  status: string;
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const sample = `{
  "threshold": 10,
  "horizon_seconds": 3600,
  "telemetry": [
    {"object_id":"SAT-1","object_type":"satellite","timestamp":"2026-01-01T00:00:00Z","position":[0,0,0],"velocity":[1,0,0]},
    {"object_id":"DEB-1","object_type":"debris","timestamp":"2026-01-01T00:00:00Z","position":[5,0,0],"velocity":[-1,0,0]}
  ]
}`;

export default function App() {
  const [payload, setPayload] = useState(sample);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [message, setMessage] = useState("Ready for telemetry");
  const [loading, setLoading] = useState(false);

  async function loadAlerts() {
    try {
      const response = await fetch(`${API_URL}/v1/alerts`);
      if (!response.ok) throw new Error("Database is unavailable");
      setAlerts(await response.json());
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to load alerts");
    }
  }

  useEffect(() => { void loadAlerts(); }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("Processing telemetry...");
    try {
      const response = await fetch(`${API_URL}/v1/conjunctions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Detection failed");
      setAlerts(body);
      setMessage(`${body.length} conjunction alert${body.length === 1 ? "" : "s"} detected`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Detection failed");
    } finally {
      setLoading(false);
    }
  }

  return <main className="shell">
    <header>
      <div><p className="eyebrow">ORBITAL SAFETY SYSTEM</p><h1>Conjunction control room</h1><p className="muted">Real-time closest-approach analysis for LEO telemetry</p></div>
      <div className="status"><span className="pulse" /> ENGINE ONLINE</div>
    </header>
    <section className="stats">
      <div><span>ACTIVE ALERTS</span><strong>{alerts.length}</strong></div>
      <div><span>PROCESSING MODEL</span><strong>RELATIVE VELOCITY</strong></div>
      <div><span>DATA STORE</span><strong>POSTGIS</strong></div>
    </section>
    <section className="workspace">
      <form className="panel input-panel" onSubmit={submit}>
        <div className="panel-heading"><div><p className="eyebrow">TELEMETRY INGEST</p><h2>Run collision scan</h2></div><span className="tag">JSON</span></div>
        <textarea value={payload} onChange={(event) => setPayload(event.target.value)} spellCheck={false} />
        <button disabled={loading}>{loading ? "ANALYZING..." : "ANALYZE TRAJECTORIES"} <span>→</span></button>
        <p className="message">{message}</p>
      </form>
      <section className="panel alerts-panel">
        <div className="panel-heading"><div><p className="eyebrow">PRIORITIZED QUEUE</p><h2>Conjunction alerts</h2></div><button className="refresh" onClick={() => void loadAlerts()}>↻ Refresh</button></div>
        {alerts.length === 0 ? <div className="empty">No alerts to display. Submit telemetry to begin analysis.</div> :
          <div className="alert-list">{alerts.map((alert, index) => <article className="alert" key={`${alert.object1_id}-${alert.object2_id}-${index}`}>
            <div className={`risk ${alert.risk_level}`}>{alert.risk_level}</div>
            <div className="alert-main"><strong>{alert.object1_id} <span>×</span> {alert.object2_id}</strong><span className="muted">TCA {new Date(alert.tca).toLocaleString()}</span></div>
            <div className="metric"><span>SEPARATION</span><strong>{alert.minimum_separation.toFixed(2)} km</strong></div>
            <div className="metric"><span>TIME TO TCA</span><strong>{alert.time_to_tca_seconds.toFixed(1)} s</strong></div>
          </article>)}</div>}
      </section>
    </section>
  </main>;
}
