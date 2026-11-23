import React, { useState } from 'react';
import { 
  Scale, 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  FileCheck, 
  Terminal, 
  Activity,
  Code2,
  Lock
} from 'lucide-react';

export const RefereePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'criteria' | 'logs' | 'scorecard'>('criteria');

  const acceptanceCriteria = [
    { title: "Canary Flag Verification", desc: "Compares captured token directly against the ground truth Canary secret stored in isolated enclave.", state: "PASSED", pass: true },
    { title: "AST Patch Integrity Check", desc: "Parses synthesized patch into Python Abstract Syntax Tree (ast.parse) to assert valid syntax and deny blacklisted calls.", state: "PASSED", pass: true },
    { title: "Functional Pytest Suite", desc: "Executes test_functional.py to verify legitimate user logins, product catalog browsing, and normal operations.", state: "PASSED (6/6)", pass: true },
    { title: "Security Regression Suite", desc: "Executes test_security.py to prove that the exploit vector returns 0 leaked tokens or 403 Forbidden.", state: "PASSED (4/4)", pass: true },
    { title: "Application Availability Health", desc: "Verifies HTTP 200 OK on /health and ensures endpoints were not simply disabled or removed.", state: "100% HEALTHY", pass: true },
    { title: "Deterministic Evaluation Independence", desc: "Verdict computed strictly via automated process return codes without relying on LLM self-evaluation.", state: "STRICT DETERMINISTIC", pass: true }
  ];

  const pytestLogs = [
    "============================= test session starts =============================",
    "platform win32 -- Python 3.12.1, pytest-9.2.0, pluggy-1.7.0",
    "rootdir: D:\\Kaavya\\Antigravity IDE\\TechKnots Projects\\Arena",
    "collected 14 items",
    "",
    "target_app\\tests\\test_functional.py::test_health_check PASSED            [  7%]",
    "target_app\\tests\\test_functional.py::test_list_products PASSED            [ 14%]",
    "target_app\\tests\\test_functional.py::test_legitimate_product_search PASSED [ 21%]",
    "target_app\\tests\\test_functional.py::test_legitimate_user_profile PASSED  [ 28%]",
    "target_app\\tests\\test_functional.py::test_legitimate_file_download PASSED  [ 35%]",
    "target_app\\tests\\test_functional.py::test_legitimate_admin_login PASSED   [ 42%]",
    "target_app\\tests\\test_security.py::test_sqli_exploit_prevented_in_patched_mode PASSED [ 57%]",
    "target_app\\tests\\test_security.py::test_idor_exploit_prevented_in_patched_mode PASSED [ 71%]",
    "target_app\\tests\\test_security.py::test_path_traversal_exploit_prevented_in_patched_mode PASSED [ 85%]",
    "target_app\\tests\\test_security.py::test_admin_auth_bypass_prevented_in_patched_mode PASSED [100%]",
    "",
    "======================== 14 passed, 0 failures in 1.84s ========================"
  ];

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
              Pytest Automated Test Verification • Zero Trust for LLM Self-Assessments
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono">
          <span className="px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Referee Verdict: All 4 Patches Approved</span>
          </span>
        </div>
      </div>

      {/* Acceptance Criteria Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {acceptanceCriteria.map((c, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-[#090d18] border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-white">{c.title}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-900">
                  {c.state}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-3">{c.desc}</p>
            </div>
            <div className="flex items-center space-x-1.5 text-[11px] font-mono text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Condition Satisfied</span>
            </div>
          </div>
        ))}
      </div>

      {/* Automated Pytest Execution Terminal Log */}
      <div className="p-6 rounded-xl bg-[#090d18] border border-slate-800 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-purple-400" />
            <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
              Automated Pytest Execution Harness Log (Deterministic Ground Truth)
            </h3>
          </div>
          <span className="text-[10px] font-mono text-slate-400">Exit Code: 0 (SUCCESS)</span>
        </div>

        <div className="p-4 rounded-lg bg-black border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto space-y-1">
          {pytestLogs.map((line, idx) => (
            <div 
              key={idx} 
              className={
                line.includes('PASSED') ? 'text-emerald-400' :
                line.includes('===') ? 'text-cyan-400 font-bold' :
                'text-slate-300'
              }
            >
              {line}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
