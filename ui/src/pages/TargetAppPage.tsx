import React, { useEffect, useState } from 'react';
import {
  Layers,
  ShieldCheck,
  ShieldAlert,
  RefreshCw,
  Server,
  FileText,
  KeyRound,
  Route,
  Globe,
  ExternalLink
} from 'lucide-react';
import { getTargetConfig, getTargetLive, TargetStatus, TargetLive } from '../services/api';

const VECTORS = [
  { id: 'sqli', name: 'SQL Injection', key: 'sqli' },
  { id: 'idor', name: 'IDOR', key: 'idor' },
  { id: 'path_traversal', name: 'Path Traversal', key: 'path_traversal' },
  { id: 'admin_auth', name: 'Admin Auth Bypass', key: 'admin_auth' },
  { id: 'mass_assignment', name: 'Mass Assignment', key: 'mass_assignment' },
  { id: 'debug_exposure', name: 'Debug Endpoint Exposure', key: 'debug_exposure' },
  { id: 'code_injection', name: 'Code Injection (eval)', key: 'code_injection' },
];

export const TargetAppPage: React.FC = () => {
  const [config, setConfig] = useState<TargetStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [live, setLive] = useState<TargetLive | null>(null);

  const loadConfig = async () => {
    setLoading(true);
    try {
      setConfig(await getTargetConfig());
      setError(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
    const interval = setInterval(loadConfig, 8000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let stop = false;
    const tick = async () => {
      try {
        const l = await getTargetLive();
        if (!stop) setLive(l);
      } catch {
        if (!stop) setLive(null);
      }
    };
    tick();
    const interval = setInterval(tick, 3000);
    return () => {
      stop = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Title & real status */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-xl bg-[#090d18] border border-cyan-900/60 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            <h1 className="text-xl font-black text-white tracking-wide">TARGET APPLICATION ENCLAVE</h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
              FASTAPI + SQLITE
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Read-only view of the target described by arena.yaml. {config?.note}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <span className={`text-xs font-mono px-3 py-1.5 rounded-lg border ${
            config?.status === 'operational'
              ? 'bg-emerald-950/40 border-emerald-700 text-emerald-300'
              : 'bg-slate-900 border-slate-700 text-slate-300'
          }`}>
            {config?.status === 'operational' ? 'MATCH IN PROGRESS' : 'IDLE (no live match)'}
          </span>
          <button
            onClick={loadConfig}
            title="Refresh config"
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-950/40 border border-red-800 text-xs font-mono text-red-300 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4" /> {error}
        </div>
      )}

      {/* The real storefront, straight from the sandbox port the red agent is hitting */}
      <div className="rounded-xl bg-[#090d18] border border-slate-800 overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-4 py-3 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <Globe className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider">
              Live Victim Site
            </h3>
            <span className="text-[10px] font-mono text-slate-500">/target</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
              live?.alive
                ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                : 'bg-slate-900 text-slate-400 border-slate-700'
            }`}>
              {live?.alive ? `TARGET LIVE :${live.port}` : 'OFFLINE'}
            </span>
            {live?.url && (
              <a
                href={live.url}
                target="_blank"
                rel="noreferrer"
                className="text-[10px] font-mono px-2 py-0.5 rounded border border-cyan-800 bg-cyan-950 text-cyan-300 hover:bg-cyan-900 flex items-center gap-1"
              >
                open <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>
        {live?.alive && live.url ? (
          <iframe
            src={live.url}
            title="MiniShop victim site"
            sandbox="allow-scripts allow-forms allow-same-origin"
            className="w-full h-[560px] bg-[#f6f4ee]"
          />
        ) : (
          <div className="h-40 flex flex-col items-center justify-center gap-1 text-center px-6">
            <p className="text-xs font-mono text-slate-400">
              No target is running right now.
            </p>
            <p className="text-[11px] font-mono text-slate-600">
              Start a battle and the real storefront appears here while it is under attack.
            </p>
          </div>
        )}
      </div>

      {/* Patch status, derived from the latest recorded match */}
      <div className="p-4 rounded-xl bg-[#090d18] border border-slate-800">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider">
            Vulnerability Coverage After the Latest Match
          </h3>
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
            config?.global_mode === 'secure'
              ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
              : 'bg-red-950 text-red-300 border-red-800'
          }`}>
            {config?.global_mode === 'secure' ? 'ALL CLASSES PATCHED' : 'OPEN CLASSES REMAIN'}
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {VECTORS.map((v) => {
            const isPatched = config?.patches?.[v.key] ?? false;
            return (
              <div
                key={v.id}
                className={`p-3 rounded-lg border flex items-center justify-between ${
                  isPatched ? 'bg-emerald-950/30 border-emerald-600/50' : 'bg-red-950/30 border-red-600/40'
                }`}
              >
                <span className="text-xs font-bold text-white">{v.name}</span>
                <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                  isPatched ? 'bg-emerald-900/60 text-emerald-300' : 'bg-red-900/60 text-red-300'
                }`}>
                  {isPatched ? 'PATCHED' : 'VULNERABLE'}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Real configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 rounded-xl bg-[#090d18] border border-slate-800 space-y-4">
          <h3 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
            <Server className="w-3.5 h-3.5" /> Target Configuration (arena.yaml)
          </h3>
          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between gap-4 p-2.5 rounded bg-black/40 border border-slate-800">
              <span className="text-slate-400 shrink-0">App directory</span>
              <span className="text-cyan-300 break-all text-right">{config?.app_dir || '—'}</span>
            </div>
            <div className="flex justify-between gap-4 p-2.5 rounded bg-black/40 border border-slate-800">
              <span className="text-slate-400 shrink-0">Match strategy</span>
              <span className="text-white font-bold">{config?.strategy || '—'}</span>
            </div>
            <div className="flex justify-between gap-4 p-2.5 rounded bg-black/40 border border-slate-800">
              <span className="text-slate-400 shrink-0">Admin routes tested</span>
              <span className="text-white text-right">{(config?.admin_routes || []).join(', ') || '—'}</span>
            </div>
            <div className="flex justify-between gap-4 p-2.5 rounded bg-black/40 border border-slate-800">
              <span className="text-slate-400 shrink-0">Traversal loot paths</span>
              <span className="text-white text-right">{(config?.loot_paths || []).join(', ') || '—'}</span>
            </div>
          </div>
        </div>

        <div className="p-5 rounded-xl bg-[#090d18] border border-slate-800 space-y-4">
          <h3 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
            <KeyRound className="w-3.5 h-3.5" /> Canary Ownership
          </h3>
          <div className="space-y-2 text-xs font-mono">
            {Object.keys(config?.flag_owners || {}).length === 0 && (
              <div className="p-2.5 rounded bg-black/40 border border-slate-800 text-slate-500">
                No owner-tagged canaries in this config.
              </div>
            )}
            {Object.entries(config?.flag_owners || {}).map(([flag, owner]) => (
              <div key={flag} className="flex justify-between gap-4 p-2.5 rounded bg-black/40 border border-amber-900/40">
                <span className="text-amber-300 break-all">{flag}</span>
                <span className="text-slate-300 shrink-0">owner: {owner}</span>
              </div>
            ))}
          </div>
          <p className="text-[11px] text-slate-500 font-mono leading-relaxed">
            A captured flag that the attacker's own account owns is not counted as a breach, so
            access-control bypasses have to be real.
          </p>
        </div>
      </div>

      {/* How the target is used in a match */}
      <div className="p-5 rounded-xl bg-[#090d18] border border-slate-800 space-y-3">
        <h3 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5" /> How the Target Runs
        </h3>
        <ul className="text-xs text-slate-300 font-mono space-y-2 leading-relaxed">
          <li className="flex gap-2"><Route className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
            Each match copies this app, its seed database and fixture files into a fresh work directory.
          </li>
          <li className="flex gap-2"><ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
            It is served on a localhost port from the sandbox allow-list. The host lock rejects any other host or port.
          </li>
          <li className="flex gap-2"><ShieldAlert className="w-3.5 h-3.5 text-red-400 shrink-0 mt-0.5" />
            There is no interactive exploit console here: attacks are driven by the match engine so the
            screenshots and logs come from real, recorded runs. Watch them on the Live Arena page.
          </li>
        </ul>
      </div>
    </div>
  );
};
