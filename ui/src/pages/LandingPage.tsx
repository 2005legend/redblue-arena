import React from 'react';
import { 
  ShieldAlert, 
  Terminal, 
  Cpu, 
  Scale, 
  Swords, 
  Play, 
  ArrowRight, 
  CheckCircle2, 
  Zap, 
  Lock, 
  Server, 
  Code2, 
  Database, 
  Layers,
  Sparkles
} from 'lucide-react';

interface LandingPageProps {
  onStartBattle: () => void;
  onExploreArena: () => void;
  setCurrentPage: (page: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onStartBattle,
  onExploreArena,
  setCurrentPage
}) => {
  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-16 border-b border-cyan-950/60 cyber-grid">
        <div className="max-w-6xl mx-auto px-4 text-center">
          {/* Badge */}
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 text-xs font-mono mb-6 glow-cyan">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Autonomous Red vs. Blue Cybersecurity Simulation</span>
          </div>

          <h1 className="text-5xl sm:text-6xl md:text-7xl font-black tracking-tight text-white mb-4">
            <span className="bg-gradient-to-r from-red-500 via-cyan-400 to-blue-500 bg-clip-text text-transparent">
              ARENA
            </span>
          </h1>

          <p className="text-xl sm:text-2xl font-medium text-slate-200 max-w-3xl mx-auto mb-4 tracking-wide">
            Where Autonomous AI Agents Battle to Secure the Future.
          </p>

          <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto mb-3 leading-relaxed font-normal">
            An autonomous cybersecurity simulation environment where AI-powered attackers discover vulnerabilities and defenders generate verified security patches in real time.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-2 mb-8 text-[11px] font-mono">
            <span className="px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800 text-emerald-300">
              Tier 1: deterministic sweep + patch cache (0 tokens)
            </span>
            <span className="px-2.5 py-1 rounded-full bg-cyan-950/60 border border-cyan-800 text-cyan-300">
              Tier 2: LLM agents on cache miss / --explore
            </span>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={onStartBattle}
              className="w-full sm:w-auto flex items-center justify-center space-x-2.5 px-6 py-3.5 rounded-xl font-bold text-sm bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-xl glow-cyan transition transform active:scale-95"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Start Battle</span>
            </button>
            <button
              onClick={onExploreArena}
              className="w-full sm:w-auto flex items-center justify-center space-x-2.5 px-6 py-3.5 rounded-xl font-semibold text-sm bg-slate-900/90 border border-slate-700 hover:border-cyan-500/60 text-slate-200 hover:text-white transition"
            >
              <Swords className="w-4 h-4 text-cyan-400" />
              <span>Explore Arena</span>
            </button>
          </div>
        </div>

        {/* Animated Red vs. Blue Battle Illustration */}
        <div className="max-w-5xl mx-auto mt-12 px-4">
          <div className="relative rounded-2xl p-6 bg-[#090d18] border border-cyan-900/50 shadow-2xl overflow-hidden glow-cyan">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-6">
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 rounded-full bg-red-500"></span>
                <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                <span className="text-xs font-mono text-slate-400 ml-2">ARENA SOC SIMULATION MONITOR</span>
              </div>
              <div className="flex items-center space-x-2 text-xs font-mono text-cyan-400">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                <span>SANDBOX ENGAGED</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
              {/* Red Agent Card */}
              <div className="p-5 rounded-xl bg-gradient-to-br from-red-950/40 to-slate-900/80 border border-red-500/40 glow-red">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <Terminal className="w-5 h-5 text-red-400" />
                    <span className="text-sm font-bold text-red-300">RED AGENT</span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-800">
                    ATTACKER
                  </span>
                </div>
                <p className="text-xs text-slate-300 mb-3">
                  Autonomously parses OpenAPI schemas, probes test vectors, and breaches seeded canary flag vaults.
                </p>
                <div className="p-2.5 rounded bg-black/60 font-mono text-[11px] text-red-400 space-y-1">
                  <div>&gt; GET /api/search?q=</div>
                  <div className="text-slate-400">&gt; Payload: ' OR 1=1--</div>
                  <div className="text-emerald-400">&gt; Flag: FLAG&#123;sqli_leaked_db&#125;</div>
                </div>
              </div>

              {/* Referee Center */}
              <div className="flex flex-col items-center text-center p-4 rounded-xl bg-purple-950/20 border border-purple-500/30 glow-purple">
                <div className="w-12 h-12 rounded-full bg-purple-500/20 border border-purple-500/50 flex items-center justify-center mb-2">
                  <Scale className="w-6 h-6 text-purple-400" />
                </div>
                <span className="text-xs font-bold text-purple-300 uppercase tracking-wider mb-1">
                  Deterministic Referee
                </span>
                <p className="text-[11px] text-slate-400 mb-2">
                  Independent Pytest Validation & Flag Ground Truth
                </p>
                <div className="w-full flex items-center justify-center gap-2 py-1 bg-purple-950/60 rounded border border-purple-800 text-[10px] font-mono text-purple-300">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  <span>Functional suite + exploit replay</span>
                </div>
              </div>

              {/* Blue Agent Card */}
              <div className="p-5 rounded-xl bg-gradient-to-br from-blue-950/40 to-slate-900/80 border border-blue-500/40 glow-blue">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <Cpu className="w-5 h-5 text-blue-400" />
                    <span className="text-sm font-bold text-blue-300">BLUE AGENT</span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
                    DEFENDER
                  </span>
                </div>
                <p className="text-xs text-slate-300 mb-3">
                  Captures telemetry alerts, isolates root causes, synthesizes surgical code diffs, and deploys verified patches.
                </p>
                <div className="p-2.5 rounded bg-black/60 font-mono text-[11px] text-blue-400 space-y-1">
                  <div>&gt; Incident: SQLi on /api/search</div>
                  <div className="text-slate-400">&gt; Diff: ... LIKE ?", (q,)</div>
                  <div className="text-emerald-400">&gt; Referee Status: VERIFIED</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-black text-white tracking-wide mb-2">HOW IT WORKS</h2>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">
            A continuous closed-loop cycle of autonomous exploit generation, surgical patching, and strict deterministic judging.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              step: "01",
              title: "Surface Discovery",
              desc: "Red Agent queries /openapi.json to discover endpoints and formulate bounded educational test payloads.",
              icon: Terminal,
              color: "text-red-400",
              borderColor: "border-red-500/30"
            },
            {
              step: "02",
              title: "Canary Breach",
              desc: "Attacker triggers seeded vulnerability to extract isolated Canary flag token and reports to Referee.",
              icon: Zap,
              color: "text-yellow-400",
              borderColor: "border-yellow-500/30"
            },
            {
              step: "03",
              title: "Surgical Patching",
              desc: "Blue Agent inspects affected source code and generates minimal code diff without removing functionality.",
              icon: Cpu,
              color: "text-blue-400",
              borderColor: "border-blue-500/30"
            },
            {
              step: "04",
              title: "Deterministic Verdict",
              desc: "The Referee executes automated pytest suites. The patch is approved only if functional and security tests pass.",
              icon: Scale,
              color: "text-purple-400",
              borderColor: "border-purple-500/30"
            }
          ].map((item, i) => {
            const Icon = item.icon;
            return (
              <div key={i} className={`p-6 rounded-xl bg-[#090d18] border ${item.borderColor} relative group hover:border-cyan-500/60 transition`}>
                <span className="text-3xl font-black font-mono text-slate-800 absolute top-4 right-4 group-hover:text-cyan-900/60 transition">
                  {item.step}
                </span>
                <div className="w-10 h-10 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center mb-4">
                  <Icon className={`w-5 h-5 ${item.color}`} />
                </div>
                <h3 className="text-base font-bold text-white mb-2">{item.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Four Vulnerability Categories */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-10">
          <h2 className="text-2xl sm:text-3xl font-black text-white tracking-wide mb-2">
            FOUR SEEDED VULNERABILITY CATEGORIES
          </h2>
          <p className="text-sm text-slate-400">
            Isolated educational test scenarios mapped to OWASP Top 10 and CWE classifications.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            {
              id: "sqli",
              name: "SQL Injection (SQLi)",
              endpoint: "GET /api/search?q=...",
              cwe: "CWE-89",
              desc: "The search term is interpolated into a LIKE query, so ' OR 1=1-- defeats the hidden = 0 filter and returns FLAG{sqli_leaked_db}.",
              mitigation: "Bind the term as a parameter: LIKE ? with ('%' + q + '%',)."
            },
            {
              id: "idor",
              name: "Insecure Direct Object Reference (IDOR)",
              endpoint: "GET /api/invoices/{invoice_id}",
              cwe: "CWE-639",
              desc: "The invoice is fetched by ID without checking owner_id, so any logged-in user can read another customer's note (FLAG{idor_invoice_leak}).",
              mitigation: "Add AND owner_id = ? using the authenticated user's id."
            },
            {
              id: "path_traversal",
              name: "Path Traversal",
              endpoint: "GET /api/files?name=...",
              cwe: "CWE-22",
              desc: "The requested name is joined to files/ without canonical checks, so ../secret.txt returns FLAG{path_traversal_leak}.",
              mitigation: "Resolve the path and reject anything outside the files/ root."
            },
            {
              id: "admin_auth",
              name: "Broken Admin Authorization",
              endpoint: "GET /api/admin/export",
              cwe: "CWE-862",
              desc: "The export checks that a session exists but never that its role is admin, so a normal user receives the users table and config note FLAG{admin_export_bypass}.",
              mitigation: "Require user['role'] == 'admin' after resolving the session."
            }
          ].map((v, i) => (
            <div key={i} className="p-6 rounded-xl bg-[#090d18] border border-slate-800 hover:border-cyan-500/50 transition glow-cyan/10">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-base font-bold text-white">{v.name}</h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                  {v.cwe}
                </span>
              </div>
              <p className="text-xs font-mono text-cyan-400 mb-2">{v.endpoint}</p>
              <p className="text-xs text-slate-300 mb-3">{v.desc}</p>
              <div className="text-[11px] font-mono text-emerald-400 bg-emerald-950/30 p-2 rounded border border-emerald-900/40">
                Fix: {v.mitigation}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Technology Stack & System Architecture */}
      <section className="max-w-6xl mx-auto px-4">
        <div className="p-8 rounded-2xl bg-[#090d18] border border-cyan-900/60 shadow-xl">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="text-2xl font-black text-white tracking-wide mb-4">
                HIGH-INTEGRITY ARCHITECTURE
              </h2>
              <p className="text-xs text-slate-300 leading-relaxed mb-6">
                ARENA enforces strict boundary separation between agents, target application, and the evaluation referee.
                Agents cannot alter testing criteria or forge referee decisions. All verification occurs via independent Pytest processes.
              </p>

              <div className="space-y-3">
                {[
                  { label: "Frontend", val: "React 19 + TypeScript + Vite + Tailwind CSS" },
                  { label: "Backend Orchestrator", val: "FastAPI + WebSockets + JSONL event log + Pytest harness" },
                  { label: "Target Application", val: "Isolated FastAPI sandbox with seeded synthetic data" },
                  { label: "Referee Evaluation", val: "Pytest functional suite + exploit replay, exit-code based" }
                ].map((item, idx) => (
                  <div key={idx} className="flex items-start space-x-2 text-xs">
                    <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-white">{item.label}: </span>
                      <span className="text-slate-400 font-mono text-[11px]">{item.val}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-5 rounded-xl bg-black/60 border border-slate-800 font-mono text-xs text-slate-300 space-y-3">
              <div className="text-cyan-400 font-bold border-b border-slate-800 pb-2">
                SYSTEM EXECUTION PIPELINE
              </div>
              <div className="space-y-1.5 text-[11px]">
                <div className="text-red-400">1. RED: template sweep on /api/search returns FLAG&#123;sqli_leaked_db&#125;</div>
                <div className="text-purple-400">2. REFEREE: functional suite passes on the untouched target</div>
                <div className="text-blue-400">3. BLUE: rewrites the LIKE clause to a bound parameter</div>
                <div className="text-purple-400">4. REFEREE: functional + exploit replay both pass</div>
                <div className="text-emerald-400">5. ARENA: records the verdict to the event log and exports the patch</div>
              </div>
              <div className="pt-2 border-t border-slate-800 flex justify-between items-center text-[10px] text-slate-500">
                <span>LOCAL SANDBOX ONLY</span>
                <span>SYNTHETIC ENCLAVE</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
