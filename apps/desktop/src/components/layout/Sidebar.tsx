import React from 'react';
import {
  ShieldAlert,
  LayoutDashboard,
  FolderGit2,
  Activity,
  Bug,
  Cpu,
  Zap,
  GitPullRequest,
  FileText,
  BrainCircuit,
  Sliders,
} from 'lucide-react';
import { useAppStore, NavigationTab } from '../../stores/appStore';

interface NavItem {
  id: NavigationTab;
  label: string;
  icon: React.ElementType;
  badge?: number;
}

export const Sidebar: React.FC = () => {
  const { activeTab, setActiveTab, findings, investigations, wsConnected } = useAppStore();

  const openFindingsCount = findings.filter((f) => f.status === 'open').length;
  const activeInvCount = investigations.filter((i) => i.status === 'in_progress').length;

  const navItems: NavItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'projects', label: 'Projects', icon: FolderGit2 },
    { id: 'monitoring', label: 'Live Monitoring', icon: Activity },
    { id: 'findings', label: 'Security Findings', icon: Bug, badge: openFindingsCount || undefined },
    { id: 'investigations', label: 'AI Investigations', icon: Cpu, badge: activeInvCount || undefined },
    { id: 'optimization', label: 'Code Optimization', icon: Zap },
    { id: 'fixes', label: 'Proposed Fixes', icon: GitPullRequest },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'insights', label: 'Neural Model Insights', icon: BrainCircuit },
    { id: 'settings', label: 'Settings', icon: Sliders },
  ];

  return (
    <aside className="w-72 h-screen bg-[#111827] border-r border-white/5 flex flex-col select-none">
      {/* Brand Header */}
      <div className="h-16 px-6 flex items-center gap-3 border-b border-white/5 bg-gradient-to-b from-indigo-950/20 to-transparent">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center shadow-glow ring-1 ring-indigo-500/30">
          <ShieldAlert className="w-5 h-5 text-white" />
        </div>
        <div>
          <span className="font-semibold text-sm tracking-wide text-white block">CodeSentinel AI</span>
          <span className="text-[10px] text-indigo-400 tracking-wider font-mono uppercase">Local-First SecOps</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-4 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                isActive
                  ? 'nav-active rounded-l-none'
                  : 'text-gray-500 hover:text-gray-200 hover:bg-white/[0.04]'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-300' : 'text-gray-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span
                  className={`px-1.5 py-0.5 text-[10px] font-semibold rounded-full ${
                    isActive ? 'bg-indigo-500/15 text-indigo-300' : 'bg-red-500/20 text-red-400'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer System Status */}
      <div className="p-4 border-t border-white/5 bg-[#0B1020]/50">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                wsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400 animate-pulse'
              }`}
            />
            Scanner Engine
          </span>
          <span className="text-[10px] font-mono text-gray-500">v1.0.0</span>
        </div>
      </div>
    </aside>
  );
};
