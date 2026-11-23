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
          {state.strategy === "hybrid" && <span className="badge">SWEEP-FIRST</span>}
          {state.strategy === "sweep" && <span className="badge">TEMPLATE SWEEP</span>}
          {state.strategy === "llm" && <span className="badge">LLM RED</span>}
          {state.budgetExceeded && <span className="bad">Token budget reached</span>}
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
            {e.type === "sweep_start" && <>⚡ <b>Template sweep</b> — deterministic payloads, 0 tokens</>}
            {e.type === "sweep_done" && (
              <>⚡ Sweep finished: <b>{e.findings}</b> findings from {e.requests} requests</>
            )}
            {e.type === "breach" && (
              <>
                💥 {e.source === "sweep" && <span className="badge">template</span>}{" "}
                <b>BREACH</b> {e.vuln_class} on <code>{e.route}</code> → <code>{e.flag}</code>
              </>
            )}
            {e.type === "red_error" && <>⚠ {e.error}</>}
            {e.type === "red_action" && (
              <>
                <code>{e.source === "setup" ? "auto-login" : e.tool}</code>{" "}
                {e.source === "sweep" && <span className="badge">template</span>}{" "}
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

const CLASS_LABEL = {
  sqli: "SQL injection",
  idor: "IDOR — another user's record",
  admin_bypass: "Admin bypass",
  path_traversal: "Path traversal",
};

function packetText(e) {
  let qs = "";
  if (e.params) {
    const s = new URLSearchParams(e.params).toString();
    if (s) qs = "?" + s;
  }
  return e.method + " " + e.path + qs + (e.json ? " " + JSON.stringify(e.json) : "");
}

export function VulnPopups({ items, onDismiss }) {
  return (
    <div className="popups" aria-live="polite">
      {items.map((e) => <VulnPopup key={e.id} e={e} onDismiss={onDismiss} />)}
    </div>
  );
}

function VulnPopup({ e, onDismiss }) {
  const defended = e.state === "defended";
  useEffect(() => {
    const t = setTimeout(() => onDismiss(e.id), defended ? 4000 : 25000);
    return () => clearTimeout(t);
  }, [defended, e.id, onDismiss]);
  return (
    <div className={"vulnpop " + e.state}>
      <div className="vp-head">
        <span>{defended ? "🛡️ DEFENDED" : "💥 VULNERABILITY"}</span>
        {e.source === "sweep"
          ? <span className="badge">template</span>
          : <span className="badge model">model</span>}
        <button className="vp-x" title="dismiss" onClick={() => onDismiss(e.id)}>×</button>
      </div>
      <div className="vp-class">{CLASS_LABEL[e.vuln_class] || e.vuln_class}</div>
      <div className="vp-route">on <code>{e.route}</code></div>
      <div className="vp-packet"><code>{packetText(e)}</code></div>
      <div className="vp-flag">canary <code>{e.flag}</code></div>
      {defended && (
        <div className="vp-meta">
          Patch verified in {e.ttp_seconds}s{e.cached ? " · cached fix, 0 tokens" : ""}
        </div>
      )}
    </div>
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
            {e.type === "blue_cache" && (
              e.hit
                ? <>⚡ Cached fix verified — 0 tokens</>
                : <>↻ Cached fix stale ({e.reason}) — asking the model</>
            )}
            {e.type === "patched" && (
              <>
                🛡️ <b>PATCHED</b> {e.cached && <span className="badge">cached</span>}{" "}
                <code>{e.route}</code> in {e.ttp_seconds}s
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
          <div><b>{s.llm_calls || 0}</b><span>LLM round-trips</span></div>
          <div><b>{s.sweep_findings || 0}</b><span>found by template sweep</span></div>
          <div><b>{s.cache_hits || 0}</b><span>patches from cache</span></div>
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
