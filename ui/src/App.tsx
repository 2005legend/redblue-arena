import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { BattleConfigModal } from './components/BattleConfigModal';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { BattleArenaPage } from './pages/BattleArenaPage';
import { TargetAppPage } from './pages/TargetAppPage';
import { RedAgentPage } from './pages/RedAgentPage';
import { BlueAgentPage } from './pages/BlueAgentPage';
import { RefereePage } from './pages/RefereePage';
import { VulnerabilityExplorerPage } from './pages/VulnerabilityExplorerPage';
import { CodePatchesPage } from './pages/CodePatchesPage';
import { BattleReportsPage } from './pages/BattleReportsPage';
import ClassicApp from './classic/App.jsx';
import { createBattle, startBattle } from './services/api';

export function App() {
  const [currentPage, setCurrentPage] = useState<string>('landing');
  const [isConfigOpen, setIsConfigOpen] = useState<boolean>(false);
  const [activeBattleId, setActiveBattleId] = useState<string>('MATCH-LIVE-001');
  const [isBattleRunning, setIsBattleRunning] = useState<boolean>(false);

  const handleStartBattleFromConfig = async (config: any) => {
    try {
      const res = await createBattle(config);
      const newId = res.battle_id;
      setActiveBattleId(newId);
      setIsBattleRunning(true);
      await startBattle(newId);
      setCurrentPage('arena');
    } catch (e: any) {
      alert(e.message || 'Error launching battle');
    }
  };

  return (
    <div className="min-h-screen bg-[#070a12] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      {/* Top Navbar */}
      <Navbar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        onOpenConfig={() => setIsConfigOpen(true)}
        activeBattleId={activeBattleId}
        isBattleRunning={isBattleRunning}
      />

      {/* Main Page Content */}
      <main className="flex-1">
        {currentPage === 'landing' && (
          <LandingPage
            onStartBattle={() => setIsConfigOpen(true)}
            onExploreArena={() => setCurrentPage('arena')}
            setCurrentPage={setCurrentPage}
          />
        )}

        {currentPage === 'dashboard' && (
          <DashboardPage
            onSelectBattle={(bId) => {
              setActiveBattleId(bId);
              setCurrentPage('arena');
            }}
            onNewBattle={() => setIsConfigOpen(true)}
          />
        )}

        {currentPage === 'arena' && (
          <BattleArenaPage
            onOpenConfig={() => setIsConfigOpen(true)}
            activeBattleId={activeBattleId}
            setActiveBattleId={setActiveBattleId}
          />
        )}

        {currentPage === 'target_app' && <TargetAppPage />}

        {currentPage === 'red_agent' && (
          <RedAgentPage onOpenConfig={() => setIsConfigOpen(true)} />
        )}

        {currentPage === 'blue_agent' && <BlueAgentPage />}

        {currentPage === 'referee' && <RefereePage />}

        {currentPage === 'vulnerabilities' && <VulnerabilityExplorerPage />}

        {currentPage === 'patches' && <CodePatchesPage />}

        {currentPage === 'reports' && <BattleReportsPage />}

        {currentPage === 'classic' && (
          <div className="max-w-6xl mx-auto px-4 py-8">
            <div className="mb-4 p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono text-cyan-300">
              Classic Vibe Arena Live Replay Mode (Direct Port 8765 WebSocket Connection)
            </div>
            <ClassicApp />
          </div>
        )}
      </main>

      {/* Battle Configuration Modal (16 Interactive Fields) */}
      <BattleConfigModal
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
        onStartBattle={handleStartBattleFromConfig}
      />

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-[#05070c] py-6 px-4 print:hidden">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-slate-500">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-300">ARENA</span>
            <span>•</span>
            <span className="text-cyan-400">Discover. Defend. Verify.</span>
          </div>
          <div className="flex items-center space-x-4">
            <span>Local Isolated Sandbox</span>
            <span>•</span>
            <span>Deterministic Pytest Referee</span>
            <span>•</span>
            <span>v2.4.0 SOC</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
