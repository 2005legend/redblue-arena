import { useState } from "react";
import { BlueFeed, EndpointGrid, EndScreen, RedFeed, Scoreboard } from "./components.jsx";
import { useArena } from "./useArena.js";

const HOST = "127.0.0.1:8765";
const API = "http://" + HOST;

export default function App() {
  const { state, connect } = useArena();
  const [matchId, setMatchId] = useState("sample");
  const [closed, setClosed] = useState(false);

  const replay = (file, speed = 1) => {
    setClosed(false);
    setMatchId(file.includes("/") ? file.split("/")[0] : file.replace(".jsonl", ""));
    connect("ws://" + HOST + "/ws?replay=" + file + "&speed=" + speed);
  };
  const startLive = async () => {
    setClosed(false);
    const r = await fetch(API + "/api/match/start", { method: "POST" });
    if (!r.ok) return alert("Could not start: " + (await r.text()));
    const { match_id } = await r.json();
    setMatchId(match_id);
    connect("ws://" + HOST + "/ws");
  };

  return (
    <div className="app">
      <Scoreboard state={state} />
      {state.status === "idle" && (
        <div className="launch">
          <p>Point two AI agents at an app built in an afternoon. Watch it get attacked and fixed.</p>
          <button onClick={startLive}>▶ Start live match</button>
          <button className="ghost" onClick={() => replay("sample.jsonl")}>↻ Replay sample match</button>
        </div>
      )}
      <EndpointGrid endpoints={state.endpoints} />
      <main className="split">
        <RedFeed items={state.red} />
        <BlueFeed items={state.blue} />
      </main>
      {state.status === "done" && !closed && (
        <EndScreen state={state} apiBase={API} matchId={matchId} onClose={() => setClosed(true)} />
      )}
    </div>
  );
}
