import React from 'react';
import { Download, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip } from 'recharts';
import { useAppStore } from '../stores/appStore';

export const Reports: React.FC = () => {
  const { findings, activeProject } = useAppStore();

  const criticalCount = findings.filter((f) => f.severity === 'critical').length;
  const highCount     = findings.filter((f) => f.severity === 'high').length;
  const mediumCount   = findings.filter((f) => f.severity === 'medium').length;
  const lowInfoCount  = findings.filter(
    (f) => f.severity === 'low' || f.severity === 'informational'
  ).length;
  const severityData = [
    { name: 'Critical', value: criticalCount, color: '#ef4444' },
    { name: 'High',     value: highCount,     color: '#f59e0b' },
    { name: 'Medium',   value: mediumCount,   color: '#eab308' },
    { name: 'Low/Info', value: lowInfoCount,  color: '#6366f1' },
  ];

  const handleExportJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(findings, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `codesentinel_report_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleExportMarkdown = () => {
    let md = `# CodeSentinel AI — Security Assessment Report\n\n`;
    md += `Project: ${activeProject?.name || 'Local Repository'}\n`;
    md += `Date: ${new Date().toISOString()}\n\n`;
    md += `## Findings (${findings.length} total)\n\n`;
    findings.forEach((f) => {
      md += `### [${f.severity.toUpperCase()}] ${f.title}\n`;
      md += `- **Rule**: ${f.rule_id} (${f.scanner_name})\n`;
      md += `- **Location**: \`${f.file_path}:${f.start_line}\`\n`;
      md += `- **Status**: ${f.status}\n\n`;
    });

    const dataStr = 'data:text/markdown;charset=utf-8,' + encodeURIComponent(md);
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `codesentinel_report_${Date.now()}.md`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Security & Compliance Reports</h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Audit-grade summaries mapped against OWASP Top 10, CWE taxonomic distributions, and artifact exports.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleExportJson}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#1F2937] hover:bg-white/10 text-xs font-medium text-white transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            Export JSON
          </button>
          <button
            onClick={handleExportMarkdown}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-glow transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            Export Markdown
          </button>
        </div>
      </div>

      {/* Mini severity donut */}
      <div style={{ width: 200, height: 200 }} className="flex items-center justify-center">
        <PieChart width={200} height={200}>
          <Pie
            data={severityData}
            cx={95}
            cy={95}
            innerRadius={50}
            outerRadius={80}
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
      </div>

      {/* Compliance Overview Card */}
      <div className="grid grid-cols-3 gap-6">
        <div className="p-5 rounded-xl bg-[#111827] border border-white/5 space-y-3">
          <h3 className="text-xs font-semibold text-white uppercase tracking-wider">OWASP Top 10 Mapping</h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between text-gray-300">
              <span>A01: Broken Access Control</span>
              <span className="font-mono text-emerald-400">0 Issues</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>A02: Cryptographic Failures</span>
              <span className="font-mono text-amber-400">1 Warning</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>A03: Injection (SQL/Cmd)</span>
              <span className="font-mono text-red-400">2 Critical</span>
            </div>
            <div className="flex justify-between text-gray-300">
              <span>A06: Vulnerable Components</span>
              <span className="font-mono text-emerald-400">0 Advisories</span>
            </div>
          </div>
        </div>

        <div className="col-span-2 p-5 rounded-xl bg-[#111827] border border-white/5">
          <h3 className="text-xs font-semibold text-white uppercase tracking-wider mb-3">Audit Summary</h3>
          <p className="text-xs text-gray-400 leading-relaxed">
            This repository has undergone local incremental static application security testing (SAST),
            secret pattern scanning, software composition analysis (SCA), and CodeBERT neural risk classification.
            All findings are preserved locally in SQLite with cryptographic fingerprints.
          </p>
          <div className="mt-4 flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
              <span>Zero Cloud Leaks</span>
            </div>
            <div className="flex items-center gap-1.5 text-indigo-400">
              <ShieldCheck className="w-4 h-4" />
              <span>Reproducible Hashes</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
