import React from 'react';
import { Play, Folder, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAppStore } from '../../stores/appStore';

export const Header: React.FC = () => {
  const {
    projects,
    activeProject,
    setActiveProject,
    triggerScan,
    isBackendConnected,
  } = useAppStore();

  const handleScanClick = () => {
    if (activeProject) {
      triggerScan(activeProject.id, 1);
    }
  };

  return (
    <header className="h-14 border-b border-gray-100 bg-white px-6 flex items-center justify-between z-10">
      {/* Active Project Selector */}
      <div className="flex items-center gap-3">
        <Folder className="w-4 h-4 text-gray-400" />
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
          <span className="flex items-center gap-1.5 text-xs text-emerald-600 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Live Watch Active
          </span>
        )}
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* Connection Status */}
        <div className="flex items-center gap-1.5 text-xs">
          {isBackendConnected ? (
            <span className="flex items-center gap-1.5 text-emerald-600 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              API Connected
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-amber-500 font-medium">
              <AlertCircle className="w-3.5 h-3.5" />
              Local Standalone Mode
            </span>
          )}
        </div>

        {/* Quick Scan Button */}
        <button
          onClick={handleScanClick}
          disabled={!activeProject}
          className="bg-gray-900 hover:bg-gray-800 text-white rounded-lg px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-50 cursor-pointer"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          Quick Scan
        </button>
      </div>
    </header>
  );
};
