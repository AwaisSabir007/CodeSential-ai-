import React from 'react';
import { Play, RefreshCw, Folder, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';

export const Header: React.FC = () => {
  const {
    projects,
    activeProject,
    setActiveProject,
    triggerScan,
    isBackendConnected,
    systemHealth,
  } = useAppStore();

  const handleScanClick = () => {
    if (activeProject) {
      triggerScan(activeProject.id, 1);
    }
  };

  return (
    <header className="h-16 border-b border-white/[0.08] bg-white/[0.03] backdrop-blur-xl px-6 flex items-center justify-between z-10">
      {/* Active Project Selector */}
      <div className="flex items-center gap-3">
        <Folder className="w-4 h-4 text-indigo-400" />
        <select
          value={activeProject?.id || ''}
          onChange={(e) => {
            const found = projects.find((p) => p.id === e.target.value);
            setActiveProject(found || null);
          }}
          className="input text-xs py-1.5 cursor-pointer"
        >
          {projects.length === 0 ? (
            <option value="">No Active Project Selected</option>
          ) : (
            projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.root_path})
              </option>
            ))
          )}
        </select>
        {activeProject?.is_monitored && (
          <span className="flex items-center gap-1.5 px-3 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 backdrop-blur-sm">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Live Watch Active
          </span>
        )}
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* Connection Status Pill */}
        <div className="flex items-center gap-1.5 text-xs">
          {isBackendConnected ? (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-medium border border-emerald-500/20">
              <CheckCircle2 className="w-3.5 h-3.5" />
              API Connected
            </span>
          ) : (
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 font-medium border border-amber-500/20">
              <AlertCircle className="w-3.5 h-3.5" />
              Local Standalone Mode
            </span>
          )}
        </div>

        {/* Quick Scan Button */}
        <button
          onClick={handleScanClick}
          disabled={!activeProject}
          className="btn-primary flex items-center gap-2 disabled:opacity-50 cursor-pointer shadow-glow"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          Quick Scan
        </button>
      </div>
    </header>
  );
};
