import React, { useState, useEffect, useRef } from 'react';
import {
  Swords,
  Terminal,
  Cpu,
  Play,
  Activity,
  CheckCircle2,
  ShieldAlert,
  Radio,
  Key,
  FileCode2,
  Sliders,
  RotateCcw,
  Zap,
  ExternalLink,
  Globe,
  X
} from 'lucide-react';
import {
  getBattles,
  getBattle,
  getTargetLive,
  startMatch,
  connectBattleWS,
  Battle,
  BattleEvent,
  TargetLive
} from '../services/api';

interface BattleArenaPageProps {
  onOpenConfig: () => void;
  activeBattleId?: string;
  setActiveBattleId?: (id: string) => void;
}

interface VulnPopup {
  id: number;
  state: 'breach' | 'defended';
  route: string;
  vuln_class: string;
  flag: string;
  method: string;
  path: string;
  params?: Record<string, string>;
  json?: any;
  source: string;
  ttp_seconds?: number;
  cached?: boolean;
}

const CLASS_LABEL: Record<string, string> = {
  sqli: 'SQL Injection',
  idor: 'IDOR',
  admin_bypass: 'Admin Bypass',
  path_traversal: 'Path Traversal',
};

function packetText(p: VulnPopup) {
  let text = `${p.method} ${p.path}`;
  if (p.params && Object.keys(p.params).length) text += ` ${JSON.stringify(p.params)}`;
  if (p.json) text += ` ${JSON.stringify(p.json)}`;
  return text;
}

const VulnPopupCard: React.FC<{ popup: VulnPopup; onDismiss: (id: number) => void }> = ({ popup, onDismiss }) => {
  useEffect(() => {
    const t = setTimeout(() => onDismiss(popup.id), popup.state === 'defended' ? 5000 : 25000);
    return () => clearTimeout(t);
  }, [popup.id, popup.state, onDismiss]);

  const defended = popup.state === 'defended';
  return (
    <div className={`pointer-events-auto rounded-xl border p-3.5 shadow-2xl font-mono transition-all ${
      defended
        ? 'bg-[#0c1d18] border-emerald-500/80 shadow-emerald-900/40'
        : 'bg-[#170f13] border-red-500/90 shadow-red-900/40'
    }`}>
      <div className={`flex items-center gap-2 text-[10px] font-black tracking-widest uppercase ${
        defended ? 'text-emerald-400' : 'text-red-400'
      }`}>
        {defended ? <CheckCircle2 className="w-3.5 h-3.5" /> : <ShieldAlert className="w-3.5 h-3.5" />}
        <span>{defended ? 'DEFENDED' : 'VULNERABILITY FOUND'}</span>
        <span className="text-slate-500 normal-case tracking-normal">· {popup.source === 'sweep' ? 'template' : 'model'}</span>
        <button onClick={() => onDismiss(popup.id)} className="ml-auto text-slate-500 hover:text-white">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
      <div className={`text-base font-bold mt-2 ${defended ? 'text-emerald-200' : 'text-white'}`}>
        {CLASS_LABEL[popup.vuln_class] || popup.vuln_class}
      </div>
      <div className="text-[11px] text-slate-400 mt-0.5 break-all">{popup.route}</div>
      <div className="text-[11px] text-slate-300 mt-1.5 break-all">{packetText(popup)}</div>
      <div className="text-[11px] text-amber-300 mt-1.5 break-all">canary: {popup.flag}</div>
      {defended && (
        <div className="text-[11px] text-emerald-400 mt-1.5">
          Patch verified in {popup.ttp_seconds}s{popup.cached ? ' · cached fix, 0 tokens' : ''}
        </div>
      )}
    </div>
  );
};

export const BattleArenaPage: React.FC<BattleArenaPageProps> = ({
  onOpenConfig,
  activeBattleId,
  setActiveBattleId
}) => {
  const [battles, setBattles] = useState<Battle[]>([]);
  const [selectedBattleId, setSelectedBattleId] = useState<string>(activeBattleId || '');
  const [battle, setBattle] = useState<Battle | null>(null);
  const [events, setEvents] = useState<BattleEvent[]>([]);
  const [popups, setPopups] = useState<VulnPopup[]>([]);
  const [wsState, setWsState] = useState<'idle' | 'connecting' | 'live' | 'replay'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [live, setLive] = useState<TargetLive | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const timelineBoxRef = useRef<HTMLDivElement | null>(null);
  const popupId = useRef(0);

  const loadBattles = async () => {
    try {
      const data = await getBattles();
      setBattles(data);
      return data;
    } catch (e: any) {
      setError(e.message);
      return [];
    }
  };

  useEffect(() => {
    loadBattles().then((data) => {
      if (!selectedBattleId && data.length > 0) {
        setSelectedBattleId(data[0].id);
        if (setActiveBattleId) setActiveBattleId(data[0].id);
      }
    });
    const interval = setInterval(loadBattles, 8000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (activeBattleId && activeBattleId !== selectedBattleId) setSelectedBattleId(activeBattleId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeBattleId]);

  // Where the sandbox is serving the target right now. The centre panel embeds that real
  // storefront (served by /target) so the audience watches the site leak data while the
  // feeds report it, instead of only reading log lines.
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
    const interval = setInterval(tick, 2500);
    return () => {
      stop = true;
      clearInterval(interval);
    };
  }, []);

  // Load the battle summary and stream its recorded log (or the live feed when it is running).
  useEffect(() => {
    if (!selectedBattleId) return;
    let cancelled = false;

    const open = async () => {
      setError(null);
      setEvents([]);
      setPopups([]);
      wsRef.current?.close();
      try {
        let b: Battle | null = null;
        for (let attempt = 0; attempt < 5 && !b; attempt++) {
          try {
            b = await getBattle(selectedBattleId);
          } catch (e) {
            if (attempt === 4) throw e;
            await new Promise((r) => setTimeout(r, 400));
          }
        }
        if (cancelled || !b) return;
        setBattle(b);
        setWsState('connecting');
        const replay = b.status === 'running' ? undefined : b.replay;
        wsRef.current = connectBattleWS(
          replay,
          (ev) => handleEvent(ev),
          () => !cancelled && setWsState('idle'),
        );
        setWsState(b.status === 'running' ? 'live' : 'replay');
        if (b.status === 'running') {
          // The live socket sends the full backlog first; mark it live as soon as it opens.
          wsRef.current.onopen = () => setWsState('live');
        }
      } catch (e: any) {
        setError(e.message);
        setBattle(null);
      }
    };

    open();
    return () => {
      cancelled = true;
      wsRef.current?.close();
      wsRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedBattleId]);

  const handleEvent = (ev: BattleEvent) => {
    const raw = ev.details || {};
    if (raw.type === 'match_start') {
      setEvents([ev]);
      setPopups([]);
      return;
    }
    setEvents((prev) => [...prev, ev]);

    if (raw.type === 'breach') {
      const id = ++popupId.current;
      setPopups((prev) => [...prev, {
        id,
        state: 'breach' as const,
        route: raw.route,
        vuln_class: raw.vuln_class,
        flag: raw.flag,
        method: raw.method || 'GET',
        path: raw.path || raw.route,
        params: raw.params,
        json: raw.json,
        source: raw.source || 'llm',
      }].slice(-6));
    }
    if (raw.type === 'patched') {
      setPopups((prev) => prev.map((p) => (
        p.state === 'breach' && p.route === raw.route
          ? { ...p, state: 'defended', ttp_seconds: raw.ttp_seconds, cached: raw.cached }
          : p
      )));
    }
    if (raw.type === 'match_end') {
      setWsState(raw.sample ? 'replay' : 'idle');
      loadBattles();
      getBattle(selectedBattleId).then(setBattle).catch(() => {});
    }
  };

  // Scroll only the telemetry list, never the page: during a live match an event arrives every
  // few seconds, and a page-level scroll would carry the arena away from the victim panel.
  useEffect(() => {
    const box = timelineBoxRef.current;
    if (box) box.scrollTop = box.scrollHeight;
  }, [events]);

  const dismissPopup = (id: number) => setPopups((prev) => prev.filter((p) => p.id !== id));

  const handleStartLive = async () => {
    setStarting(true);
    setError(null);
    try {
      const matchId = await startMatch();
      if (setActiveBattleId) setActiveBattleId(matchId);
      setSelectedBattleId(matchId);
      await loadBattles();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setStarting(false);
    }
  };

  const breaches = events.filter((e) => e.details?.type === 'breach');
  const patches = events.filter((e) => e.details?.type === 'patched');
  const lastHealth = [...events].reverse().find((e) => e.details?.type === 'health');
  const activeEndpoint = [...events].reverse().find((e) => e.endpoint)?.endpoint;

  const findingsCount = breaches.length || battle?.red_discoveries || 0;
  const flagsCount = new Set(breaches.map((e) => e.details?.flag)).size || battle?.red_flags_captured || 0;
  const patchCount = patches.length || battle?.blue_patches_generated || 0;
  const verifiedCount = patches.filter((e) => e.details?.ok !== false).length || battle?.blue_patches_approved || 0;
  const healthText = lastHealth
    ? `${lastHealth.details.passed}/${(lastHealth.details.passed || 0) + (lastHealth.details.failed || 0)} tests`
    : battle?.final_health || 'unknown';

  const captured = Array.from(new Map(
    breaches.map((e) => [e.details?.flag, {
      vuln_class: e.details?.vuln_class, flag: e.details?.flag, route: e.details?.route,
    }]),
  ).values());

  const verified = Array.from(new Map(
    patches.map((e) => [e.details?.route, {
      vuln_class: e.details?.vuln_class, route: e.details?.route,
      ttp: e.details?.ttp_seconds, cached: e.details?.cached,
    }]),
  ).values());

  const isRunning = battle?.status === 'running';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 relative">
      {/* Live vulnerability pop-up stack */}
      <div className="fixed right-4 top-20 z-40 w-[340px] max-h-[calc(100vh-120px)] overflow-y-auto space-y-2.5 pointer-events-none">
        {popups.map((p) => (
          <VulnPopupCard key={p.id} popup={p} onDismiss={dismissPopup} />
        ))}
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-950/40 border border-red-800 text-xs font-mono text-red-300 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4" /> {error}
        </div>
      )}

      {/* Top SOC Bar with Battle Selector and Controls */}
      <div className="p-4 rounded-xl bg-[#090d18] border border-cyan-900/60 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-red-600/30 via-cyan-500/20 to-blue-600/30 border border-cyan-500/40 flex items-center justify-center glow-cyan">
            <Swords className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-black text-white tracking-wide">LIVE CYBER-BATTLE ARENA</h1>
              <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-black/60 border border-slate-700 text-[10px] font-mono">
                <span className={`w-2 h-2 rounded-full ${
                  wsState === 'live' ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'
                }`}></span>
                <span className={wsState === 'live' ? 'text-emerald-400' : 'text-slate-400'}>
                  {wsState === 'live' ? 'LIVE TELEMETRY' : wsState === 'replay' ? 'RECORDED LOG REPLAY' : 'DISCONNECTED'}
                </span>
              </div>
            </div>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              Red exploitation events stream in; each canary capture pops up until Blue's patch is verified
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={selectedBattleId}
            onChange={(e) => {
              setSelectedBattleId(e.target.value);
              if (setActiveBattleId) setActiveBattleId(e.target.value);
            }}
            className="px-3 py-1.5 rounded-lg bg-black border border-slate-700 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-400"
          >
            {battles.map((b) => (
              <option key={b.id} value={b.id}>
                {b.id} - {b.status}
              </option>
            ))}
          </select>

          <button
            onClick={handleStartLive}
            disabled={starting || isRunning}
            title={isRunning ? 'A match is already running' : 'Start a match with the repo arena.yaml'}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-gradient-to-r from-red-600 to-cyan-500 hover:from-red-500 hover:to-cyan-400 text-white rounded-lg text-xs font-bold glow-cyan transition transform active:scale-95 disabled:opacity-40"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{starting ? 'Launching...' : isRunning ? 'Match Running' : 'Start Live Match'}</span>
          </button>

          {battle && battle.status !== 'running' && (
            <button
              onClick={() => {
                wsRef.current?.close();
                setEvents([]);
                setPopups([]);
                wsRef.current = connectBattleWS(battle.replay, handleEvent, () => setWsState('idle'));
                setWsState('replay');
              }}
              className="flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Replay</span>
            </button>
          )}

          <button
            onClick={onOpenConfig}
            className="flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-lg text-xs font-medium border border-cyan-900/60 transition"
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Config</span>
          </button>
        </div>
      </div>

      {/* Two-tier proof strip: deterministic fast-path vs LLM agents, taken from the match log */}
      {battle && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="p-3.5 rounded-xl bg-[#07100d] border border-emerald-900/60 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-700/60 flex items-center justify-center">
                <Zap className="w-4 h-4 text-emerald-400" />
              </div>
              <div>
                <div className="text-[10px] font-mono font-bold tracking-widest text-emerald-400">
                  TIER 1 · DETERMINISTIC FAST-PATH
                </div>
                <div className="text-[11px] font-mono text-slate-400">
                  {battle.sweep_requests} sweep requests · {battle.sweep_findings} findings · {battle.cache_hits} cached patches
                </div>
              </div>
            </div>
            <span className={`px-2 py-1 rounded text-[10px] font-mono font-bold border ${
              battle.llm_calls === 0
                ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800'
                : 'bg-slate-900 text-slate-400 border-slate-700'
            }`}>
              {battle.llm_calls === 0
                ? '0 LLM calls · 0 tokens'
                : battle.llm_calls === null
                  ? 'calls not recorded'
                  : 'cache miss, model ran'}
            </span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#090d18] border border-cyan-900/60 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-800/60 flex items-center justify-center">
                <Cpu className="w-4 h-4 text-cyan-400" />
              </div>
              <div>
                <div className="text-[10px] font-mono font-bold tracking-widest text-cyan-400">
                  TIER 2 · LLM AGENTS
                </div>
                <div className="text-[11px] font-mono text-slate-400">
                  {battle.llm_calls === 0
                    ? 'Not needed: sweep + cache closed every finding'
                    : battle.llm_calls === null
                      ? 'Older log: per-call counts were not recorded'
                      : 'Used where the fast path had no answer'}
                </div>
              </div>
            </div>
            <span className="px-2 py-1 rounded text-[10px] font-mono font-bold border bg-slate-900 text-cyan-300 border-cyan-900 text-right leading-4">
              <span className="text-red-400">RED</span> {battle.red_llm_calls ?? '—'} calls · {battle.red_tokens ?? '—'} tok
              <br />
              <span className="text-blue-400">BLUE</span> {battle.blue_llm_calls ?? '—'} calls · {battle.blue_tokens ?? '—'} tok
            </span>
          </div>
        </div>
      )}


      {/* LIVE VICTIM SITE: full width, because this is the actual app under attack.
          /target?embed=1 is the same victim page as the full-screen view, without its feed. */}
      <div className="rounded-xl bg-[#090d18] border border-cyan-900/60 overflow-hidden">
        <div className="flex flex-wrap items-center gap-2 px-4 py-2.5 border-b border-cyan-950">
          <span className="flex items-center gap-1.5 text-[11px] font-mono font-bold tracking-widest text-cyan-400">
            <Globe className="w-3.5 h-3.5" /> LIVE VICTIM SITE
          </span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-cyan-900 bg-cyan-950/60 text-cyan-300">FASTAPI</span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-cyan-900 bg-cyan-950/60 text-cyan-300">SQLITE</span>
          <span className="text-[10px] font-mono text-slate-500 hidden md:inline">
            the real storefront the agents are hitting, served by the sandbox
          </span>
          <span className="ml-auto flex items-center gap-2">
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
              live?.alive
                ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                : 'bg-slate-900 text-slate-400 border-slate-700'
            }`}>
              {live?.alive ? `LIVE :${live.port}` : 'OFFLINE — start a match'}
            </span>
            <a href="/target" target="_blank" rel="noreferrer"
              className="text-[10px] font-mono px-2 py-0.5 rounded border border-cyan-800 bg-cyan-950 text-cyan-300 hover:bg-cyan-900 flex items-center gap-1">
              full screen <ExternalLink className="w-2.5 h-2.5" />
            </a>
          </span>
        </div>
        {live?.alive && live.url ? (
          <iframe src="/target?embed=1" title="Live victim site under attack"
            className="w-full h-[520px] bg-[#070b12]" />
        ) : (
          <div className="h-[300px] flex flex-col items-center justify-center gap-2 px-6 text-center">
            <ShieldAlert className="w-6 h-6 text-slate-600" />
            <p className="text-xs font-mono text-slate-400">No target is running.</p>
            <p className="text-[11px] font-mono text-slate-600">
              Start a match and the real storefront appears here while Red attacks it —
              leaks the canary, then refuses the same request after every verified patch.
            </p>
          </div>
        )}
      </div>

      {/* 3-COLUMN MAIN ARENA GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* LEFT PANEL: RED AGENT */}
        <div className="lg:col-span-4 p-5 rounded-xl bg-[#090d18] border border-red-900/40 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-red-950 pb-3 mb-3">
              <div className="flex items-center space-x-2">
                <Terminal className="w-5 h-5 text-red-400" />
                <span className="text-sm font-bold text-red-300 tracking-wider">RED AGENT</span>
              </div>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                isRunning ? 'bg-red-950 text-red-400 border border-red-700 animate-pulse'
                  : 'bg-slate-900 text-slate-400 border border-slate-800'
              }`}>
                {isRunning ? 'attacking' : battle?.status || 'idle'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono mb-4">
              <div className="p-2.5 rounded-lg bg-black/50 border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Findings Confirmed</span>
                <span className="text-lg font-bold text-white">{findingsCount}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-red-950/30 border border-red-900/60">
                <span className="text-red-300 block text-[10px]">Canaries Captured</span>
                <span className="text-lg font-bold text-red-400">{flagsCount}</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-black/60 border border-slate-800 text-xs font-mono space-y-1 mb-4">
              <div className="text-[10px] text-red-400 uppercase font-bold flex items-center gap-1">
                <Activity className="w-3 h-3" /> Strategy
              </div>
              <p className="text-slate-300 leading-snug">
                {battle?.simulation_mode === 'sweep'
                  ? 'Deterministic template sweep first; the model only runs on leftover surface.'
                  : battle?.simulation_mode === 'llm'
                    ? 'Model-driven probing across the discovered routes.'
                    : 'Template sweep first, then the model for anything left unresolved.'}
              </p>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Captured Canary Vault:</span>
              {captured.length === 0 && (
                <div className="p-2 rounded bg-black/40 border border-slate-800 text-[10px] font-mono text-slate-500">
                  No canaries captured in the current buffer.
                </div>
              )}
              {captured.map((c, i) => (
                <div key={i} className="p-2 rounded bg-black/40 border border-red-950 text-[10px] font-mono flex items-center justify-between gap-2">
                  <span className="text-slate-400 shrink-0">{CLASS_LABEL[c.vuln_class] || c.vuln_class}</span>
                  <span className="text-red-400 font-bold truncate">{c.flag}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CENTER PANEL: TARGET APPLICATION */}
        <div className="lg:col-span-4 p-5 rounded-xl bg-[#090d18] border border-cyan-900/50 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-cyan-950 pb-3 mb-3">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-5 h-5 text-cyan-400" />
                <span className="text-sm font-bold text-white tracking-wider">TARGET APPLICATION</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                HEALTH: {healthText}
              </span>
            </div>

            <div className="p-3.5 rounded-lg bg-black/60 border border-cyan-900/50 space-y-2 mb-4">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-400">Last Touched Endpoint:</span>
                <span className="flex items-center gap-1.5 text-cyan-400 font-bold">
                  <Radio className="w-3.5 h-3.5 animate-pulse" /> {isRunning ? 'ACTIVE' : 'IDLE'}
                </span>
              </div>
              <div className="text-xs font-mono text-cyan-300 font-bold bg-cyan-950/40 p-2 rounded border border-cyan-800/60 truncate">
                {activeEndpoint || battle?.selected_vulnerabilities?.join(', ') || 'awaiting events'}
              </div>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between p-2 rounded bg-black/40 border border-slate-800">
                <span className="text-slate-400">Sandbox Isolation:</span>
                <span className="text-emerald-400 font-bold">Localhost, host-locked</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-black/40 border border-slate-800">
                <span className="text-slate-400">Data Store:</span>
                <span className="text-white font-bold">SQLite seed database</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-black/40 border border-slate-800">
                <span className="text-slate-400">Referee:</span>
                <span className="text-purple-400 font-bold">Pytest, deterministic</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-black/40 border border-slate-800">
                <span className="text-slate-400">Target Duration:</span>
                <span className="text-white font-bold">{battle?.duration_seconds ?? 0}s recorded</span>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-cyan-950/30 border border-cyan-800/40 text-[11px] font-mono text-cyan-300 text-center">
            Zero external traffic allowed. Strict sandbox boundary enforced.
          </div>
        </div>

        {/* RIGHT PANEL: BLUE AGENT */}
        <div className="lg:col-span-4 p-5 rounded-xl bg-[#090d18] border border-blue-900/40 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-blue-950 pb-3 mb-3">
              <div className="flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-blue-400" />
                <span className="text-sm font-bold text-blue-300 tracking-wider">BLUE AGENT</span>
              </div>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                isRunning ? 'bg-blue-950 text-blue-400 border border-blue-700 animate-pulse'
                  : 'bg-slate-900 text-slate-400 border border-slate-800'
              }`}>
                {isRunning ? 'patching' : battle?.status || 'idle'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono mb-4">
              <div className="p-2.5 rounded-lg bg-black/50 border border-slate-800">
                <span className="text-slate-400 block text-[10px]">Patches Generated</span>
                <span className="text-lg font-bold text-white">{patchCount}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-900/60">
                <span className="text-emerald-300 block text-[10px]">Referee Verified</span>
                <span className="text-lg font-bold text-emerald-400">{verifiedCount}</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-black/60 border border-slate-800 text-xs font-mono space-y-1 mb-4">
              <div className="text-[10px] text-blue-400 uppercase font-bold flex items-center gap-1">
                <FileCode2 className="w-3 h-3" /> Verified Patches
              </div>
              <p className="text-slate-300 leading-snug">
                Blue rewrites the handler source, then the referee replays the exploit and runs the functional suite.
              </p>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Active Verified Patches:</span>
              {verified.length === 0 && (
                <div className="p-2 rounded bg-black/40 border border-slate-800 text-[10px] font-mono text-slate-500">
                  No verified patches in the current buffer.
                </div>
              )}
              {verified.map((p, i) => (
                <div key={i} className="p-2 rounded bg-black/40 border border-blue-950 text-[10px] font-mono flex items-center justify-between gap-2">
                  <span className="text-slate-300 truncate">{CLASS_LABEL[p.vuln_class] || p.vuln_class}</span>
                  <span className="text-emerald-400 font-bold shrink-0">{p.ttp}s{p.cached ? ' · cache' : ''}</span>
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
              Battle Telemetry & Referee Verdict Stream
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {events.length} telemetry events
          </span>
        </div>

        <div ref={timelineBoxRef} className="space-y-2 max-h-80 overflow-y-auto pr-2">
          {events.length === 0 ? (
            <div className="text-center py-10 text-xs font-mono text-slate-500">
              No events yet. Start a live match or pick a recorded battle to replay its log.
            </div>
          ) : (
            events.map((ev, idx) => {
              const isRed = ev.source === 'RED';
              const isBlue = ev.source === 'BLUE';
              const isReferee = ev.source === 'REFEREE';
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
                  <span className="text-[10px] text-slate-500 shrink-0 pt-0.5 w-14">
                    {ev.ts !== undefined ? `t+${ev.ts.toFixed(1)}s` : '--'}
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
        </div>
      </div>
    </div>
  );
};
