import React, { useState, useEffect } from 'react';
import { 
  Layers, 
  Users, 
  ShoppingBag, 
  FileText, 
  ShieldCheck, 
  ShieldAlert, 
  Search, 
  FolderDown, 
  RefreshCw, 
  Check, 
  ToggleLeft, 
  ToggleRight, 
  Terminal, 
  Send,
  Lock,
  FileCode
} from 'lucide-react';
import { 
  getTargetConfig, 
  setTargetMode, 
  resetTargetApp,
  testTargetSearch,
  testTargetOrder,
  testTargetFile,
  testTargetAdmin
} from '../services/api';

export const TargetAppPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'users' | 'products' | 'orders' | 'admin' | 'files' | 'search' | 'console'>('products');
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  // Test Console State
  const [selectedVector, setSelectedVector] = useState<'sqli' | 'idor' | 'path_traversal' | 'admin_auth'>('sqli');
  const [customInput, setCustomInput] = useState("' UNION SELECT id, flag_key, flag_value, description, 0, 'active' FROM canary_flags --");
  const [consoleResult, setConsoleResult] = useState<any>(null);
  const [consoleLoading, setConsoleLoading] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await getTargetConfig();
      setConfig(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleGlobalToggle = async (mode: 'vulnerable' | 'secure') => {
    setLoading(true);
    try {
      await setTargetMode(mode);
      await loadConfig();
      setFeedback(`Target Application switched to ${mode.toUpperCase()} mode.`);
      setTimeout(() => setFeedback(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  const handlePatchToggle = async (patchId: string, currentStatus: boolean) => {
    setLoading(true);
    try {
      await setTargetMode(config?.global_mode || 'vulnerable', patchId, !currentStatus);
      await loadConfig();
      setFeedback(`Vulnerability [${patchId}] patch state updated.`);
      setTimeout(() => setFeedback(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!confirm("Reset target database and restore all vulnerabilities to clean state?")) return;
    setLoading(true);
    try {
      await resetTargetApp();
      await loadConfig();
      setFeedback("Target application database and patches reset to original vulnerable state.");
      setTimeout(() => setFeedback(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  const runLiveProbe = async () => {
    setConsoleLoading(true);
    try {
      if (selectedVector === 'sqli') {
        const res = await testTargetSearch(customInput);
        setConsoleResult(res);
      } else if (selectedVector === 'idor') {
        const orderId = parseInt(customInput, 10) || 5;
        const res = await testTargetOrder(orderId);
        setConsoleResult(res);
      } else if (selectedVector === 'path_traversal') {
        const res = await testTargetFile(customInput);
        setConsoleResult(res);
      } else if (selectedVector === 'admin_auth') {
        const res = await testTargetAdmin(customInput);
        setConsoleResult(res);
      }
    } catch (err: any) {
      setConsoleResult({ error: err.message });
    } finally {
      setConsoleLoading(false);
    }
  };

  const updateVectorSelection = (v: 'sqli' | 'idor' | 'path_traversal' | 'admin_auth') => {
    setSelectedVector(v);
    if (v === 'sqli') {
      setCustomInput("' UNION SELECT id, flag_key, flag_value, description, 0, 'active' FROM canary_flags --");
    } else if (v === 'idor') {
      setCustomInput("5");
    } else if (v === 'path_traversal') {
      setCustomInput("../canary_storage/canary_flag.txt");
    } else if (v === 'admin_auth') {
      setCustomInput("arena-debug-mode");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Title & Global Mode Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-xl bg-[#090d18] border border-cyan-900/60 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <Layers className="w-5 h-5 text-cyan-400" />
            <h1 className="text-xl font-black text-white tracking-wide">TARGET APPLICATION ENCLAVE</h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
              FASTAPI + SQLITE SANDBOX
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Isolated test environment seeded with 4 educational vulnerability scenarios and synthetic data
          </p>
        </div>

        {/* Global Switch Controls */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center p-1 bg-black/60 rounded-lg border border-slate-700">
            <button
              onClick={() => handleGlobalToggle('vulnerable')}
              disabled={loading}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-bold transition ${
                config?.global_mode === 'vulnerable'
                  ? 'bg-red-600/30 text-red-300 border border-red-500 glow-red'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              VULNERABLE MODE
            </button>
            <button
              onClick={() => handleGlobalToggle('secure')}
              disabled={loading}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-bold transition ${
                config?.global_mode === 'secure'
                  ? 'bg-emerald-600/30 text-emerald-300 border border-emerald-500 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              SECURE REFERENCE
            </button>
          </div>

          <button
            onClick={handleReset}
            title="Reset Database to initial vulnerable state"
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {feedback && (
        <div className="p-3 rounded-lg bg-cyan-950/60 border border-cyan-500/50 text-xs font-mono text-cyan-300 flex items-center gap-2">
          <Check className="w-4 h-4 text-emerald-400" />
          <span>{feedback}</span>
        </div>
      )}

      {/* Per-Vulnerability Patch Switch Bar */}
      <div className="p-4 rounded-xl bg-[#090d18] border border-slate-800">
        <h3 className="text-xs font-mono font-semibold text-cyan-400 uppercase tracking-wider mb-3">
          Granular Security Patch Switches
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { id: 'sqli', name: 'SQL Injection', ep: '/api/products/search' },
            { id: 'idor', name: 'IDOR', ep: '/api/orders/{id}' },
            { id: 'path_traversal', name: 'Path Traversal', ep: '/api/files/download' },
            { id: 'admin_auth', name: 'Admin Auth Bypass', ep: '/api/admin/dashboard' }
          ].map((item) => {
            const isPatched = config?.patches?.[item.id] ?? false;
            return (
              <div 
                key={item.id}
                onClick={() => handlePatchToggle(item.id, isPatched)}
                className={`p-3 rounded-lg border cursor-pointer flex items-center justify-between transition ${
                  isPatched
                    ? 'bg-emerald-950/30 border-emerald-600/50'
                    : 'bg-red-950/30 border-red-600/40'
                }`}
              >
                <div>
                  <span className="text-xs font-bold text-white block">{item.name}</span>
                  <span className="text-[10px] font-mono text-slate-400">{item.ep}</span>
                </div>
                <div className="text-right">
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                    isPatched ? 'bg-emerald-900/60 text-emerald-300' : 'bg-red-900/60 text-red-300'
                  }`}>
                    {isPatched ? 'PATCHED' : 'VULNERABLE'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Target Application Tabs */}
      <div className="flex border-b border-slate-800 space-x-2 overflow-x-auto">
        {[
          { id: 'products', label: 'B. Products', icon: ShoppingBag },
          { id: 'orders', label: 'C. Orders', icon: FileText },
          { id: 'admin', label: 'D. Admin Panel', icon: ShieldCheck },
          { id: 'files', label: 'E. Files', icon: FolderDown },
          { id: 'users', label: 'A. Users', icon: Users },
          { id: 'search', label: 'F. Search', icon: Search },
          { id: 'console', label: 'Interactive Exploit Probe', icon: Terminal, highlight: true }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-medium border-b-2 whitespace-nowrap transition ${
                isActive
                  ? tab.highlight 
                    ? 'border-cyan-400 text-cyan-300 font-bold bg-cyan-950/30'
                    : 'border-cyan-400 text-white font-bold bg-slate-900/50'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Contents */}
      <div className="p-6 rounded-xl bg-[#090d18] border border-slate-800">
        {/* Products Module (SQLi Seeded) */}
        {activeTab === 'products' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">Product Catalog & Inventory</h3>
                <p className="text-xs text-slate-400 font-mono">Endpoint: GET /api/products/search (Seeded with SQL Injection)</p>
              </div>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-900">
                SQLi Target Endpoint
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { name: "Quantum Key Distribution Module", price: "$24,999", stock: 5, cat: "Hardware" },
                { name: "Neural Firewall Appliance", price: "$8,500", stock: 12, cat: "Hardware" },
                { name: "Airgap Diode Transceiver", price: "$3,400", stock: 8, cat: "Hardware" },
                { name: "Sentinel Threat Intelligence Suite", price: "$1,200", stock: 50, cat: "Software" },
                { name: "Cryptographic Coprocessor HSM", price: "$6,200", stock: 15, cat: "Hardware" },
                { name: "Red Team Adversary Emulator", price: "$4,500", stock: 20, cat: "Software" }
              ].map((p, idx) => (
                <div key={idx} className="p-4 rounded-lg bg-black/40 border border-slate-800">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-bold text-white">{p.name}</span>
                    <span className="text-xs font-mono text-cyan-400 font-bold">{p.price}</span>
                  </div>
                  <div className="flex justify-between text-[11px] font-mono text-slate-400">
                    <span>Category: {p.cat}</span>
                    <span>Stock: {p.stock} units</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Orders Module (IDOR Seeded) */}
        {activeTab === 'orders' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">Order Management System</h3>
                <p className="text-xs text-slate-400 font-mono">Endpoint: GET /api/orders/{'{id}'} (Seeded with IDOR)</p>
              </div>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-orange-950 text-orange-400 border border-orange-900">
                IDOR Target Endpoint
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2">Order ID</th>
                    <th>User ID</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Shipping Destination</th>
                    <th>Classification</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  <tr>
                    <td className="py-2.5 text-cyan-400">#001</td>
                    <td>1 (sec_admin)</td>
                    <td>$49,998</td>
                    <td>Delivered</td>
                    <td>SOC Command Bunker Alpha</td>
                    <td>Standard</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 text-cyan-400">#002</td>
                    <td>2 (alice_dev)</td>
                    <td>$1,200</td>
                    <td>Completed</td>
                    <td>Dev Lab 402, Building B</td>
                    <td>Standard</td>
                  </tr>
                  <tr className="bg-red-950/20 text-red-300">
                    <td className="py-2.5 font-bold">#005 (TARGET)</td>
                    <td>5 (exec_director)</td>
                    <td>$31,000</td>
                    <td>Classified</td>
                    <td>Executive Underground Shelter Sigma</td>
                    <td className="text-red-400 font-bold">CONTAINS CANARY FLAG</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Admin Panel (Broken Auth Seeded) */}
        {activeTab === 'admin' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">Administrative Security Console</h3>
                <p className="text-xs text-slate-400 font-mono">Endpoint: GET /api/admin/dashboard (Seeded with Header Auth Bypass)</p>
              </div>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-purple-950 text-purple-400 border border-purple-900">
                Broken Auth Target Endpoint
              </span>
            </div>
            <div className="p-4 rounded-lg bg-black/40 border border-slate-800 space-y-3">
              <div className="flex items-center space-x-2 text-xs font-mono text-slate-300">
                <Lock className="w-4 h-4 text-purple-400" />
                <span>Admin Login: POST /api/admin/login (username: sec_admin)</span>
              </div>
              <p className="text-xs text-slate-400">
                In vulnerable mode, passing header <code className="text-red-400 font-mono">X-Admin-Bypass: arena-debug-mode</code> returns administrative metrics and exposes <code className="text-cyan-300 font-mono">FLAG&#123;CANARY_ADMIN_AUTH_BYPASS_404&#125;</code> without valid bearer tokens.
              </p>
            </div>
          </div>
        )}

        {/* Files Module (Path Traversal Seeded) */}
        {activeTab === 'files' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white">File Repository & Storage Enclave</h3>
                <p className="text-xs text-slate-400 font-mono">Endpoint: GET /api/files/download (Seeded with Path Traversal)</p>
              </div>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-900">
                Path Traversal Target
              </span>
            </div>
            <div className="space-y-2">
              <div className="p-3 rounded-lg bg-black/40 border border-slate-800 flex justify-between items-center text-xs font-mono">
                <span>system_guide.txt (Designated public documentation)</span>
                <span className="text-emerald-400">Safe Boundary</span>
              </div>
              <div className="p-3 rounded-lg bg-red-950/20 border border-red-900/60 flex justify-between items-center text-xs font-mono text-red-300">
                <span>../canary_storage/canary_flag.txt (Restricted canary file)</span>
                <span className="text-red-400 font-bold">Vulnerable to ../ traversal</span>
              </div>
            </div>
          </div>
        )}

        {/* Users Module */}
        {activeTab === 'users' && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white">User Registry & Account Directory</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
              {[
                { name: "sec_admin", role: "admin", dept: "Cyber Operations" },
                { name: "alice_dev", role: "developer", dept: "Software Engineering" },
                { name: "bob_analyst", role: "analyst", dept: "SOC Tier 2" },
                { name: "exec_director", role: "executive", dept: "Executive Committee" }
              ].map((u, i) => (
                <div key={i} className="p-3 rounded-lg bg-black/40 border border-slate-800">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-white">{u.name}</span>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-cyan-400">{u.role}</span>
                  </div>
                  <span className="text-slate-400 text-[11px]">{u.dept}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Search Module */}
        {activeTab === 'search' && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white">Unified Sandbox Search Interface</h3>
            <p className="text-xs text-slate-400 font-mono">
              Filter across users, products, and orders using safe prepared queries or test the specialized product search vector.
            </p>
          </div>
        )}

        {/* Interactive Exploit Probe Console */}
        {activeTab === 'console' && (
          <div className="space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-cyan-400 flex items-center gap-1.5">
                  <Terminal className="w-4 h-4" /> Live Interactive Probe Console
                </h3>
                <p className="text-xs text-slate-400">
                  Test vulnerability payloads against the local target app and observe real responses under vulnerable vs patched states.
                </p>
              </div>
              <span className={`text-[11px] font-mono font-bold px-2.5 py-1 rounded ${
                config?.global_mode === 'vulnerable' ? 'bg-red-950 text-red-400 border border-red-800' : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
              }`}>
                TARGET MODE: {config?.global_mode?.toUpperCase()}
              </span>
            </div>

            {/* Vector Selector */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {[
                { id: 'sqli', name: '1. SQL Injection' },
                { id: 'idor', name: '2. IDOR' },
                { id: 'path_traversal', name: '3. Path Traversal' },
                { id: 'admin_auth', name: '4. Broken Admin Auth' }
              ].map((v) => (
                <button
                  key={v.id}
                  onClick={() => updateVectorSelection(v.id as any)}
                  className={`px-3 py-2 rounded-lg text-xs font-mono font-bold border transition ${
                    selectedVector === v.id
                      ? 'bg-cyan-950/60 border-cyan-500 text-cyan-300 glow-cyan'
                      : 'bg-black/40 border-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {v.name}
                </button>
              ))}
            </div>

            {/* Input Bar */}
            <div className="space-y-1">
              <label className="text-xs font-mono text-slate-400">
                {selectedVector === 'sqli' && "Search Query Payload (query param):"}
                {selectedVector === 'idor' && "Order ID to Access (order_id):"}
                {selectedVector === 'path_traversal' && "File Path Parameter (filename):"}
                {selectedVector === 'admin_auth' && "Header Value for 'X-Admin-Bypass':"}
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customInput}
                  onChange={(e) => setCustomInput(e.target.value)}
                  className="flex-1 px-3 py-2 bg-black border border-slate-700 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-cyan-400"
                />
                <button
                  onClick={runLiveProbe}
                  disabled={consoleLoading}
                  className="flex items-center space-x-1.5 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-bold glow-cyan transition transform active:scale-95 disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{consoleLoading ? "Testing..." : "Send Request"}</span>
                </button>
              </div>
            </div>

            {/* Response Viewer */}
            {consoleResult && (
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-400">Response Status: {consoleResult.status}</span>
                  {typeof consoleResult.data === 'string' && consoleResult.data.includes('FLAG{') && (
                    <span className="text-red-400 font-bold animate-pulse">CANARY FLAG DETECTED!</span>
                  )}
                </div>
                <pre className="p-4 rounded-lg bg-black border border-slate-800 text-xs font-mono text-slate-200 overflow-x-auto max-h-60">
                  {typeof consoleResult.data === 'object'
                    ? JSON.stringify(consoleResult.data, null, 2)
                    : String(consoleResult.data || consoleResult.error || '')}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
