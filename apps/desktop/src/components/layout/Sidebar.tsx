import React from 'react';
import {
  ShieldCheck,
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
    <aside className="w-64 h-screen bg-white border-r border-gray-100 flex flex-col select-none">
      {/* Brand Header */}
      <div className="h-14 px-4 flex items-center gap-3 border-b border-gray-100">
        <div className="w-8 h-8 rounded-lg bg-gray-900 flex items-center justify-center flex-shrink-0">
          <ShieldCheck className="w-4 h-4 text-white" />
        </div>
        <div>
          <span className="font-semibold text-sm text-gray-900 block">CodeSentinel AI</span>
          <span className="text-xs text-gray-400 tracking-wider">Local-First SecOps</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'nav-active rounded-l-none pl-[10px]'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50 rounded-lg'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${isActive ? 'text-gray-700' : 'text-gray-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span
                  className={`px-1.5 py-0.5 text-[10px] font-semibold rounded ${
                    isActive ? 'bg-gray-200 text-gray-700' : 'bg-red-100 text-red-600'
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
      <div className="p-4 border-t border-gray-100 bg-white">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-xs text-gray-400">
            <span
              className={`w-2 h-2 rounded-full flex-shrink-0 ${
                wsConnected ? 'bg-emerald-500' : 'bg-gray-300'
              }`}
            />
            Scanner Engine
          </span>
          <span className="text-[10px] font-mono text-gray-400">v1.0.0</span>
        </div>
      </div>
    </aside>
  );
};
