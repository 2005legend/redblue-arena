import { useEffect, useState } from "react";

export function Scoreboard({ state }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 500);
    return () => clearInterval(t);
  }, []);
  const running = state.startedAt && state.status === "running";
  const secs = state.startedAt ? Math.floor(((running ? now : state.endedAt || now) - state.startedAt) / 1000) : 0;
  const mm = String(Math.floor(secs / 60)).padStart(2, "0");
  const ss = String(secs % 60).padStart(2, "0");
  const h = state.health;
  return (
    <header className="topbar">
      <div className="score red"><span>RED</span><b>{state.score.red}</b></div>
      <div className="center">
        <div className="title">VIBE ARENA</div>
        <div className="meta">
          <span>⏱ {mm}:{ss}</span>
          <span className={h && h.failed ? "bad" : "ok"}>
            ❤ App health {h ? h.passed + "/" + (h.passed + h.failed) + " tests" : "–"}
          </span>
          {state.sample && <span className="badge">SAMPLE REPLAY</span>}
        </div>
      </div>
      <div className="score blue"><b>{state.score.blue}</b><span>BLUE</span></div>
    </header>
  );
}

const ICON = { healthy: "🟢 Healthy", breached: "🔴 Breached!", patched: "🛡️ Patched" };

export function EndpointGrid({ endpoints }) {
  return (
    <section className="grid">
      {Object.entries(endpoints).map(([route, st]) => (
        <div key={route} className={"tile " + st}>
          <code>{route}</code>
          <span>{ICON[st]}</span>
        </div>
      ))}
    </section>
  );
}

export function RedFeed({ items }) {
  return (
    <section className="feed red">
      <h2>🟥 RED — attacker</h2>
      <div className="scroll">
        {items.map((e, i) => (
          <div key={i} className={"row " + e.type}>
            {e.type === "breach" && (
              <>💥 <b>BREACH</b> {e.vuln_class} on <code>{e.route}</code> → <code>{e.flag}</code></>
            )}
            {e.type === "red_error" && <>⚠ {e.error}</>}
            {e.type === "red_action" && (
              <>
                <code>{e.tool}</code>{" "}
                {e.args && e.args.path && (
                  <code>{e.args.method} {e.args.path}{e.args.params ? " " + JSON.stringify(e.args.params) : ""}</code>
                )}
                {e.status != null && <span className="st"> → {e.status}</span>}
              </>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

export function Diff({ text }) {
  return (
    <pre className="diff">
      {text.split("\n").map((l, i) => {
        let c = "";
        if (l.startsWith("+++") || l.startsWith("---")) c = "hdr";
        else if (l.startsWith("+")) c = "add";
        else if (l.startsWith("-")) c = "del";
        else if (l.startsWith("@@")) c = "hunk";
        return <div key={i} className={c}>{l || " "}</div>;
      })}
    </pre>
  );
}

export function BlueFeed({ items }) {
  return (
    <section className="feed blue">
      <h2>🟦 BLUE — defender</h2>
      <div className="scroll">
        {items.map((e, i) => (
          <div key={i} className={"row " + e.type}>
            {e.type === "blue_thinking" && <>🧠 {e.text}</>}
            {e.type === "blue_attempt" && <>{e.ok ? "✅" : "❌"} attempt {e.n}: {e.reason}</>}
            {e.type === "patched" && (
              <>
                🛡️ <b>PATCHED</b> <code>{e.route}</code> in {e.ttp_seconds}s
                <Diff text={e.patch} />
              </>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

export function EndScreen({ state, apiBase, matchId, onClose }) {
  const s = state.summary;
  if (!s) return null;
  const dl = (f) => apiBase + "/api/export/" + matchId + "/" + f;
  const avg = s.ttp && s.ttp.length ? (s.ttp.reduce((a, b) => a + b, 0) / s.ttp.length).toFixed(1) : "–";
  const h = state.health;
  return (
    <div className="overlay">
      <div className="card">
        <h1>Match complete</h1>
        <div className="stats">
          <div><b>{s.closed}/{s.total}</b><span>vulnerabilities closed</span></div>
          <div><b>{h ? h.passed + "/" + (h.passed + h.failed) : "–"}</b><span>functional tests passing</span></div>
          <div><b>{avg}s</b><span>mean time to patch</span></div>
          <div><b>{s.tokens || 0}</b><span>LLM tokens used</span></div>
        </div>
        <div className="downloads">
          <a href={dl("hardened.patch")}>⬇ hardened.patch</a>
          <a href={dl("security_tests.zip")}>⬇ security tests</a>
          <a href={dl("report.md")}>⬇ report.md</a>
        </div>
        <button onClick={onClose}>Close</button>
      </div>
    </div>
  );
}
