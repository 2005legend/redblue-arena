import { useCallback, useEffect, useReducer, useRef } from "react";

const norm = (r) => r.replace(/\{[^}]+\}/g, "{id}");
const init = {
  status: "idle", sample: false, score: { red: 0, blue: 0 }, endpoints: {},
  red: [], blue: [], health: null, summary: null, startedAt: null,
};

function reduce(s, e) {
  if (e.type === "reset") return { ...init, status: "connecting" };
  switch (e.type) {
    case "match_start": {
      const endpoints = {};
      e.routes.forEach((r) => (endpoints[norm(r)] = "healthy"));
      return { ...s, status: "running", sample: !!e.sample, endpoints, startedAt: Date.now() };
    }
    case "red_action":
    case "red_error":
      return { ...s, red: [...s.red, e] };
    case "breach":
      return { ...s, red: [...s.red, e], endpoints: { ...s.endpoints, [norm(e.route)]: "breached" } };
    case "blue_thinking":
    case "blue_attempt":
      return { ...s, blue: [...s.blue, e] };
    case "patched":
      return { ...s, blue: [...s.blue, e], endpoints: { ...s.endpoints, [norm(e.route)]: "patched" } };
    case "score":
      return { ...s, score: { red: e.red, blue: e.blue } };
    case "health":
      return { ...s, health: { passed: e.passed, failed: e.failed } };
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
  return { state, connect };
}
