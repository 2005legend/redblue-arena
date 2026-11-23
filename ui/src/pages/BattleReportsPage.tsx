import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  Printer, 
  CheckCircle2, 
  ShieldCheck, 
  Award, 
  Calendar, 
  Clock, 
  Terminal, 
  Cpu, 
  Scale, 
  Activity,
  Layers
} from 'lucide-react';
import { getBattles, getBattleReport, Battle } from '../services/api';

export const BattleReportsPage: React.FC = () => {
  const [battles, setBattles] = useState<Battle[]>([]);
  const [selectedBattleId, setSelectedBattleId] = useState<string>('');
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadBattles();
  }, []);

  const loadBattles = async () => {
    try {
      const data = await getBattles();
      setBattles(data);
      if (data.length > 0) {
        setSelectedBattleId(data[0].id);
        fetchReport(data[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchReport = async (bId: string) => {
    setLoading(true);
    try {
      const rep = await getBattleReport(bId);
      setReport(rep);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header and Print Control */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-xl bg-[#090d18] border border-cyan-900/50 print:hidden">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <FileText className="w-6 h-6 text-cyan-400" />
            <h1 className="text-xl font-black text-white tracking-wide">BATTLE EVALUATION REPORTS</h1>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            Cryptographically logged battle assessments, test scores, and compliance validation reports
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={selectedBattleId}
            onChange={(e) => {
              setSelectedBattleId(e.target.value);
              fetchReport(e.target.value);
            }}
            className="px-3 py-2 bg-black border border-slate-700 rounded-lg text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-400"
          >
            {battles.map(b => (
              <option key={b.id} value={b.id}>
                {b.id} ({b.name})
              </option>
            ))}
          </select>

          <button
            onClick={handlePrint}
            className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-xs font-bold glow-cyan transition transform active:scale-95"
          >
            <Printer className="w-4 h-4" />
            <span>Print / Export PDF</span>
          </button>
        </div>
      </div>

      {/* Printable Report Document Card */}
      {report && (
        <div id="battle-report-document" className="p-8 sm:p-10 rounded-2xl bg-[#090d18] border border-slate-800 shadow-2xl space-y-8 print:p-0 print:border-none print:bg-white print:text-black">
          {/* Document Header */}
          <div className="flex flex-col sm:flex-row justify-between items-start border-b border-slate-800 pb-6 print:border-black">
            <div>
              <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs font-bold uppercase tracking-wider mb-1 print:text-blue-700">
                <span>ARENA CYBER-INTELLIGENCE PLATFORM</span>
              </div>
              <h2 className="text-2xl font-black text-white tracking-tight print:text-black">
                {report.executive_summary.title}
              </h2>
              <p className="text-xs font-mono text-slate-400 print:text-gray-600 mt-1">
                Report ID: {report.report_id} • Target: {report.executive_summary.target_app}
              </p>
            </div>
            <div className="mt-4 sm:mt-0 text-left sm:text-right font-mono text-xs">
              <span className="px-3 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold block print:bg-emerald-100 print:text-emerald-800">
                {report.battle.outcome}
              </span>
              <span className="text-slate-400 text-[10px] block mt-1 print:text-gray-500">
                Generated: {report.generated_at}
              </span>
            </div>
          </div>

          {/* Key Executive Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-4 rounded-xl bg-black/40 border border-slate-800 print:border-gray-300 print:bg-gray-50">
              <span className="text-slate-400 print:text-gray-500 block mb-1">Battle ID:</span>
              <span className="text-white print:text-black font-bold text-sm">{report.battle.id}</span>
            </div>
            <div className="p-4 rounded-xl bg-black/40 border border-slate-800 print:border-gray-300 print:bg-gray-50">
              <span className="text-slate-400 print:text-gray-500 block mb-1">Execution Duration:</span>
              <span className="text-white print:text-black font-bold text-sm">
                {roundNumber(report.battle.duration_seconds || 0)}s
              </span>
            </div>
            <div className="p-4 rounded-xl bg-black/40 border border-slate-800 print:border-gray-300 print:bg-gray-50">
              <span className="text-slate-400 print:text-gray-500 block mb-1">Canaries Captured:</span>
              <span className="text-red-400 print:text-red-700 font-bold text-sm">
                {report.battle.red_flags_captured} flags
              </span>
            </div>
            <div className="p-4 rounded-xl bg-black/40 border border-slate-800 print:border-gray-300 print:bg-gray-50">
              <span className="text-slate-400 print:text-gray-500 block mb-1">Patches Verified:</span>
              <span className="text-emerald-400 print:text-emerald-700 font-bold text-sm">
                {report.battle.blue_patches_approved} of {report.battle.blue_patches_generated} generated
              </span>
            </div>
          </div>

          {/* Detailed Verification Matrix */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white print:text-black uppercase tracking-wider font-mono">
              Deterministic Vulnerability Mitigation Matrix
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-800 print:border-gray-400 text-slate-400 print:text-gray-600">
                    <th className="py-2.5">Vulnerability Category</th>
                    <th>Status</th>
                    <th>Extracted Canary Token</th>
                    <th>Referee Validation</th>
                    <th>Pytest Functional</th>
                    <th>Pytest Security</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 print:divide-gray-200">
                  {report.findings.map((f: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-900/30">
                      <td className="py-3 font-bold text-white print:text-black">{f.vuln_type}</td>
                      <td>
                        <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-[10px] print:bg-cyan-100 print:text-cyan-900">
                          {f.status}
                        </span>
                      </td>
                      <td className="text-red-400 print:text-red-700 font-bold text-[11px]">{f.canary_token}</td>
                      <td className="text-emerald-400 print:text-emerald-700 font-bold">{f.patch_verification}</td>
                      <td className="text-slate-300 print:text-gray-700">{f.functional_tests}</td>
                      <td className="text-slate-300 print:text-gray-700">{f.security_tests}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Evaluation Scorecard */}
          <div className="p-6 rounded-xl bg-black/40 border border-slate-800 print:border-gray-400 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white print:text-black font-mono">
                Referee Scorecard & Health Verification
              </h3>
              <span className="text-xs font-mono text-emerald-400 font-bold print:text-emerald-700">
                Final health: {report.battle.final_health}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
              <div className="p-3 rounded bg-slate-900/60 border border-slate-800 print:bg-gray-100 print:border-gray-300">
                <span className="text-slate-400 print:text-gray-600 block">Red Findings:</span>
                <span className="text-lg font-bold text-red-400 print:text-red-700">{report.battle.red_discoveries}</span>
              </div>
              <div className="p-3 rounded bg-slate-900/60 border border-slate-800 print:bg-gray-100 print:border-gray-300">
                <span className="text-slate-400 print:text-gray-600 block">Blue Patches Verified:</span>
                <span className="text-lg font-bold text-blue-400 print:text-blue-700">{report.battle.blue_patches_approved}</span>
              </div>
              <div className="p-3 rounded bg-slate-900/60 border border-slate-800 print:bg-gray-100 print:border-gray-300">
                <span className="text-slate-400 print:text-gray-600 block">Open Findings:</span>
                <span className="text-lg font-bold text-emerald-400 print:text-emerald-700">
                  {report.findings.filter((f) => f.status === 'Open').length}
                </span>
              </div>
            </div>
          </div>

          {/* Compliance Footer */}
          <div className="border-t border-slate-800 pt-4 flex flex-col sm:flex-row justify-between text-[11px] font-mono text-slate-500 print:text-gray-500">
            <span>Deterministic Pytest Harness • Local Isolated Sandbox</span>
            <span>Derived from the recorded event log</span>
          </div>
        </div>
      )}
    </div>
  );
};

function roundNumber(n: number) {
  return Math.round(n * 10) / 10;
}
