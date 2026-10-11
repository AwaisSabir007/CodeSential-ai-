import React from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  FolderGit2,
  Activity,
  Cpu,
  Play,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useAppStore } from '../stores/appStore';

export const Dashboard: React.FC = () => {
  const { findings, scans, projects, activeProject, triggerScan, setActiveTab } = useAppStore();

  const criticalCount = findings.filter((f) => f.severity === 'critical').length;
  const highCount = findings.filter((f) => f.severity === 'high').length;
  const openCount = findings.filter((f) => f.status === 'open').length;
  const mediumCount = findings.filter((f) => f.severity === 'medium').length;
  const lowInfoCount = findings.filter(
    (f) => f.severity === 'low' || f.severity === 'informational'
  ).length;

  const severityData = [
    { name: 'Critical', value: criticalCount, color: '#ef4444' },
    { name: 'High', value: highCount, color: '#f59e0b' },
    { name: 'Medium', value: mediumCount, color: '#eab308' },
    { name: 'Low/Info', value: lowInfoCount, color: '#6366f1' },
  ];

  const barData = [...scans]
    .slice(0, 10)
    .reverse()
    .map((s) => ({
      date: new Date(s.started_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      findings: s.findings_count,
    }));

  const scanners = [
    { name: 'Bandit', target: 'Python AST Security', status: 'Active', color: 'emerald' },
    { name: 'Semgrep', target: 'Multi-Language Static Rules', status: 'Active', color: 'emerald' },
    { name: 'Gitleaks', target: 'Secrets & API Key Detector', status: 'Active', color: 'emerald' },
    { name: 'pip-audit', target: 'Python Package Advisories', status: 'Active', color: 'emerald' },
    { name: 'npm audit', target: 'Node Dependency CVEs', status: 'Active', color: 'emerald' },
    { name: 'CodeBERT Neural', target: 'Deep Learning Risk Head', status: 'Ready', color: 'indigo' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome */}
      <div className="flex items-center justify-between bg-gradient-to-r from-indigo-950/40 via-surface to-surface p-6 rounded-2xl border border-indigo-500/10">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Security Command Center</h1>
          <p className="text-xs text-gray-400 mt-1">
            Real-time IDE change detection, static analysis, neural risk scoring, and autonomous agent
            remediation.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => activeProject && triggerScan(activeProject.id, 1)}
            disabled={!activeProject}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-glow transition-all active:scale-95 disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            Scan Current Project
          </button>
        </div>
      </div>

      {/* Row 1: stat cards (col-span-4) + severity donut (col-span-1) */}
      <div className="grid grid-cols-5 gap-4">
        <div className="col-span-4 grid grid-cols-2 gap-4">
          <div className="p-5 rounded-xl bg-[#111827] border border-white/5 glow-card">
            <div className="flex items-center justify-between text-gray-400 text-xs">
              <span>Critical Risks</span>
              <ShieldAlert className="w-4 h-4 text-red-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white font-mono">{criticalCount}</span>
              <span className="text-[10px] text-red-400 font-medium">Needs Attention</span>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-[#111827] border border-white/5 glow-card">
            <div className="flex items-center justify-between text-gray-400 text-xs">
              <span>High Severity</span>
              <AlertTriangle className="w-4 h-4 text-amber-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white font-mono">{highCount}</span>
              <span className="text-[10px] text-amber-400 font-medium">Investigation Queue</span>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-[#111827] border border-white/5 glow-card">
            <div className="flex items-center justify-between text-gray-400 text-xs">
              <span>Open Findings</span>
              <Activity className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white font-mono">{openCount}</span>
              <span className="text-[10px] text-gray-400 font-medium">Across all files</span>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-[#111827] border border-white/5 glow-card">
            <div className="flex items-center justify-between text-gray-400 text-xs">
              <span>Monitored Projects</span>
              <FolderGit2 className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white font-mono">{projects.length}</span>
              <span className="text-[10px] text-emerald-400 font-medium">Watchdog Observers</span>
            </div>
          </div>
        </div>

        {/* Severity Donut */}
        <div className="col-span-1 p-4 rounded-xl bg-[#111827] border border-white/5 flex flex-col items-center justify-center">
          <div className="text-xs font-semibold text-white mb-2">Severity Mix</div>
          <PieChart width={140} height={140}>
            <Pie
              data={severityData}
              cx={65}
              cy={65}
              innerRadius={40}
              outerRadius={65}
              dataKey="value"
              stroke="none"
            >
              {severityData.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: 'none',
                borderRadius: '8px',
                color: '#fff',
                fontSize: 11,
              }}
            />
          </PieChart>
          <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 mt-2">
            {severityData.map((d) => (
              <div key={d.name} className="flex items-center gap-1 text-[10px] text-gray-400">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                {d.name}: {d.value}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 2: Scan History Bar Chart */}
      <div className="p-5 rounded-xl bg-[#111827] border border-white/5">
        <h2 className="text-sm font-semibold text-white mb-4">Scan History</h2>
        {barData.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-8">No scan history yet</p>
        ) : (
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={barData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.9} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.4} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
              <XAxis
                dataKey="date"
                tick={{ fill: '#9ca3af', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#9ca3af', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                allowDecimals={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: 11,
                }}
              />
              <Bar dataKey="findings" fill="url(#barGradient)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Row 3: Scanner matrix (col-span-2) + Agent actions (col-span-1) */}
      <div className="grid grid-cols-3 gap-6">
        {/* Scanners Active Matrix */}
        <div className="col-span-2 p-5 rounded-xl bg-[#111827] border border-white/5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white">Scanner Engine Coverage</h2>
            <span className="text-[10px] text-gray-400 uppercase font-mono">6 Engines Active</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {scanners.map((s) => (
              <div
                key={s.name}
                className="p-3.5 rounded-lg bg-[#1F2937]/50 border border-white/5 flex items-center justify-between"
              >
                <div>
                  <div className="text-xs font-semibold text-white">{s.name}</div>
                  <div className="text-[10px] text-gray-400 mt-0.5">{s.target}</div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {s.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Agent Actions */}
        <div className="p-5 rounded-xl bg-[#111827] border border-white/5 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-white mb-2">
              <Cpu className="w-4 h-4 text-indigo-400" />
              Autonomous Agents
            </div>
            <p className="text-xs text-gray-400">
              Multi-agent state machine ready to triage, trace taint flows, compute neural risk, and
              formulate verified patches.
            </p>
          </div>
          <div className="mt-4 space-y-2">
            <button
              onClick={() => setActiveTab('investigations')}
              className="w-full py-2.5 px-3 rounded-lg bg-[#1F2937] hover:bg-white/10 text-xs font-medium text-white flex items-center justify-between transition-all"
            >
              <span>View Investigation Graph</span>
              <span className="text-indigo-400 font-mono text-[11px]">&rarr;</span>
            </button>
            <button
              onClick={() => setActiveTab('insights')}
              className="w-full py-2.5 px-3 rounded-lg bg-[#1F2937] hover:bg-white/10 text-xs font-medium text-white flex items-center justify-between transition-all"
            >
              <span>CodeBERT Model Metrics</span>
              <span className="text-indigo-400 font-mono text-[11px]">&rarr;</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
