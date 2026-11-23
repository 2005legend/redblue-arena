import React, { useEffect, useState } from 'react';
import {
  X,
  Swords,
  Sliders,
  Terminal,
  Cpu,
  Play,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';
import { getTargetConfig, TargetStatus } from '../services/api';

interface BattleConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartBattle: (config?: any) => Promise<void>;
}

export const BattleConfigModal: React.FC<BattleConfigModalProps> = ({
  isOpen,
  onClose,
  onStartBattle
}) => {
  const [config, setConfig] = useState<TargetStatus | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setConfigError(null);
    getTargetConfig().then(setConfig).catch((e) => setConfigError(e.message));
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onStartBattle();
      onClose();
    } catch (err: any) {
      alert(err.message || "Failed to start the match.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-3xl bg-[#0a0e19] border border-cyan-500/40 rounded-xl shadow-2xl overflow-hidden my-8 glow-cyan">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-[#0d1322] border-b border-cyan-900/50">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center">
              <Swords className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide">Battle Configuration</h2>
              <p className="text-xs text-cyan-400/80 font-mono">Scenario comes from arena.yaml - nothing is simulated</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div className="p-3 rounded-lg bg-cyan-950/40 border border-cyan-800/60 text-xs font-mono text-cyan-200 leading-relaxed">
            The orchestrator launches with the repository's real settings below. The web UI is
            read-only: it does not rewrite arena.yaml, swap models, or skip the referee.
          </div>

          {configError && (
            <div className="p-3 rounded-lg bg-red-950/40 border border-red-800 text-xs font-mono text-red-300">
              Could not load arena.yaml: {configError}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3.5 rounded-lg bg-[#070a13] border border-slate-800">
              <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400 uppercase mb-1.5">
                <Terminal className="w-3 h-3 text-cyan-400" /> Target app
              </div>
              <div className="text-xs font-mono text-white break-all">{config?.app_dir || 'loading...'}</div>
            </div>
            <div className="p-3.5 rounded-lg bg-[#070a13] border border-slate-800">
              <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400 uppercase mb-1.5">
                <Cpu className="w-3 h-3 text-cyan-400" /> Extraction strategy
              </div>
              <div className="text-xs font-mono text-white">{config?.strategy || 'loading...'}</div>
            </div>
            <div className="p-3.5 rounded-lg bg-[#070a13] border border-slate-800">
              <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400 uppercase mb-1.5">
                <Sliders className="w-3 h-3 text-cyan-400" /> Admin routes under test
              </div>
              <div className="text-xs font-mono text-white break-all">{(config?.admin_routes || []).join(', ') || '—'}</div>
            </div>
            <div className="p-3.5 rounded-lg bg-[#070a13] border border-slate-800">
              <div className="flex items-center gap-1.5 text-[10px] font-mono text-slate-400 uppercase mb-1.5">
                <ShieldCheck className="w-3 h-3 text-cyan-400" /> Referee
              </div>
              <div className="text-xs font-mono text-white">Pytest functional + exploit replay</div>
            </div>
          </div>

          <div className="p-3.5 rounded-lg bg-black/50 border border-slate-800 text-[11px] font-mono text-slate-400 leading-relaxed space-y-1">
            <div>Agent models: configured in models.yaml / environment</div>
            <div>Target sandbox: fresh copy on a localhost port, host-locked to this machine.</div>
            <div>Pacing: the orchestrator uses its configured pacing; replay speed is independent.</div>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-lg text-xs font-bold bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 hover:from-cyan-400 hover:to-blue-500 text-white glow-cyan transition transform active:scale-95 disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>{loading ? "Starting sandbox..." : "Launch Live Match"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
