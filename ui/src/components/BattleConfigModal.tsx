import React, { useState } from 'react';
import { 
  X, 
  Swords, 
  ShieldCheck, 
  Sliders, 
  Terminal, 
  Cpu, 
  Layers, 
  Settings2, 
  CheckSquare, 
  Clock, 
  Radio, 
  Play, 
  Save 
} from 'lucide-react';

interface BattleConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartBattle: (config: any) => Promise<void>;
}

export const BattleConfigModal: React.FC<BattleConfigModalProps> = ({
  isOpen,
  onClose,
  onStartBattle
}) => {
  // 16 Interactive Fields State
  const [name, setName] = useState("Operation Cyber-Grid Alpha");
  const [description, setDescription] = useState("Full-matrix autonomous Red vs. Blue verification inside local sandbox");
  const [targetApp, setTargetApp] = useState("ARENA Vulnerable Web Target v2.4 (FastAPI + SQLite)");
  const [targetEnvironment, setTargetEnvironment] = useState("Local Sandbox (Process Isolated)");
  const [redModel, setRedModel] = useState("Gemini 3.8 Flash (High)");
  const [blueModel, setBlueModel] = useState("Gemini 3.8 Flash (High)");
  const [simulationMode, setSimulationMode] = useState("autonomous");
  const [vulns, setVulns] = useState<string[]>(["sqli", "idor", "path_traversal", "admin_auth"]);
  const [maxExecutionTime, setMaxExecutionTime] = useState(120);
  const [maxTestRequests, setMaxTestRequests] = useState(50);
  const [patchValidationMode, setPatchValidationMode] = useState("strict_pytest");
  const [functionalTestSuite, setFunctionalTestSuite] = useState("target_app/tests/test_functional.py");
  const [securityTestSuite, setSecurityTestSuite] = useState("target_app/tests/test_security.py");
  const [autoDeployPatch, setAutoDeployPatch] = useState(true);
  const [enableLiveMonitoring, setEnableLiveMonitoring] = useState(true);
  const [saveConfiguration, setSaveConfiguration] = useState(true);

  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const toggleVuln = (vId: string) => {
    if (vulns.includes(vId)) {
      setVulns(vulns.filter(id => id !== vId));
    } else {
      setVulns([...vulns, vId]);
    }
  };

  const selectAllVulns = () => {
    if (vulns.length === 4) {
      setVulns([]);
    } else {
      setVulns(["sqli", "idor", "path_traversal", "admin_auth"]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (vulns.length === 0) {
      alert("Please select at least one vulnerability scenario for testing.");
      return;
    }
    setLoading(true);
    try {
      await onStartBattle({
        name,
        description,
        target_app: targetApp,
        target_environment: targetEnvironment,
        red_model: redModel,
        blue_model: blueModel,
        simulation_mode: simulationMode,
        vulnerabilities: vulns,
        max_execution_time: maxExecutionTime,
        max_test_requests: maxTestRequests,
        patch_validation_mode: patchValidationMode,
        functional_test_suite: functionalTestSuite,
        security_test_suite: securityTestSuite,
        auto_deploy_patch: autoDeployPatch,
        enable_live_monitoring: enableLiveMonitoring,
        save_configuration: saveConfiguration
      });
      onClose();
    } catch (err: any) {
      alert(err.message || "Failed to initialize battle.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-[#0a0e19] border border-cyan-500/40 rounded-xl shadow-2xl overflow-hidden my-8 glow-cyan">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-[#0d1322] border-b border-cyan-900/50">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center">
              <Swords className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-wide">Battle Configuration</h2>
              <p className="text-xs text-cyan-400/80 font-mono">16 Interactive Cyber Simulation Controls</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {/* Section 1: Core Parameters */}
          <div>
            <h3 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Settings2 className="w-3.5 h-3.5" /> 1. Mission & Environment Identification
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Field 1: Battle Name */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">1. Battle Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-[#070a13] border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-400 font-mono"
                />
              </div>

              {/* Field 2: Description */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">2. Battle Description</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-[#070a13] border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-400 font-mono"
                />
              </div>

              {/* Field 3: Target Application */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">3. Target Application</label>
                <select
                  value={targetApp}
                  onChange={(e) => setTargetApp(e.target.value)}
                  className="w-full px-3 py-2 bg-[#070a13] border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-400 font-mono"
                >
                  <option value="ARENA Vulnerable Web Target v2.4 (FastAPI + SQLite)">ARENA Target App v2.4 (FastAPI + SQLite)</option>
                  <option value="ARENA E-Commerce Secure Reference Mock">ARENA E-Commerce Secure Mock</option>
                  <option value="Custom Isolated API Mock">Custom Isolated API Mock</option>
                </select>
              </div>

              {/* Field 4: Target Environment */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">4. Target Environment</label>
                <select
                  value={targetEnvironment}
                  onChange={(e) => setTargetEnvironment(e.target.value)}
                  className="w-full px-3 py-2 bg-[#070a13] border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-cyan-400 font-mono"
                >
                  <option value="Local Sandbox (Process Isolated)">Local Sandbox (Process Isolated)</option>
                  <option value="Docker Container (Container Isolated)">Docker Container (Container Isolated)</option>
                  <option value="In-Memory Microservice Sandbox">In-Memory Microservice Sandbox</option>
                </select>
              </div>
            </div>
          </div>

          {/* Section 2: Agent Architecture */}
          <div className="pt-2 border-t border-slate-800">
            <h3 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5" /> 2. AI Agent Models & Simulation Logic
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Field 5: Red Model */}
              <div>
                <label className="block text-xs font-medium text-red-300 mb-1 flex items-center gap-1">
                  <Terminal className="w-3 h-3 text-red-400" /> 5. Red Agent Model
                </label>
                <select
                  value={redModel}
                  onChange={(e) => setRedModel(e.target.value)}
                  className="w-full px-3 py-2 bg-[#070a13] border border-red-900/50 rounded-lg text-xs text-white focus:outline-none focus:border-red-400 font-mono"
                >
                  <option value="Gemini 3.8 Flash (High)">Gemini 3.8 Flash (High)</option>
                  <option value="Claude 3.7 Sonnet">Claude 3.7 Sonnet</option>
                  <option value="GPT-4o Security Special">GPT-4o Security Special</option>
                  <option value="Deterministic Autonomous Fuzzer">Deterministic Autonomous Fuzzer</option>
                </select>
              </div>

              {/* Field 6: Blue Model */}
              <div>
                <label className="block text-xs font-medium text-blue-300 mb-1 flex items-center gap-1">
                  <Cpu className="w-3 h-3 text-blue-400" /> 6. Blue Agent Model
                </label>
                <select
                  value={blueModel}
                  onChange={(e) => setBlueModel(e.target.value)}
                  className="w-full px-3 py-2 bg-[#070a13] border border-blue-900/50 rounded-lg text-xs text-white focus:outline-none focus:border-blue-400 font-mono"
                >
                  <option value="Gemini 3.8 Flash (High)">Gemini 3.8 Flash (High)</option>
                  <option value="Claude 3.7 Sonnet">Claude 3.7 Sonnet</option>
                  <option value="DeepSeek R1 Cyber-Synthesizer">DeepSeek R1 Cyber-Synthesizer</option>
                  <option value="Deterministic Surgical Patcher">Deterministic Surgical Patcher</option>
                </select>
              </div>

              {/* Field 7: Simulation Mode */}
              <div>
                <label className="block text-xs font-medium text-purple-300 mb-1 flex items-center gap-1">
                  <Sliders className="w-3 h-3 text-purple-400" /> 7. Simulation Mode
                </label>
                <select
                  value={simulationMode}
                  onChange={(e) => setSimulationMode(e.target.value)}
                  className="w-full px-3 py-2 bg-[#070a13] border border-purple-900/50 rounded-lg text-xs text-white focus:outline-none focus:border-purple-400 font-mono"
                >
                  <option value="autonomous">Autonomous Continuous Battle</option>
                  <option value="step-by-step">Step-by-Step Interactive</option>
                  <option value="verification-only">Verification Test Only</option>
                </select>
              </div>
            </div>
          </div>

          {/* Section 3: Vulnerabilities Selection (Field 8) */}
          <div className="pt-2 border-t border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                <CheckSquare className="w-3.5 h-3.5" /> 8. Vulnerability Scenarios Selection
              </h3>
              <button
                type="button"
                onClick={selectAllVulns}
                className="text-[11px] font-mono text-cyan-400 hover:text-cyan-300 underline"
              >
                {vulns.length === 4 ? "Deselect All" : "Select All 4"}
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { id: "sqli", name: "SQL Injection", desc: "/api/products/search", badge: "Critical" },
                { id: "idor", name: "IDOR", desc: "/api/orders/{id}", badge: "High" },
                { id: "path_traversal", name: "Path Traversal", desc: "/api/files/download", badge: "High" },
                { id: "admin_auth", name: "Broken Admin Auth", desc: "/api/admin/dashboard", badge: "Critical" },
              ].map((v) => {
                const isSelected = vulns.includes(v.id);
                return (
                  <div
                    key={v.id}
                    onClick={() => toggleVuln(v.id)}
                    className={`cursor-pointer p-3 rounded-lg border transition-all ${
                      isSelected
                        ? "bg-cyan-950/40 border-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.2)]"
                        : "bg-[#070a13] border-slate-800 hover:border-slate-700 opacity-60"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-white">{v.name}</span>
                      <span className={`text-[10px] font-mono px-1 rounded ${
                        v.badge === "Critical" ? "bg-red-950 text-red-400" : "bg-orange-950 text-orange-400"
                      }`}>{v.badge}</span>
                    </div>
                    <p className="text-[10px] font-mono text-slate-400">{v.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Section 4: Execution Limits & Tests */}
          <div className="pt-2 border-t border-slate-800">
            <h3 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" /> 3. Execution Constraints & Pytest Test Suites
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Field 9: Max Execution Time */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  9. Max Execution Time ({maxExecutionTime}s)
                </label>
                <input
                  type="range"
                  min="30"
                  max="300"
                  step="15"
                  value={maxExecutionTime}
                  onChange={(e) => setMaxExecutionTime(Number(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>

              {/* Field 10: Max Test Requests */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">10. Max Test Requests</label>
                <input
                  type="number"
                  min="10"
                  max="200"
                  value={maxTestRequests}
                  onChange={(e) => setMaxTestRequests(Number(e.target.value))}
                  className="w-full px-3 py-1.5 bg-[#070a13] border border-slate-700 rounded-lg text-xs text-white font-mono"
                />
              </div>

              {/* Field 11: Patch Validation Mode */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">11. Patch Validation Mode</label>
                <select
                  value={patchValidationMode}
                  onChange={(e) => setPatchValidationMode(e.target.value)}
                  className="w-full px-3 py-1.5 bg-[#070a13] border border-slate-700 rounded-lg text-xs text-white font-mono"
                >
                  <option value="strict_pytest">Strict Pytest (Functional + Security)</option>
                  <option value="ast_and_tests">AST Parsing + Pytest Harness</option>
                  <option value="dry_run">Dry Run Evaluation</option>
                </select>
              </div>

              {/* Field 12: Functional Test Suite */}
              <div className="md:col-span-1">
                <label className="block text-xs font-medium text-slate-300 mb-1">12. Functional Test Suite</label>
                <input
                  type="text"
                  value={functionalTestSuite}
                  onChange={(e) => setFunctionalTestSuite(e.target.value)}
                  className="w-full px-3 py-1.5 bg-[#070a13] border border-slate-700 rounded-lg text-xs text-slate-300 font-mono"
                />
              </div>

              {/* Field 13: Security Test Suite */}
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-slate-300 mb-1">13. Security Test Suite</label>
                <input
                  type="text"
                  value={securityTestSuite}
                  onChange={(e) => setSecurityTestSuite(e.target.value)}
                  className="w-full px-3 py-1.5 bg-[#070a13] border border-slate-700 rounded-lg text-xs text-slate-300 font-mono"
                />
              </div>
            </div>
          </div>

          {/* Section 5: Deployment & Monitoring Switches */}
          <div className="pt-2 border-t border-slate-800">
            <h3 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" /> 4. Deployment & Monitoring Automation
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Field 14: Auto Deploy */}
              <label className="flex items-center space-x-2.5 p-3 rounded-lg bg-[#070a13] border border-slate-800 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoDeployPatch}
                  onChange={(e) => setAutoDeployPatch(e.target.checked)}
                  className="w-4 h-4 accent-cyan-400"
                />
                <span className="text-xs text-slate-200">14. Auto-Deploy Verified Patch</span>
              </label>

              {/* Field 15: Live Monitoring */}
              <label className="flex items-center space-x-2.5 p-3 rounded-lg bg-[#070a13] border border-slate-800 cursor-pointer">
                <input
                  type="checkbox"
                  checked={enableLiveMonitoring}
                  onChange={(e) => setEnableLiveMonitoring(e.target.checked)}
                  className="w-4 h-4 accent-cyan-400"
                />
                <span className="text-xs text-slate-200">15. Enable Live Telemetry</span>
              </label>

              {/* Field 16: Save Configuration */}
              <label className="flex items-center space-x-2.5 p-3 rounded-lg bg-[#070a13] border border-slate-800 cursor-pointer">
                <input
                  type="checkbox"
                  checked={saveConfiguration}
                  onChange={(e) => setSaveConfiguration(e.target.checked)}
                  className="w-4 h-4 accent-cyan-400"
                />
                <span className="text-xs text-slate-200">16. Save Configuration</span>
              </label>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
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
              <span>{loading ? "Initializing Sandbox..." : "Launch Autonomous Battle"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
