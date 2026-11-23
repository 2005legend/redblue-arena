import React, { useEffect, useState } from 'react';
import {
  Scale,
  CheckCircle2,
  Terminal,
  ShieldAlert
} from 'lucide-react';
import { getBattles, getBattleReport, BattleReport } from '../services/api';

export const RefereePage: React.FC = () => {
  const [report, setReport] = useState<BattleReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const battles = await getBattles();
        if (battles.length > 0) {
          setReport(await getBattleReport(battles[0].id));
        }
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const acceptanceCriteria = [
    { title: "Canary Flag Ground Truth", desc: "Each captured token is compared against the canary planted in the target's seed data, not against the model's own claim." },
    { title: "Patch Application Check", desc: "The proposed edit must parse as valid Python and stay inside the target app directory." },
    { title: "Functional Pytest Suite", desc: "The target's functional tests must still pass after the patch is applied to a fresh sandbox copy." },
    { title: "Security Replay", desc: "The referee re-runs the exact exploit packet. A patch only counts if the canary is no longer returned." },
    { title: "Health Verification", desc: "Routes must keep responding; disabling a handler is not an acceptable fix." },
    { title: "No LLM Self-Assessment", desc: "Verdicts come from process exit codes and response bodies, never from the agents' own reports." },
  ];

  const findings = report?.findings ?? [];
  const mitigated = findings.filter((f) => f.status === 'Mitigated').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-xl bg-[#090d18] border border-purple-900/50 glow-purple">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-purple-950/80 border border-purple-500/50 flex items-center justify-center glow-purple">
            <Scale className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-black text-white tracking-wide">DETERMINISTIC REFEREE & JUDGING HARNESS</h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase bg-purple-950 text-purple-400 border border-purple-700">
                INDEPENDENT ARBITER
              </span>
            </div>
            <p className="text-xs text-purple-300 font-mono mt-0.5">
              Pytest-based verification - no trust in either agent's self-assessment
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono">
          <span className="px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>{report ? `${mitigated}/${findings.length} findings mitigated in ${report.battle.id}` : 'no battle loaded'}</span>
          </span>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-950/40 border border-red-800 text-xs font-mono text-red-300 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4" /> {error}
        </div>
      )}

      {/* Acceptance Criteria Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {acceptanceCriteria.map((c, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-[#090d18] border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-white">{c.title}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-900">
                  CHECK {idx + 1}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-3">{c.desc}</p>
            </div>
            <div className="flex items-center space-x-1.5 text-[11px] font-mono text-slate-500">
              <CheckCircle2 className="w-3.5 h-3.5 text-purple-400" />
              <span>Applied to every patch verdict</span>
            </div>
          </div>
        ))}
      </div>

      {/* Latest verification matrix, from the recorded log */}
      <div className="p-6 rounded-xl bg-[#090d18] border border-slate-800 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-purple-400" />
            <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
              Latest Referee Verdicts {report ? `(${report.battle.id})` : ''}
            </h3>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            Target: {report?.executive_summary.target_app || 'local sandbox'}
          </span>
        </div>

        <div className="p-4 rounded-lg bg-black border border-slate-800 font-mono text-xs overflow-x-auto space-y-1">
          {loading && <div className="text-slate-500">Loading verdicts...</div>}
          {!loading && findings.length === 0 && (
            <div className="text-slate-500">No findings recorded yet. Run a match to produce referee verdicts.</div>
          )}
          {findings.map((f, idx) => (
            <div key={idx} className="flex flex-wrap gap-x-3">
              <span className={f.status === 'Mitigated' ? 'text-emerald-400' : 'text-orange-400'}>
                [{f.status === 'Mitigated' ? 'PASS' : 'OPEN'}]
              </span>
              <span className="text-cyan-400">{f.vuln_type}</span>
              <span className="text-slate-400">{f.endpoint}</span>
              <span className="text-slate-300">{f.canary_token}</span>
              <span className="text-slate-500">verification: {f.patch_verification}</span>
              <span className="text-slate-500">functional: {f.functional_tests}</span>
              <span className="text-slate-500">replay: {f.security_tests}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
