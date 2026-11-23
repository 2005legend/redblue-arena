import React from 'react';
import { 
  ShieldAlert, 
  Terminal, 
  Cpu, 
  Scale, 
  LayoutDashboard, 
  Swords, 
  FileCode2, 
  FileText, 
  Bug, 
  Layers, 
  Play, 
  Activity,
  Radio
} from 'lucide-react';

interface NavbarProps {
  currentPage: string;
  setCurrentPage: (page: string) => void;
  onOpenConfig: () => void;
  activeBattleId?: string;
  isBattleRunning?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentPage,
  setCurrentPage,
  onOpenConfig,
  activeBattleId,
  isBattleRunning
}) => {
  const navItems = [
    { id: 'landing', label: 'Home', icon: Activity },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'arena', label: 'Live Arena', icon: Swords, highlight: true },
    { id: 'target_app', label: 'Target App', icon: Layers },
    { id: 'red_agent', label: 'Red Agent', icon: Terminal, color: 'text-red-400' },
    { id: 'blue_agent', label: 'Blue Agent', icon: Cpu, color: 'text-blue-400' },
    { id: 'referee', label: 'Referee', icon: Scale, color: 'text-purple-400' },
    { id: 'vulnerabilities', label: 'Vulns', icon: Bug },
    { id: 'patches', label: 'Patches', icon: FileCode2 },
    { id: 'reports', label: 'Reports', icon: FileText }
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#070a12]/95 backdrop-blur border-b border-cyan-900/40 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div 
            onClick={() => setCurrentPage('landing')}
            className="flex items-center space-x-3 cursor-pointer group"
          >
            <div className="relative">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 via-blue-600/30 to-purple-600/20 border border-cyan-500/40 flex items-center justify-center glow-cyan group-hover:border-cyan-400 transition-all">
                <ShieldAlert className="w-6 h-6 text-cyan-400" />
              </div>
              {isBattleRunning && (
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                </span>
              )}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-black tracking-wider text-white">ARENA</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60 uppercase">
                  v2.4 SOC
                </span>
              </div>
              <p className="text-[10px] font-mono text-cyan-500/80 -mt-0.5 tracking-tight">
                Discover. Defend. Verify.
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentPage(item.id)}
                  className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                    isActive
                      ? item.highlight
                        ? 'bg-gradient-to-r from-red-600/30 to-blue-600/30 text-white border border-cyan-500/60 shadow-[0_0_12px_rgba(6,182,212,0.3)]'
                        : 'bg-cyan-950/70 text-cyan-300 border border-cyan-800/60 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${item.color || (isActive ? 'text-cyan-400' : 'text-slate-400')}`} />
                  <span>{item.label}</span>
                  {item.highlight && isBattleRunning && (
                    <Radio className="w-3 h-3 text-red-400 animate-pulse ml-0.5" />
                  )}
                </button>
              );
            })}
          </nav>

          {/* Action & Status */}
          <div className="flex items-center space-x-3">
            {/* Status Pill */}
            <div className="hidden sm:flex items-center space-x-2 px-2.5 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-[11px] font-mono text-slate-300">
              <span className={`w-2 h-2 rounded-full ${isBattleRunning ? 'bg-emerald-400 animate-pulse' : 'bg-cyan-400'}`}></span>
              <span>{isBattleRunning ? 'SIMULATION ACTIVE' : 'SANDBOX ISOLATED'}</span>
            </div>

            {/* Battle Launcher Button */}
            <button
              onClick={onOpenConfig}
              className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-md glow-cyan transition-all transform active:scale-95"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>New Battle</span>
            </button>
          </div>
        </div>

        {/* Mobile Nav strip */}
        <div className="lg:hidden flex overflow-x-auto py-2 space-x-2 border-t border-slate-800/80 scrollbar-none">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentPage(item.id)}
                className={`flex items-center space-x-1 px-2.5 py-1 rounded text-xs whitespace-nowrap ${
                  isActive ? 'bg-cyan-900/60 text-cyan-200 border border-cyan-700' : 'text-slate-400'
                }`}
              >
                <Icon className="w-3 h-3" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
