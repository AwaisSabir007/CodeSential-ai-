import React, { useState } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle,
  Cpu,
  Search,
  Filter,
  Code,
  X,
} from 'lucide-react';
import { useAppStore } from '../stores/appStore';
import { Finding, Severity } from '../types';
import { api } from '../services/api';

export const Findings: React.FC = () => {
  const { findings, setActiveTab, setActiveInvestigation, activeProject } = useAppStore();
  const [search, setSearch] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('open');
  const [activeFinding, setActiveFinding] = useState<Finding | null>(null);

  const filtered = findings.filter((f) => {
    if (activeProject && f.project_id !== activeProject.id) return false;
    if (selectedStatus !== 'all' && f.status !== selectedStatus) return false;
    const matchesSearch =
      f.title.toLowerCase().includes(search.toLowerCase()) ||
      f.file_path.toLowerCase().includes(search.toLowerCase()) ||
      f.rule_id.toLowerCase().includes(search.toLowerCase());
    const matchesSev = selectedSeverity === 'all' || f.severity === selectedSeverity;
    return matchesSearch && matchesSev;
  });

  const getSeverityBadge = (sev: Severity) => {
    switch (sev) {
      case 'critical':
        return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'high':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'medium':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
      default:
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    }
  };

  const handleStartInvestigation = async (finding: Finding) => {
    try {
      const inv = await api.triggerInvestigation({
        project_id: finding.project_id,
        finding_id: finding.id,
        scanner_name: finding.scanner_name,
        rule_id: finding.rule_id,
        category: finding.category,
        severity: finding.severity,
        file_path: finding.file_path,
        line_number: finding.line_start ?? finding.start_line ?? 1,
        snippet: finding.code_snippet || finding.snippet || finding.title,
        title: finding.title,
        description: finding.description,
      });
      setActiveInvestigation(inv);
      setActiveTab('investigations');
    } catch (err: any) {
      alert(`Investigation failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Security Findings</h1>
          <p className="text-sm text-gray-400 font-light mt-0.5">
            Normalized, correlated vulnerability findings from static analysis, secret scans, and dependency audits.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by rule, title, or filename..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input w-full pl-9"
          />
        </div>
        <select
          value={selectedSeverity}
          onChange={(e) => setSelectedSeverity(e.target.value)}
          className="input"
        >
          <option value="all">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="input"
        >
          <option value="open">Open Findings</option>
          <option value="resolved">Resolved Findings</option>
          <option value="all">All Statuses</option>
        </select>
      </div>

      {/* Findings Table */}
      <div className="rounded-2xl bg-[#111827] border border-white/[0.08] overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-white/[0.03] text-gray-400 border-b border-white/[0.05]">
            <tr>
              <th className="py-3 px-4 section-label">Severity</th>
              <th className="py-3 px-4 section-label">Vulnerability Title</th>
              <th className="py-3 px-4 section-label">Scanner</th>
              <th className="py-3 px-4 section-label">Location</th>
              <th className="py-3 px-4 section-label text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.05]">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-gray-500">
                  No findings matching criteria
                </td>
              </tr>
            ) : (
              filtered.map((f) => (
                <tr key={f.id} className="hover:bg-white/[0.03] transition-colors">
                  <td className="py-3 px-4">
                    <span
                      className={`badge border uppercase tracking-wider ${getSeverityBadge(
                        f.severity
                      )}`}
                    >
                      {f.severity}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="font-semibold text-white">{f.title}</div>
                    <div className="text-[10px] text-gray-400 font-mono mt-0.5">{f.rule_id}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-gray-300">{f.scanner_name}</span>
                  </td>
                  <td className="py-3 px-4 font-mono text-[11px] text-gray-400">
                    {f.file_path}:{f.line_start ?? f.start_line ?? 1}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => setActiveFinding(f)}
                      className="px-3 py-1.5 rounded-full bg-white/[0.05] hover:bg-white/10 text-gray-300 hover:text-white transition-all duration-200 mr-2 text-xs"
                    >
                      Details
                    </button>
                    <button
                      onClick={() => handleStartInvestigation(f)}
                      className="px-3 py-1.5 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium shadow-glow transition-all duration-200 text-xs"
                    >
                      Investigate AI
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Details Slide-over modal */}
      {activeFinding && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex justify-end z-50">
          <div className="w-full max-w-xl bg-[#0d1428]/95 backdrop-blur-xl h-full p-6 border-l border-white/[0.08] flex flex-col justify-between overflow-y-auto">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-white/[0.05]">
                <div>
                  <span
                    className={`badge border uppercase ${getSeverityBadge(
                      activeFinding.severity
                    )}`}
                  >
                    {activeFinding.severity}
                  </span>
                  <h2 className="text-base font-bold text-white mt-2">{activeFinding.title}</h2>
                </div>
                <button
                  onClick={() => setActiveFinding(null)}
                  className="p-1 rounded-full text-gray-400 hover:text-white hover:bg-white/5"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4 mt-6">
                <div>
                  <div className="text-xs font-semibold text-gray-300 mb-1">Description</div>
                  <p className="text-xs text-gray-400 leading-relaxed">{activeFinding.description}</p>
                </div>

                <div>
                  <div className="text-xs font-semibold text-gray-300 mb-1">Code Snippet</div>
                  <div className="p-3 bg-[#0B1020] rounded-2xl border border-white/[0.05] font-mono text-xs text-gray-200 overflow-x-auto">
                    <pre>{activeFinding.code_snippet || activeFinding.snippet || 'No code preview available'}</pre>
                  </div>
                </div>

                <div>
                  <div className="text-xs font-semibold text-gray-300 mb-1">Recommendation</div>
                  <p className="text-xs text-indigo-300 bg-indigo-950/20 p-3 rounded-2xl border border-indigo-500/20">
                    {activeFinding.recommendation || 'Apply parameterized execution or sanitized inputs.'}
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-white/[0.05] flex items-center justify-end gap-3">
              <button
                onClick={() => setActiveFinding(null)}
                className="btn-secondary"
              >
                Close
              </button>
              <button
                onClick={() => {
                  const f = activeFinding;
                  setActiveFinding(null);
                  handleStartInvestigation(f);
                }}
                className="btn-primary shadow-glow"
              >
                Launch Multi-Agent Investigation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
