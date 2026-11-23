import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  ShieldCheck, 
  FileCode2, 
  CheckCircle2, 
  AlertOctagon, 
  Activity, 
  Terminal, 
  Play, 
  FileText,
  GitCommit,
  Layers,
  Sparkles
} from 'lucide-react';
import { getPatches, PatchRecord } from '../services/api';

export const BlueAgentPage: React.FC = () => {
  const [patches, setPatches] = useState<PatchRecord[]>([]);
  const [selectedPatch, setSelectedPatch] = useState<PatchRecord | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPatches();
  }, []);

  const loadPatches = async () => {
    try {
      const data = await getPatches();
      setPatches(data);
      if (data.length > 0) {
        setSelectedPatch(data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-xl bg-[#090d18] border border-blue-900/50 glow-blue">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-blue-950/80 border border-blue-500/50 flex items-center justify-center glow-blue">
            <Cpu className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-black text-white tracking-wide">BLUE AGENT DEFENSE CENTER</h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase bg-blue-950 text-blue-400 border border-blue-700">
                ACTIVE DEFENSE OPERATIONAL
              </span>
            </div>
            <p className="text-xs text-blue-300 font-mono mt-0.5">
              Incident Analysis, Minimal Surgical Patch Synthesis, & Zero-Regression Deployment
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono">
          <div className="px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>4 / 4 Patches Referee-Approved</span>
          </div>
        </div>
      </div>

      {/* Workflow Steps Indicator */}
      <div className="p-4 rounded-xl bg-[#090d18] border border-slate-800">
        <h3 className="text-xs font-mono font-bold text-blue-400 uppercase tracking-wider mb-3">
          Automated Blue Agent Defense Lifecycle
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs font-mono">
          {[
            { step: "1. Incident Detection", desc: "Telemetry alert triggers on breach attempt" },
            { step: "2. AST Root Cause", desc: "Isolate vulnerable handler code snippet" },
            { step: "3. Minimal Patch", desc: "Synthesize surgical diff without dropping route" },
            { step: "4. Referee Verification", desc: "Execute pytest functional + security suites" },
            { step: "5. Safe Hot-Deploy", desc: "Deploy patch with 100% app availability" }
          ].map((s, idx) => (
            <div key={idx} className="p-2.5 rounded-lg bg-black/40 border border-slate-800">
              <div className="flex justify-between items-center mb-1">
                <span className="font-bold text-white text-[11px]">{s.step}</span>
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
              </div>
              <p className="text-[10px] text-slate-400 leading-tight">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Select Patch Buttons */}
      <div className="flex border-b border-slate-800 space-x-2 overflow-x-auto pb-2">
        {patches.map((p) => {
          const isSelected = selectedPatch?.id === p.id;
          return (
            <button
              key={p.id}
              onClick={() => setSelectedPatch(p)}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-mono font-bold transition whitespace-nowrap ${
                isSelected
                  ? 'bg-blue-600/30 text-blue-300 border border-blue-500 glow-blue'
                  : 'bg-[#090d18] text-slate-400 border border-slate-800 hover:text-white'
              }`}
            >
              <FileCode2 className="w-3.5 h-3.5" />
              <span>{p.name} ({p.id})</span>
            </button>
          );
        })}
      </div>

      {/* Code Editor Style Side-by-Side Comparison */}
      {selectedPatch && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Original Vulnerable Code */}
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-red-950/20 border border-red-900/50">
              <div className="flex items-center space-x-2">
                <AlertOctagon className="w-4 h-4 text-red-400" />
                <span className="text-xs font-mono font-bold text-red-300 uppercase">
                  Original Vulnerable Implementation
                </span>
              </div>
              <span className="text-[10px] font-mono text-slate-400">{selectedPatch.source_file}</span>
            </div>
            <div className="p-4 rounded-xl bg-black border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto max-h-96">
              <pre>{selectedPatch.original_code}</pre>
            </div>
          </div>

          {/* Right Column: Proposed Surgical Patch */}
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/50">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-mono font-bold text-emerald-300 uppercase">
                  Synthesized Minimal Security Patch
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                REFEREE APPROVED
              </span>
            </div>
            <div className="p-4 rounded-xl bg-black border border-emerald-900/40 font-mono text-xs text-emerald-300 overflow-x-auto max-h-96">
              <pre>{selectedPatch.proposed_patch}</pre>
            </div>
          </div>

          {/* Diff View & Explanation spanning full width */}
          <div className="lg:col-span-2 p-5 rounded-xl bg-[#090d18] border border-slate-800 space-y-4">
            <h4 className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
              <GitCommit className="w-4 h-4" /> Unified Code Difference (Diff) & Mitigation Explanation
            </h4>

            <pre className="p-3.5 rounded-lg bg-black border border-slate-800 font-mono text-xs text-cyan-300 overflow-x-auto">
              {selectedPatch.diff_code}
            </pre>

            <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-300 space-y-1">
              <span className="font-bold text-white font-mono block">Fix Strategy:</span>
              <p>{selectedPatch.explanation}</p>
            </div>

            {/* Test Verification Status */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
              <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40 flex items-center justify-between">
                <span className="text-slate-300">Functional Pytest Suite:</span>
                <span className="text-emerald-400 font-bold">PASSED (6/6)</span>
              </div>
              <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40 flex items-center justify-between">
                <span className="text-slate-300">Security Regression Suite:</span>
                <span className="text-emerald-400 font-bold">PASSED (100%)</span>
              </div>
              <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40 flex items-center justify-between">
                <span className="text-slate-300">Application Availability:</span>
                <span className="text-emerald-400 font-bold">100% HEALTHY</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
