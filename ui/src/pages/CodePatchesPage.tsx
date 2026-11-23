import React, { useState, useEffect } from 'react';
import { 
  FileCode2, 
  GitCommit, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  RotateCcw, 
  FileText, 
  Layers, 
  ShieldCheck,
  Terminal,
  Code
} from 'lucide-react';
import { getPatches, PatchRecord } from '../services/api';

export const CodePatchesPage: React.FC = () => {
  const [patches, setPatches] = useState<PatchRecord[]>([]);
  const [selectedPatch, setSelectedPatch] = useState<PatchRecord | null>(null);
  const [activeFileView, setActiveFileView] = useState<'diff' | 'vulnerable' | 'secure'>('diff');

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
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-xl bg-[#090d18] border border-cyan-900/50">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <FileCode2 className="w-6 h-6 text-cyan-400" />
            <h1 className="text-xl font-black text-white tracking-wide">SOURCE CODE & PATCH HISTORY</h1>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            Audit trail of referee-verified patches replayed from the recorded match log
          </p>
        </div>
      </div>

      {/* Grid: Patch History List & Code Diff Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Patch List (4 cols) */}
        <div className="lg:col-span-4 space-y-3">
          <h3 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
            Synthesized Patches ({patches.length})
          </h3>
          <div className="space-y-2">
            {patches.map((p) => {
              const isSelected = selectedPatch?.id === p.id;
              return (
                <div
                  key={p.id}
                  onClick={() => setSelectedPatch(p)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition ${
                    isSelected
                      ? 'bg-blue-950/40 border-blue-500 glow-blue/20'
                      : 'bg-[#090d18] border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-mono font-bold text-white">{p.id}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                      APPROVED
                    </span>
                  </div>
                  <div className="text-xs font-bold text-slate-200 mb-1">{p.name}</div>
                  <div className="text-[10px] font-mono text-slate-400 truncate">{p.source_file}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Code Viewer (8 cols) */}
        {selectedPatch && (
          <div className="lg:col-span-8 p-6 rounded-xl bg-[#090d18] border border-slate-800 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">{selectedPatch.name}</h3>
                <span className="text-xs font-mono text-cyan-400">{selectedPatch.source_file}</span>
              </div>

              {/* View Selector */}
              <div className="flex items-center p-1 bg-black rounded-lg border border-slate-800 text-xs font-mono">
                <button
                  onClick={() => setActiveFileView('diff')}
                  className={`px-3 py-1 rounded transition ${
                    activeFileView === 'diff' ? 'bg-cyan-900/60 text-cyan-300 font-bold' : 'text-slate-400'
                  }`}
                >
                  Unified Diff
                </button>
                <button
                  onClick={() => setActiveFileView('vulnerable')}
                  className={`px-3 py-1 rounded transition ${
                    activeFileView === 'vulnerable' ? 'bg-red-900/60 text-red-300 font-bold' : 'text-slate-400'
                  }`}
                >
                  Vulnerable
                </button>
                <button
                  onClick={() => setActiveFileView('secure')}
                  className={`px-3 py-1 rounded transition ${
                    activeFileView === 'secure' ? 'bg-emerald-900/60 text-emerald-300 font-bold' : 'text-slate-400'
                  }`}
                >
                  Secure
                </button>
              </div>
            </div>

            {/* Code Body */}
            <div className="p-4 rounded-xl bg-black border border-slate-800 font-mono text-xs overflow-x-auto max-h-[450px]">
              {activeFileView === 'diff' && (
                <pre className="text-cyan-300 whitespace-pre leading-relaxed">{selectedPatch.diff_code}</pre>
              )}
              {activeFileView === 'vulnerable' && (
                <pre className="text-red-300 whitespace-pre leading-relaxed">{selectedPatch.original_code}</pre>
              )}
              {activeFileView === 'secure' && (
                <pre className="text-emerald-300 whitespace-pre leading-relaxed">{selectedPatch.proposed_patch}</pre>
              )}
            </div>

            {/* Patch Verification Proof */}
            <div className="p-4 rounded-lg bg-black/40 border border-slate-800 space-y-2 text-xs font-mono">
              <div className="flex justify-between items-center text-slate-300">
                <span>Referee Evaluation Verdict:</span>
                <span className="text-emerald-400 font-bold">{selectedPatch.referee_notes}</span>
              </div>
              <div className="text-[11px] text-slate-400">
                Patch source: {selectedPatch.explanation}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
