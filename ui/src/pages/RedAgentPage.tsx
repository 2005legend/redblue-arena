import React, { useState, useEffect } from 'react';
import {
  Terminal,
  Play,
  CheckCircle2,
  AlertTriangle,
  Key,
  Search,
  Activity,
  ShieldAlert
} from 'lucide-react';
import {
  getBattles,
  getBattleReport,
  startMatch,
  Battle,
  BattleReport
} from '../services/api';

interface RedAgentPageProps {
  onOpenConfig: () => void;
}

export const RedAgentPage: React.FC<RedAgentPageProps> = ({ onOpenConfig }) => {
  const [battles, setBattles] = useState<Battle[]>([]);
  const [selectedBattleId, setSelectedBattleId] = useState<string>('');
  const [activeBattle, setActiveBattle] = useState<Battle | null>(null);
  const [report, setReport] = useState<BattleReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    loadBattles();
    const interval = setInterval(loadBattles, 4000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBattleId]);

  const loadBattles = async () => {
    try {
      const data = await getBattles();
      setBattles(data);
      const wanted = selectedBattleId || data[0]?.id;
      const found = data.find((b) => b.id === wanted) || data[0];
      if (found) {
        setActiveBattle(found);
        if (!selectedBattleId) setSelectedBattleId(found.id);
        try {
          setReport(await getBattleReport(found.id));
        } catch {
          setReport(null);
        }
      }
      setError(null);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleStart = async () => {
    setStarting(true);
    try {
      const matchId = await startMatch();
      setSelectedBattleId(matchId);
      await loadBattles();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setStarting(false);
    }
  };

  const findings = report?.findings ?? [];
  const running = activeBattle?.status === 'running';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-xl bg-[#090d18] border border-red-900/50 glow-red">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-red-950/80 border border-red-500/50 flex items-center justify-center glow-red">
            <Terminal className="w-6 h-6 text-red-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-black text-white tracking-wide">RED AGENT CONTROL CENTER</h1>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                running ? 'bg-red-950 text-red-400 border border-red-700 animate-pulse' :
                  activeBattle?.status === 'completed' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                    'bg-slate-900 text-slate-400 border border-slate-700'
              }`}>
                STATUS: {activeBattle?.status || 'idle'}
              </span>
            </div>
            <p className="text-xs text-red-300 font-mono mt-0.5">
              Template sweep first, then model-driven probing on leftover surface
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={selectedBattleId}
            onChange={(e) => setSelectedBattleId(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-black border border-slate-700 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-400"
          >
            {battles.map((b) => (
              <option key={b.id} value={b.id}>{b.id}</option>
            ))}
          </select>
          <button
            onClick={handleStart}
            disabled={starting || running}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-bold glow-red transition transform active:scale-95 disabled:opacity-40"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{starting ? 'Launching...' : running ? 'Match Running' : 'Start Live Match'}</span>
          </button>
          <button
            onClick={onOpenConfig}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-lg text-xs font-medium border border-cyan-900/60 transition"
          >
            Config
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-950/40 border border-red-800 text-xs font-mono text-red-300 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4" /> {error}
        </div>
      )}

      {/* Target & Objective Banner */}
      <div className="p-4 rounded-xl bg-[#090d18] border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-red-400 shrink-0" />
          <span className="text-slate-400">Current Objective:</span>
          <span className="text-white font-bold">
            {running
              ? 'Live match in progress - follow the feed on the Live Arena page'
              : activeBattle?.outcome || 'Awaiting a recorded or live match'}
          </span>
        </div>
        <div className="text-slate-400">
          Battle: <span className="text-cyan-400 font-bold">{activeBattle?.id || 'none'}</span>
        </div>
      </div>

      {/* 4 Telemetry Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Findings Confirmed", val: activeBattle?.red_discoveries ?? 0, icon: Search, color: "text-cyan-400" },
          { label: "Vulnerability Classes", val: activeBattle?.selected_vulnerabilities?.length ?? 0, icon: AlertTriangle, color: "text-yellow-400" },
          { label: "Canary Flags Captured", val: activeBattle?.red_flags_captured ?? 0, icon: Key, color: "text-red-400" },
          { label: "Rejected Patch Attempts", val: activeBattle?.blue_patches_rejected ?? 0, icon: CheckCircle2, color: "text-purple-400" },
        ].map((m, idx) => {
          const Icon = m.icon;
          return (
            <div key={idx} className="p-4 rounded-xl bg-[#090d18] border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-medium text-slate-400">{m.label}</span>
                <Icon className={`w-4 h-4 ${m.color}`} />
              </div>
              <div className="text-2xl font-black font-mono text-white">{m.val}</div>
            </div>
          );
        })}
      </div>

      {/* Workflow Stages */}
      <div className="p-6 rounded-xl bg-[#090d18] border border-slate-800 space-y-4">
        <h3 className="text-xs font-mono font-bold text-red-400 uppercase tracking-wider">
          Red Agent Execution Pipeline
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
          {[
            { step: "1. Schema Ingestion", desc: "Read /openapi.json and index every route and parameter" },
            { step: "2. Template Sweep", desc: "Bounded, scripted checks for the four seeded bug classes" },
            { step: "3. Model Fallback", desc: "Only when the sweep leaves findings unresolved" },
            { step: "4. Flag Capture", desc: "Each leaked canary is recorded with the exact packet" },
          ].map((s, i) => (
            <div key={i} className="p-3 rounded-lg bg-black/40 border border-slate-800">
              <div className="flex justify-between items-center mb-1">
                <span className="font-bold text-white">{s.step}</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-red-950 text-red-400 border border-red-900">
                  STAGE {i + 1}
                </span>
              </div>
              <p className="text-[11px] text-slate-400">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Captured Canary Flags Vault */}
      <div className="p-6 rounded-xl bg-[#090d18] border border-red-900/50 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono font-bold text-red-400 uppercase tracking-wider flex items-center gap-2">
            <Key className="w-4 h-4" /> Captured Canary Tokens
          </h3>
          <span className="text-xs font-mono text-slate-400">
            {activeBattle ? `Battle ${activeBattle.id}` : 'no battle selected'}
          </span>
        </div>
        {findings.length === 0 ? (
          <div className="p-4 rounded-lg bg-black/40 border border-slate-800 text-xs font-mono text-slate-500">
            No findings recorded for this battle.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
            {findings.map((f, i) => (
              <div key={i} className="p-3 rounded-lg bg-black/50 border border-red-950 flex flex-col justify-between">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold text-slate-200">{f.vuln_type}</span>
                  <span className="text-[10px] text-slate-400">{f.endpoint}</span>
                </div>
                <div className="p-2 rounded bg-red-950/40 text-red-300 font-bold tracking-wider select-all border border-red-900/50 text-[11px]">
                  {f.canary_token}
                </div>
                <div className="text-[10px] text-slate-500 mt-1.5">Referee: {f.patch_verification}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
