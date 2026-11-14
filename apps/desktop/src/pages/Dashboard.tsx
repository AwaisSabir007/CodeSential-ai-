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

  const recentScans = [...scans].slice(0, 10).reverse();

  // If all scans share the same calendar date, show time (HH:MM) instead to avoid
  // duplicate axis labels. Otherwise show "Mon DD".
  const uniqueDates = new Set(
    recentScans.map((s) =>
      new Date(s.started_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    )
  );
  const allSameDay = uniqueDates.size <= 1 && recentScans.length > 1;

  const barData = recentScans.map((s, idx) => {
    const d = new Date(s.started_at);
    const label = allSameDay
      ? d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
      : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    return {
      date: label,
      findings: s.findings_count,
      // keep a unique key for recharts even if labels collide
      _idx: idx,
    };
  });

  const scanners = [
    { name: 'Bandit', target: 'Python AST Security', status: 'Active' },
    { name: 'Semgrep', target: 'Multi-Language Static Rules', status: 'Active' },
    { name: 'Gitleaks', target: 'Secrets & API Key Detector', status: 'Active' },
    { name: 'pip-audit', target: 'Python Package Advisories', status: 'Active' },
    { name: 'npm audit', target: 'Node Dependency CVEs', status: 'Active' },
    { name: 'CodeBERT Neural', target: 'Deep Learning Risk Head', status: 'Ready' },
  ];

  const tooltipStyle = {
    backgroundColor: '#ffffff',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    color: '#111827',
    fontSize: 11,
    boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex items-center justify-between bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Security Command Center</h1>
          <p className="text-sm text-gray-500 mt-1">
            Real-time IDE change detection, static analysis, neural risk scoring, and autonomous agent
            remediation.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => activeProject && triggerScan(activeProject.id, 1)}
            disabled={!activeProject}
            className="bg-gray-900 hover:bg-gray-800 text-white rounded-lg px-4 py-2 text-sm font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            Scan Current Project
          </button>
        </div>
      </div>

      {/* Row 1: stat cards + severity donut */}
      <div className="grid grid-cols-5 gap-5">
        <div className="col-span-4 grid grid-cols-2 gap-5">
          {/* Critical */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:border-gray-300 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="section-label">Critical Risks</p>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-2xl font-semibold text-gray-900 font-mono">{criticalCount}</span>
                  <span className="text-xs text-gray-400">Needs Attention</span>
                </div>
              </div>
              <ShieldAlert className="w-5 h-5 text-gray-300" />
            </div>
          </div>

          {/* High */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:border-gray-300 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="section-label">High Severity</p>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-2xl font-semibold text-gray-900 font-mono">{highCount}</span>
                  <span className="text-xs text-gray-400">Investigation Queue</span>
                </div>
              </div>
              <AlertTriangle className="w-5 h-5 text-gray-300" />
            </div>
          </div>

          {/* Open */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:border-gray-300 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="section-label">Open Findings</p>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-2xl font-semibold text-gray-900 font-mono">{openCount}</span>
                  <span className="text-xs text-gray-400">Across all files</span>
                </div>
              </div>
              <Activity className="w-5 h-5 text-gray-300" />
            </div>
          </div>

          {/* Projects */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:border-gray-300 transition-colors">
            <div className="flex items-start justify-between">
              <div>
                <p className="section-label">Monitored Projects</p>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-2xl font-semibold text-gray-900 font-mono">{projects.length}</span>
                  <span className="text-xs text-gray-400">Watchdog Observers</span>
                </div>
              </div>
              <FolderGit2 className="w-5 h-5 text-gray-300" />
            </div>
          </div>
        </div>

        {/* Severity Donut */}
        <div className="col-span-1 bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex flex-col items-center justify-center">
          <div className="text-xs font-medium text-gray-700 mb-2">Severity Mix</div>
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
            <Tooltip contentStyle={tooltipStyle} />
          </PieChart>
          <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 mt-2">
            {severityData.map((d) => (
              <div key={d.name} className="flex items-center gap-1 text-[10px] text-gray-500">
                <span className="w-2 h-2 rounded-full" style={{backgroundColor: d.color}} />
                {d.name}: {d.value}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 2: Scan History Bar Chart */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-900 mb-4">Scan History</h2>
        {barData.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No scan history yet</p>
        ) : (
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={barData} margin={{top: 4, right: 8, left: -20, bottom: 0}}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis
                dataKey="date"
                tick={{fill: '#9ca3af', fontSize: 10}}
                axisLine={false}
                tickLine={false}
                interval={0}
              />
              <YAxis
                tick={{fill: '#9ca3af', fontSize: 10}}
                axisLine={false}
                tickLine={false}
                allowDecimals={false}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="findings" fill="#111827" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Row 3: Scanner matrix + Agent actions */}
      <div className="grid grid-cols-3 gap-5">
        {/* Scanners */}
        <div className="col-span-2 bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-900">Scanner Engine Coverage</h2>
            <span className="section-label">6 Engines Active</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {scanners.map((s) => (
              <div
                key={s.name}
                className="p-3 bg-gray-50 border border-gray-100 rounded-lg hover:border-gray-200 flex items-center justify-between transition-colors"
              >
                <div>
                  <div className="text-xs font-semibold text-gray-900">{s.name}</div>
                  <div className="text-[10px] text-gray-500 mt-0.5">{s.target}</div>
                </div>
                <span className={`badge text-[10px] border ${
                  s.status === 'Active'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
                    : 'bg-gray-50 text-gray-500 border-gray-200'
                }`}>
                  {s.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Agents Panel */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 mb-2">
              <Cpu className="w-4 h-4 text-gray-400" />
              Autonomous Agents
            </div>
            <p className="text-xs text-gray-500">
              Multi-agent state machine ready to triage, trace taint flows, compute neural risk, and
              formulate verified patches.
            </p>
          </div>
          <div className="mt-4 space-y-2">
            <button
              onClick={() => setActiveTab('investigations')}
              className="w-full py-2.5 px-4 rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-700 border border-gray-100 text-xs font-medium flex items-center justify-between transition-colors"
            >
              <span>View Investigation Graph</span>
              <span className="text-gray-400 font-mono text-[11px]">&rarr;</span>
            </button>
            <button
              onClick={() => setActiveTab('insights')}
              className="w-full py-2.5 px-4 rounded-lg bg-gray-50 hover:bg-gray-100 text-gray-700 border border-gray-100 text-xs font-medium flex items-center justify-between transition-colors"
            >
              <span>CodeBERT Model Metrics</span>
              <span className="text-gray-400 font-mono text-[11px]">&rarr;</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
