import React, { useState, useEffect, useRef } from 'react';
import { 
  Swords, 
  Terminal, 
  Cpu, 
  Scale, 
  Play, 
  Pause, 
  RotateCcw, 
  Square, 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldAlert, 
  Radio, 
  Key, 
  FileCode2,
  Sliders
} from 'lucide-react';
import { 
  getBattles, 
  getBattle, 
  startBattle, 
  pauseBattle, 
  resumeBattle, 
  resetBattle, 
  connectBattleWS, 
  Battle, 
  BattleEvent 
} from '../services/api';

interface BattleArenaPageProps {
  onOpenConfig: () => void;
  activeBattleId?: string;
  setActiveBattleId?: (id: string) => void;
}

export const BattleArenaPage: React.FC<BattleArenaPageProps> = ({
  onOpenConfig,
  activeBattleId,
  setActiveBattleId
}) => {
  const [battles, setBattles] = useState<Battle[]>([]);
  const [selectedBattleId, setSelectedBattleId] = useState<string>(activeBattleId || '');
  const [battle, setBattle] = useState<Battle | null>(null);
  const [events, setEvents] = useState<BattleEvent[]>([]);
  const [isLiveWs, setIsLiveWs] = useState(false);
  const [activeEndpoint, setActiveEndpoint] = useState<string>('/api/products/search');
  const [appHealth, setAppHealth] = useState<string>('100% Operational');
  const [redStatus, setRedStatus] = useState<string>('idle');
  const [blueStatus, setBlueStatus] = useState<string>('idle');

  const wsRef = useRef<WebSocket | null>(null);
  const timelineEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    loadBattles();
    const interval = setInterval(loadBattles, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadBattles = async () => {
    try {
      const data = await getBattles();
      setBattles(data);
      if (data.length > 0 && !selectedBattleId) {
        const id = data[0].id;
        setSelectedBattleId(id);
        if (setActiveBattleId) setActiveBattleId(id);
        fetchBattleData(id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchBattleData = async (bId: string) => {
    try {
      const b = await getBattle(bId);
      setBattle(b);
      if (b.events && b.events.length > 0) {
        setEvents(b.events);
      }
      if (b.status === 'running') {
        setRedStatus('running');
        setBlueStatus('active');
      } else if (b.status === 'completed') {
        setRedStatus('completed');
        setBlueStatus('completed');
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Connect WebSocket when selectedBattleId changes
  useEffect(() => {
    if (!selectedBattleId) return;
    fetchBattleData(selectedBattleId);

    if (wsRef.current) {
      wsRef.current.close();
    }

    try {
      const ws = connectBattleWS(selectedBattleId, (ev: BattleEvent) => {
        setIsLiveWs(true);
        setEvents(prev => [...prev, ev]);

        if (ev.endpoint) {
          setActiveEndpoint(ev.endpoint);
        }

        if (ev.source === 'RED') {
          setRedStatus('attacking');
        } else if (ev.source === 'BLUE') {
          setBlueStatus('patching');
        }

        if (ev.event_type === 'BATTLE_CONCLUDED') {
          setRedStatus('completed');
          setBlueStatus('completed');
          loadBattles();
        }
      });

      ws.onopen = () => setIsLiveWs(true);
      ws.onclose = () => setIsLiveWs(false);
      wsRef.current = ws;

      return () => {
        ws.close();
      };
    } catch (e) {
      console.error('WS init error', e);
    }
  }, [selectedBattleId]);

  // Auto-scroll timeline
  useEffect(() => {
    if (timelineEndRef.current) {
      timelineEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events]);

  const handleStart = async () => {
    if (!selectedBattleId) return;
    try {
      await startBattle(selectedBattleId);
      setRedStatus('running');
      setBlueStatus('ready');
      fetchBattleData(selectedBattleId);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handlePause = async () => {
    if (!selectedBattleId) return;
    try {
      await pauseBattle(selectedBattleId);
      setRedStatus('paused');
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleResume = async () => {
    if (!selectedBattleId) return;
    try {
      await resumeBattle(selectedBattleId);
      setRedStatus('running');
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleReset = async () => {
    if (!selectedBattleId) return;
    try {
      await resetBattle(selectedBattleId);
      setEvents([]);
      setRedStatus('idle');
      setBlueStatus('idle');
      fetchBattleData(selectedBattleId);
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top SOC Bar with Battle Selector and Control Buttons */}
      <div className="p-4 rounded-xl bg-[#090d18] border border-cyan-900/60 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-red-600/30 via-cyan-500/20 to-blue-600/30 border border-cyan-500/40 flex items-center justify-center glow-cyan">
            <Swords className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-black text-white tracking-wide">LIVE CYBER-BATTLE ARENA</h1>
              <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-black/60 border border-slate-700 text-[10px] font-mono">
                <span className={`w-2 h-2 rounded-full ${isLiveWs ? 'bg-emerald-400 animate-pulse' : 'bg-yellow-400'}`}></span>
                <span className={isLiveWs ? 'text-emerald-400' : 'text-yellow-400'}>
                  {isLiveWs ? 'WS TELEMETRY CONNECTED' : 'POLLING MODE'}
                </span>
              </div>
            </div>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              Simultaneous Autonomous Offensive Probing vs. Surgical Defensive Patching
            </p>
          </div>
        </div>

        {/* Controls & Battle Selector */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedBattleId}
            onChange={(e) => {
              setSelectedBattleId(e.target.value);
              if (setActiveBattleId) setActiveBattleId(e.target.value);
            }}
            className="px-3 py-1.5 rounded-lg bg-black border border-slate-700 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-400"
          >
            {battles.map(b => (
              <option key={b.id} value={b.id}>
                {b.id} - {b.name} ({b.status})
              </option>
            ))}
          </select>

          {battle?.status !== 'running' ? (
            <button
              onClick={handleStart}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-gradient-to-r from-red-600 to-cyan-500 hover:from-red-500 hover:to-cyan-400 text-white rounded-lg text-xs font-bold glow-cyan transition transform active:scale-95"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Engage Battle</span>
            </button>
          ) : (
            <button
              onClick={handlePause}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-yellow-600 hover:bg-yellow-500 text-white rounded-lg text-xs font-bold transition"
            >
              <Pause className="w-3.5 h-3.5 fill-current" />
              <span>Pause</span>
            </button>
          )}

          <button
            onClick={handleReset}
            className="flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>

          <button
            onClick={onOpenConfig}
            className="flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-lg text-xs font-medium border border-cyan-900/60 transition"
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Config</span>
          </button>
        </div>
      </div>

      {/* 3-COLUMN MAIN ARENA GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* LEFT PANEL: RED AGENT (Col 4) */}
        <div className="lg:col-span-4 p-5 rounded-xl bg-[#090d18] border border-red-900/40 glow-red/5 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-red-950 pb-3 mb-3">
              <div className="flex items-center space-x-2">
                <Terminal className="w-5 h-5 text-red-400" />
                <span className="text-sm font-bold text-red-300 tracking-wider">RED AGENT</span>
              </div>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                redStatus === 'running' || redStatus === 'attacking'
                  ? 'bg-red-950 text-red-400 border border-red-700 animate-pulse'
                  : 'bg-slate-900 text-slate-400 border border-slate-800'
              }`}>
                {redStatus}
              </span>
            </div>

            {/* Red Stats */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono mb-4">
              <div className="p-2.5 rounded-lg bg-black/50 border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Endpoints Probed</span>
                <span className="text-lg font-bold text-white">{battle?.red_discoveries ?? 4}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-red-950/30 border border-red-900/60">
                <span className="text-red-300 block text-[10px]">Canaries Captured</span>
                <span className="text-lg font-bold text-red-400">{battle?.red_flags_captured ?? 4}</span>
              </div>
            </div>

            {/* Current Objective */}
            <div className="p-3 rounded-lg bg-black/60 border border-slate-800 text-xs font-mono space-y-1 mb-4">
              <div className="text-[10px] text-red-400 uppercase font-bold flex items-center gap-1">
                <Activity className="w-3 h-3" /> Current Offensive Objective:
              </div>
              <p className="text-slate-300 leading-snug">
                Probing targeted parameter surfaces against isolated sandbox. Validating canary token leakage.
              </p>
            </div>

            {/* Captured Canary Badges */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                Captured Canary Secret Vault:
              </span>
              {[
                { name: "SQL Injection", flag: "FLAG{CANARY_SQLI_DISCOVERED_984}" },
                { name: "IDOR", flag: "FLAG{CANARY_IDOR_ORDER_ACCESS_312}" },
                { name: "Path Traversal", flag: "FLAG{CANARY_PATH_TRAVERSAL_881}" },
                { name: "Broken Admin Auth", flag: "FLAG{CANARY_ADMIN_AUTH_BYPASS_404}" }
              ].map((c, i) => (
                <div key={i} className="p-2 rounded bg-black/40 border border-red-950 text-[10px] font-mono flex items-center justify-between">
                  <span className="text-slate-400">{c.name}</span>
                  <span className="text-red-400 font-bold">{c.flag.substring(0, 16)}...&#125;</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CENTER PANEL: TARGET APPLICATION (Col 4) */}
        <div className="lg:col-span-4 p-5 rounded-xl bg-[#090d18] border border-cyan-900/50 glow-cyan/10 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-cyan-950 pb-3 mb-3">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-5 h-5 text-cyan-400" />
                <span className="text-sm font-bold text-white tracking-wider">TARGET APPLICATION</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                HEALTH: {appHealth}
              </span>
            </div>

            {/* Active Endpoint Beacon */}
            <div className="p-3.5 rounded-lg bg-black/60 border border-cyan-900/50 space-y-2 mb-4">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">Target Endpoint:</span>
                <span className="flex items-center gap-1.5 text-cyan-400 font-bold">
                  <Radio className="w-3.5 h-3.5 animate-pulse text-cyan-400" /> ACTIVE
                </span>
              </div>
              <div className="text-xs font-mono text-cyan-300 font-bold bg-cyan-950/40 p-2 rounded border border-cyan-800/60 truncate">
                {activeEndpoint}
              </div>
            </div>

            {/* Enclave Status Matrix */}
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2 rounded bg-black/40 border border-slate-800">
                <span className="text-slate-400">Sandbox Isolation:</span>
                <span className="text-emerald-400 font-bold">Local Process Isolated</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-black/40 border border-slate-800">
                <span className="text-slate-400">Database Engine:</span>
                <span className="text-white font-bold">SQLite 3 (Synthetic)</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-black/40 border border-slate-800">
                <span className="text-slate-400">Active Handlers:</span>
                <span className="text-cyan-400 font-bold">Vulnerable / Hot-Patchable</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-black/40 border border-slate-800">
                <span className="text-slate-400">HTTP Response Code:</span>
                <span className="text-emerald-400 font-bold">200 OK / 403 Forbidden</span>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-cyan-950/30 border border-cyan-800/40 text-[11px] font-mono text-cyan-300 text-center">
            Zero external traffic allowed. Strict sandbox boundary enforced.
          </div>
        </div>

        {/* RIGHT PANEL: BLUE AGENT (Col 4) */}
        <div className="lg:col-span-4 p-5 rounded-xl bg-[#090d18] border border-blue-900/40 glow-blue/5 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-blue-950 pb-3 mb-3">
              <div className="flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-blue-400" />
                <span className="text-sm font-bold text-blue-300 tracking-wider">BLUE AGENT</span>
              </div>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                blueStatus === 'patching' || blueStatus === 'active'
                  ? 'bg-blue-950 text-blue-400 border border-blue-700 animate-pulse'
                  : 'bg-slate-900 text-slate-400 border border-slate-800'
              }`}>
                {blueStatus}
              </span>
            </div>

            {/* Blue Stats */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono mb-4">
              <div className="p-2.5 rounded-lg bg-black/50 border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Patches Generated</span>
                <span className="text-lg font-bold text-white">{battle?.blue_patches_generated ?? 4}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-900/60">
                <span className="text-emerald-300 block text-[10px]">Referee Verified</span>
                <span className="text-lg font-bold text-emerald-400">{battle?.blue_patches_approved ?? 4}</span>
              </div>
            </div>

            {/* Current Defense Objective */}
            <div className="p-3 rounded-lg bg-black/60 border border-slate-800 text-xs font-mono space-y-1 mb-4">
              <div className="text-[10px] text-blue-400 uppercase font-bold flex items-center gap-1">
                <FileCode2 className="w-3 h-3" /> Defensive Synthesis:
              </div>
              <p className="text-slate-300 leading-snug">
                Parsing breach incidents, producing minimal AST-safe python diffs, and requesting Pytest evaluation.
              </p>
            </div>

            {/* Deployed Patches Matrix */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                Active Verified Patches:
              </span>
              {[
                { name: "SQLi Parameterizer", status: "VERIFIED" },
                { name: "IDOR Authorization Guard", status: "VERIFIED" },
                { name: "Safe Path Boundary Check", status: "VERIFIED" },
                { name: "Bearer Token Authenticator", status: "VERIFIED" }
              ].map((p, i) => (
                <div key={i} className="p-2 rounded bg-black/40 border border-blue-950 text-[10px] font-mono flex items-center justify-between">
                  <span className="text-slate-300">{p.name}</span>
                  <span className="text-emerald-400 font-bold">{p.status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* BOTTOM PANEL: REAL-TIME BATTLE EVENT TIMELINE */}
      <div className="p-6 rounded-xl bg-[#090d18] border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
              Live Battle Telemetry & Referee Verdict Stream
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {events.length} Telemetry Events Recorded
          </span>
        </div>

        {/* Scrollable Event Feed */}
        <div className="space-y-2 max-h-80 overflow-y-auto pr-2 scrollbar-thin">
          {events.length === 0 ? (
            <div className="text-center py-10 text-xs font-mono text-slate-500">
              No live events in current buffer. Click "Engage Battle" to launch simulation.
            </div>
          ) : (
            events.map((ev, idx) => {
              const isRed = ev.source === 'RED';
              const isBlue = ev.source === 'BLUE';
              const isReferee = ev.source === 'REFEREE';
              const isArena = ev.source === 'ARENA';

              const sourceBadge = isRed
                ? 'bg-red-950 text-red-400 border-red-800'
                : isBlue
                ? 'bg-blue-950 text-blue-400 border-blue-800'
                : isReferee
                ? 'bg-purple-950 text-purple-400 border-purple-800'
                : 'bg-cyan-950 text-cyan-400 border-cyan-800';

              return (
                <div
                  key={idx}
                  className="flex items-start space-x-3 p-3 rounded-lg bg-black/40 border border-slate-800/80 hover:border-slate-700 transition font-mono text-xs"
                >
                  <span className="text-[10px] text-slate-500 shrink-0 pt-0.5">
                    {ev.timestamp ? ev.timestamp.split('T')[1]?.substring(0, 8) || ev.timestamp : '00:00:00'}
                  </span>

                  <span className={`text-[10px] px-2 py-0.5 rounded border font-bold uppercase shrink-0 ${sourceBadge}`}>
                    [{ev.source}]
                  </span>

                  <div className="flex-1">
                    <span className="text-slate-200">{ev.summary}</span>
                    {ev.endpoint && (
                      <span className="text-[10px] text-cyan-400 ml-2">({ev.endpoint})</span>
                    )}
                  </div>
                </div>
              );
            })
          )}
          <div ref={timelineEndRef} />
        </div>
      </div>
    </div>
  );
};
