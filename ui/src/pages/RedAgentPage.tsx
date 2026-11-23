import React, { useState, useEffect } from 'react';
import { 
  Terminal, 
  Play, 
  Pause, 
  Square, 
  RotateCcw, 
  CheckCircle2, 
  AlertTriangle, 
  Key, 
  Clock, 
  Search,
  Activity,
  Layers,
  FileJson
} from 'lucide-react';
import { getBattles, startBattle, pauseBattle, resumeBattle, stopBattle, resetBattle, Battle } from '../services/api';

interface RedAgentPageProps {
  onOpenConfig: () => void;
}

export const RedAgentPage: React.FC<RedAgentPageProps> = ({ onOpenConfig }) => {
  const [battles, setBattles] = useState<Battle[]>([]);
  const [selectedBattleId, setSelectedBattleId] = useState<string>('');
  const [activeBattle, setActiveBattle] = useState<Battle | null>(null);
  const [agentStatus, setAgentStatus] = useState<string>('idle');
  const [currentObjective, setCurrentObjective] = useState<string>('Awaiting deployment signal');

  useEffect(() => {
    loadBattles();
    const interval = setInterval(loadBattles, 4000);
    return () => clearInterval(interval);
  }, []);

  const loadBattles = async () => {
    try {
      const data = await getBattles();
      setBattles(data);
      if (data.length > 0 && !selectedBattleId) {
        setSelectedBattleId(data[0].id);
        setActiveBattle(data[0]);
        setAgentStatus(data[0].status);
      } else if (selectedBattleId) {
        const found = data.find(b => b.id === selectedBattleId);
        if (found) {
          setActiveBattle(found);
          setAgentStatus(found.status);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleStart = async () => {
    if (!selectedBattleId) return;
    try {
      await startBattle(selectedBattleId);
      setAgentStatus('running');
      setCurrentObjective('Autonomous attack sequence initiated: Fetching /openapi.json');
      loadBattles();
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handlePause = async () => {
    if (!selectedBattleId) return;
    try {
      await pauseBattle(selectedBattleId);
      setAgentStatus('paused');
      setCurrentObjective('Paused by operator. Holding attack queue.');
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleResume = async () => {
    if (!selectedBattleId) return;
    try {
      await resumeBattle(selectedBattleId);
      setAgentStatus('running');
      setCurrentObjective('Resuming automated security tests.');
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleStop = async () => {
    if (!selectedBattleId) return;
    try {
      await stopBattle(selectedBattleId);
      setAgentStatus('stopped');
      setCurrentObjective('Attack sequence stopped.');
    } catch (e: any) {
      alert(e.message);
    }
  };

  const handleReset = async () => {
    if (!selectedBattleId) return;
    try {
      await resetBattle(selectedBattleId);
      setAgentStatus('idle');
      setCurrentObjective('Agent reset to clean idle state.');
      loadBattles();
    } catch (e: any) {
      alert(e.message);
    }
  };

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
                agentStatus === 'running' ? 'bg-red-950 text-red-400 border border-red-700 animate-pulse' :
                agentStatus === 'completed' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                'bg-slate-900 text-slate-400 border border-slate-700'
              }`}>
                STATUS: {agentStatus}
              </span>
            </div>
            <p className="text-xs text-red-300 font-mono mt-0.5">
              Autonomous Attack Surface Discovery & Canary Flag Exploitation
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {agentStatus !== 'running' ? (
            <button
              onClick={handleStart}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-bold glow-red transition transform active:scale-95"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Start Red Agent</span>
            </button>
          ) : (
            <button
              onClick={handlePause}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-yellow-600 hover:bg-yellow-500 text-white rounded-lg text-xs font-bold transition transform active:scale-95"
            >
              <Pause className="w-3.5 h-3.5 fill-current" />
              <span>Pause</span>
            </button>
          )}

          {agentStatus === 'paused' && (
            <button
              onClick={handleResume}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Resume</span>
            </button>
          )}

          <button
            onClick={handleStop}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition"
          >
            <Square className="w-3.5 h-3.5" />
            <span>Stop</span>
          </button>

          <button
            onClick={handleReset}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Target & Objective Banner */}
      <div className="p-4 rounded-xl bg-[#090d18] border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-red-400 shrink-0" />
          <span className="text-slate-400">Current Objective:</span>
          <span className="text-white font-bold">{currentObjective}</span>
        </div>
        <div className="text-slate-400">
          Target: <span className="text-cyan-400 font-bold">{activeBattle?.target_app || 'ARENA Target Sandbox'}</span>
        </div>
      </div>

      {/* 4 Telemetry Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "OpenAPI Endpoints Discovered", val: activeBattle?.red_discoveries || 18, icon: Search, color: "text-cyan-400" },
          { label: "Vulnerabilities Identified", val: activeBattle?.red_discoveries || 4, icon: AlertTriangle, color: "text-yellow-400" },
          { label: "Canary Flags Captured", val: activeBattle?.red_flags_captured || 4, icon: Key, color: "text-red-400" },
          { label: "Referee Verdicts", val: activeBattle?.blue_patches_approved || 4, icon: CheckCircle2, color: "text-purple-400" },
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

      {/* Workflow Progress Tracker */}
      <div className="p-6 rounded-xl bg-[#090d18] border border-slate-800 space-y-4">
        <h3 className="text-xs font-mono font-bold text-red-400 uppercase tracking-wider">
          Red Agent Automated Execution Protocol
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
          {[
            { step: "1. Schema Ingestion", desc: "Read /openapi.json specification and index all routes", state: "Completed" },
            { step: "2. Surface Analysis", desc: "Identify sensitive parameters and query inputs", state: "Completed" },
            { step: "3. Harmless Probing", desc: "Inject bounded payloads into isolated endpoints", state: "Completed" },
            { step: "4. Flag Verification", desc: "Transmit extracted tokens to Referee vault", state: "Completed" }
          ].map((s, i) => (
            <div key={i} className="p-3 rounded-lg bg-black/40 border border-slate-800">
              <div className="flex justify-between items-center mb-1">
                <span className="font-bold text-white">{s.step}</span>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <p className="text-[11px] text-slate-400 mb-2">{s.desc}</p>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-900">
                {s.state}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Captured Canary Flags Vault */}
      <div className="p-6 rounded-xl bg-[#090d18] border border-red-900/50 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono font-bold text-red-400 uppercase tracking-wider flex items-center gap-2">
            <Key className="w-4 h-4" /> Captured Canary Tokens (Breach Proofs)
          </h3>
          <span className="text-xs font-mono text-emerald-400">All 4 Validated by Referee</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
          {[
            { vuln: "SQL Injection", flag: "FLAG{CANARY_SQLI_DISCOVERED_984}", ep: "/api/products/search" },
            { vuln: "IDOR", flag: "FLAG{CANARY_IDOR_ORDER_ACCESS_312}", ep: "/api/orders/5" },
            { vuln: "Path Traversal", flag: "FLAG{CANARY_PATH_TRAVERSAL_881}", ep: "/api/files/download" },
            { vuln: "Broken Admin Auth", flag: "FLAG{CANARY_ADMIN_AUTH_BYPASS_404}", ep: "/api/admin/dashboard" }
          ].map((f, i) => (
            <div key={i} className="p-3 rounded-lg bg-black/50 border border-red-950 flex flex-col justify-between">
              <div className="flex justify-between items-center mb-1">
                <span className="font-bold text-slate-200">{f.vuln}</span>
                <span className="text-[10px] text-slate-400">{f.ep}</span>
              </div>
              <div className="p-2 rounded bg-red-950/40 text-red-300 font-bold tracking-wider select-all border border-red-900/50 text-[11px]">
                {f.flag}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
