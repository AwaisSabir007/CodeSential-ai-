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
        return 'bg-red-50 text-red-700 border border-red-100';
      case 'high':
        return 'bg-amber-50 text-amber-700 border border-amber-100';
      case 'medium':
        return 'bg-yellow-50 text-yellow-700 border border-yellow-100';
      default:
        return 'bg-blue-50 text-blue-700 border border-blue-100';
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
          <h1 className="text-xl font-semibold text-gray-900">Security Findings</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Normalized, correlated vulnerability findings from static analysis, secret scans, and dependency audits.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
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
      <div className="rounded-xl bg-white border border-gray-200 overflow-hidden shadow-sm">
        <table className="w-full text-left text-xs">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Severity</th>
              <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Vulnerability Title</th>
              <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Scanner</th>
              <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
              <th className="py-3 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-gray-400">
                  No findings matching criteria
                </td>
              </tr>
            ) : (
              filtered.map((f) => (
                <tr key={f.id} className="hover:bg-gray-50 border-b border-gray-100 transition-colors">
                  <td className="py-3 px-4">
                    <span
                      className={`badge uppercase tracking-wider ${getSeverityBadge(f.severity)}`}
                    >
                      {f.severity}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="text-sm font-medium text-gray-900">{f.title}</div>
                    <div className="text-[10px] text-gray-400 font-mono mt-0.5">{f.rule_id}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="text-sm text-gray-600">{f.scanner_name}</span>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-gray-500">
                    {f.file_path}:{f.line_start ?? f.start_line ?? 1}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => setActiveFinding(f)}
                      className="px-3 py-1 rounded-lg bg-white hover:bg-gray-50 text-gray-600 border border-gray-200 text-xs mr-2 transition-colors"
                    >
                      Details
                    </button>
                    <button
                      onClick={() => handleStartInvestigation(f)}
                      className="px-3 py-1 rounded-lg bg-gray-900 hover:bg-gray-800 text-white text-xs transition-colors"
                    >
                      Investigate
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
        <div className="fixed inset-0 bg-black/20 backdrop-blur-sm flex justify-end z-50">
          <div className="w-full max-w-xl bg-white border-l border-gray-200 h-full p-6 flex flex-col justify-between overflow-y-auto">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-gray-100">
                <div>
                  <span
                    className={`badge uppercase ${getSeverityBadge(activeFinding.severity)}`}
                  >
                    {activeFinding.severity}
                  </span>
                  <h2 className="text-base font-semibold text-gray-900 mt-2">{activeFinding.title}</h2>
                </div>
                <button
                  onClick={() => setActiveFinding(null)}
                  className="p-1 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4 mt-6">
                <div>
                  <div className="text-xs font-medium text-gray-700 mb-1">Description</div>
                  <p className="text-xs text-gray-600 leading-relaxed">{activeFinding.description}</p>
                </div>

                <div>
                  <div className="text-xs font-medium text-gray-700 mb-1">Code Snippet</div>
                  <div className="p-3 bg-gray-50 rounded-xl border border-gray-200 font-mono text-xs text-gray-700 overflow-x-auto">
                    <pre>{activeFinding.code_snippet || activeFinding.snippet || 'No code preview available'}</pre>
                  </div>
                </div>

                <div>
                  <div className="text-xs font-medium text-gray-700 mb-1">Recommendation</div>
                  <p className="text-xs text-gray-700 bg-gray-50 p-3 rounded-xl border border-gray-200">
                    {activeFinding.recommendation || 'Apply parameterized execution or sanitized inputs.'}
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-gray-100 flex items-center justify-end gap-3">
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
                className="btn-primary"
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
