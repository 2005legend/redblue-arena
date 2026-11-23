import { useCallback, useEffect, useReducer, useRef } from "react";

const norm = (r) => r.replace(/\{[^}]+\}/g, "{id}");
const init = {
  status: "idle", sample: false, strategy: null, score: { red: 0, blue: 0 }, endpoints: {},
  red: [], blue: [], health: null, summary: null, startedAt: null, budgetExceeded: null,
  popups: [],
};

function popupFromBreach(e) {
  return {
    id: e.seq, state: "breach", route: e.route, vuln_class: e.vuln_class, flag: e.flag,
    method: e.method || "GET", path: e.path || e.route, params: e.params, json: e.json,
    source: e.source || "llm",
  };
}

function reduce(s, e) {
  if (e.type === "reset") return { ...init, status: "connecting" };
  switch (e.type) {
    case "match_start": {
      const endpoints = {};
      e.routes.forEach((r) => (endpoints[norm(r)] = "healthy"));
      return {
        ...s, status: "running", sample: !!e.sample, strategy: e.strategy || null,
        endpoints, startedAt: Date.now(), popups: [],
      };
    }
    case "sweep_start":
    case "sweep_done":
    case "red_action":
    case "red_error":
      return { ...s, red: [...s.red, e] };
    case "breach":
      return {
        ...s, red: [...s.red, e], popups: [...s.popups, popupFromBreach(e)].slice(-6),
        endpoints: { ...s.endpoints, [norm(e.route)]: "breached" },
      };
    case "patched":
      return {
        ...s, blue: [...s.blue, e], endpoints: { ...s.endpoints, [norm(e.route)]: "patched" },
        popups: s.popups.map((p) => (
          p.state === "breach" && p.route === e.route
            ? { ...p, state: "defended", ttp_seconds: e.ttp_seconds, cached: e.cached }
            : p)),
      };
    case "popup_dismiss":
      return { ...s, popups: s.popups.filter((p) => p.id !== e.id) };
    case "blue_thinking":
    case "blue_attempt":
    case "blue_cache":
      return { ...s, blue: [...s.blue, e] };
    case "score":
      return { ...s, score: { red: e.red, blue: e.blue } };
    case "health":
      return { ...s, health: { passed: e.passed, failed: e.failed } };
    case "budget_exceeded":
      return { ...s, budgetExceeded: e.error };
    case "match_end":
      return { ...s, status: "done", summary: e.summary, endedAt: Date.now() };
    case "idle":
      return { ...s, status: "idle" };
    default:
      return s;
  }
}

export function useArena() {
  const [state, dispatch] = useReducer(reduce, init);
  const sock = useRef(null);
  const connect = useCallback((url) => {
    sock.current?.close();
    dispatch({ type: "reset" });
    const ws = new WebSocket(url);
    ws.onmessage = (m) => dispatch(JSON.parse(m.data));
    ws.onerror = () => dispatch({ type: "idle" });
    sock.current = ws;
  }, []);
  useEffect(() => () => sock.current?.close(), []);
  const dismissPopup = useCallback((id) => dispatch({ type: "popup_dismiss", id }), []);
  return { state, connect, dismissPopup };
}
