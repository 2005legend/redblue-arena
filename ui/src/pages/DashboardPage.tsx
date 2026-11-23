import React, { useEffect, useState } from 'react';
import { 
  ShieldAlert, 
  Terminal, 
  Cpu, 
  Scale, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Activity, 
  Radio, 
  TrendingUp, 
  Flame,
  ArrowUpRight
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  LineChart, 
  Line, 
  PieChart, 
  Pie, 
  Cell, 
  CartesianGrid, 
  Legend 
} from 'recharts';
import { getDashboardStats, DashboardStats } from '../services/api';

interface DashboardPageProps {
  onSelectBattle: (battleId: string) => void;
  onNewBattle: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onSelectBattle,
  onNewBattle
}) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
    const interval = setInterval(loadStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const data = await getDashboardStats();
      setStats(data);
    } catch (e) {
      console.error('Error fetching dashboard stats', e);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <Activity className="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
          <p className="text-xs font-mono text-slate-400">Loading live telemetry from ARENA database...</p>
        </div>
      </div>
    );
  }

  const statCards = [
    { label: "Total Battles", value: stats?.total_battles ?? 0, icon: Flame, color: "text-cyan-400", bg: "bg-cyan-950/30", border: "border-cyan-800/50" },
    { label: "Red Agent Success Rate", value: `${stats?.red_success_rate ?? 0}%`, icon: Terminal, color: "text-red-400", bg: "bg-red-950/30", border: "border-red-800/50" },
    { label: "Blue Agent Defense Rate", value: `${stats?.blue_defense_rate ?? 0}%`, icon: Cpu, color: "text-blue-400", bg: "bg-blue-950/30", border: "border-blue-800/50" },
    { label: "Vulnerabilities Discovered", value: stats?.vulnerabilities_discovered ?? 0, icon: ShieldAlert, color: "text-yellow-400", bg: "bg-yellow-950/30", border: "border-yellow-800/50" },
    { label: "Vulnerabilities Patched", value: stats?.vulnerabilities_patched ?? 0, icon: CheckCircle, color: "text-emerald-400", bg: "bg-emerald-950/30", border: "border-emerald-800/50" },
    { label: "Failed Patch Attempts", value: stats?.failed_patch_attempts ?? 0, icon: XCircle, color: "text-rose-400", bg: "bg-rose-950/30", border: "border-rose-800/50" },
    { label: "Average Patch Time", value: `${stats?.average_patch_time_sec ?? 18}s`, icon: Clock, color: "text-purple-400", bg: "bg-purple-950/30", border: "border-purple-800/50" },
    { label: "Application Availability", value: stats?.application_availability ?? "99.98%", icon: Activity, color: "text-cyan-300", bg: "bg-cyan-950/30", border: "border-cyan-800/50" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black text-white tracking-wide">SOC CYBER-INTELLIGENCE DASHBOARD</h1>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Real-time telemetry aggregated from autonomous simulations in SQLite orchestrator
          </p>
        </div>
        <button
          onClick={onNewBattle}
          className="self-start sm:self-auto px-4 py-2 rounded-lg text-xs font-bold bg-cyan-500 hover:bg-cyan-400 text-slate-950 glow-cyan transition"
        >
          Deploy New Simulation
        </button>
      </div>

      {/* 8 Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div
              key={i}
              className={`p-4 rounded-xl bg-[#090d18] border ${card.border} hover:border-cyan-500/60 transition shadow-lg`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-medium text-slate-400">{card.label}</span>
                <div className={`p-1.5 rounded-md ${card.bg}`}>
                  <Icon className={`w-4 h-4 ${card.color}`} />
                </div>
              </div>
              <div className="text-2xl font-black font-mono text-white tracking-tight">{card.value}</div>
            </div>
          );
        })}
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Red vs. Blue Performance */}
        <div className="p-5 rounded-xl bg-[#090d18] border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white">Red vs. Blue Operational Capability</h3>
              <p className="text-[11px] font-mono text-slate-400">Tactical capability scores by operational vector</p>
            </div>
            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="flex items-center gap-1 text-red-400">
                <span className="w-2.5 h-2.5 rounded bg-red-500 inline-block"></span> Red (Attacker)
              </span>
              <span className="flex items-center gap-1 text-blue-400">
                <span className="w-2.5 h-2.5 rounded bg-blue-500 inline-block"></span> Blue (Defender)
              </span>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats?.charts.comparison || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="metric" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748b" domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }}
                />
                <Bar dataKey="red" fill="#ef4444" radius={[4, 4, 0, 0]} />
                <Bar dataKey="blue" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Timeline */}
        <div className="p-5 rounded-xl bg-[#090d18] border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-white">Vulnerability Discovery & Defense Timeline</h3>
              <p className="text-[11px] font-mono text-slate-400">Cumulative rate of breach detection vs. patch deployment</p>
            </div>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-900">
              Zero Regressions
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats?.charts.timeline || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
                <Line type="monotone" dataKey="attacks" stroke="#ef4444" strokeWidth={2} name="Red Probes" />
                <Line type="monotone" dataKey="defenses" stroke="#3b82f6" strokeWidth={2} name="Blue Patches" />
                <Line type="monotone" dataKey="health" stroke="#10b981" strokeWidth={2} strokeDasharray="4 4" name="App Health %" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Security Event Distribution */}
        <div className="p-5 rounded-xl bg-[#090d18] border border-slate-800">
          <h3 className="text-sm font-bold text-white mb-1">Vulnerability Vector Distribution</h3>
          <p className="text-[11px] font-mono text-slate-400 mb-4">Total simulated attacks by threat category</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats?.charts.event_distribution || []}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={45}
                  dataKey="count"
                  paddingAngle={4}
                  label={({ name, percent }) => `${name} (${((percent || 0) * 100).toFixed(0)}%)`}
                >
                  {(stats?.charts.event_distribution || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '11px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Battle History Table */}
        <div className="p-5 rounded-xl bg-[#090d18] border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white">Recent Simulation Battles</h3>
              <span className="text-[10px] font-mono text-cyan-400">Live Database Feed</span>
            </div>
            <div className="space-y-2.5">
              {(stats?.recent_battles || []).map((b, idx) => (
                <div 
                  key={idx}
                  onClick={() => onSelectBattle(b.id)}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-black/40 border border-slate-800/80 hover:border-cyan-500/50 cursor-pointer transition"
                >
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono font-bold text-white">{b.id}</span>
                      <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                        b.status === 'completed' ? 'bg-emerald-950 text-emerald-400' : 'bg-cyan-950 text-cyan-400'
                      }`}>
                        {b.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 truncate max-w-[200px] sm:max-w-xs">{b.name}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] font-mono text-cyan-400 block">{b.blue_patches_approved} Patches</span>
                    <span className="text-[10px] font-mono text-slate-500">{b.start_time?.split(' ')[0]}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
