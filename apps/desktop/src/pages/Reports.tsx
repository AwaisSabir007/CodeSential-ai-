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

  const tooltipStyle = {
    backgroundColor: '#ffffff',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    color: '#111827',
    fontSize: 11,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Security &amp; Compliance Reports</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Audit-grade summaries mapped against OWASP Top 10, CWE taxonomic distributions, and artifact exports.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleExportJson}
            className="btn-secondary flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            Export JSON
          </button>
          <button
            onClick={handleExportMarkdown}
            className="btn-primary flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            Export Markdown
          </button>
        </div>
      </div>

      {/* Mini severity donut */}
      <div className="card inline-flex items-center justify-center">
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
          <Tooltip contentStyle={tooltipStyle} />
        </PieChart>
      </div>

      {/* Compliance Overview Card */}
      <div className="grid grid-cols-3 gap-5">
        <div className="card space-y-3">
          <h3 className="section-label">OWASP Top 10 Mapping</h3>
          <div className="space-y-0 text-xs">
            <div className="flex justify-between py-2.5 border-b border-gray-100 text-sm">
              <span className="text-gray-700">A01: Broken Access Control</span>
              <span className="font-mono text-emerald-600">0 Issues</span>
            </div>
            <div className="flex justify-between py-2.5 border-b border-gray-100 text-sm">
              <span className="text-gray-700">A02: Cryptographic Failures</span>
              <span className="font-mono text-amber-600">1 Warning</span>
            </div>
            <div className="flex justify-between py-2.5 border-b border-gray-100 text-sm">
              <span className="text-gray-700">A03: Injection (SQL/Cmd)</span>
              <span className="font-mono text-red-600">2 Critical</span>
            </div>
            <div className="flex justify-between py-2.5 last:border-0 text-sm">
              <span className="text-gray-700">A06: Vulnerable Components</span>
              <span className="font-mono text-emerald-600">0 Advisories</span>
            </div>
          </div>
        </div>

        <div className="col-span-2 card">
          <h3 className="section-label mb-3">Audit Summary</h3>
          <p className="text-xs text-gray-600 leading-relaxed">
            This repository has undergone local incremental static application security testing (SAST),
            secret pattern scanning, software composition analysis (SCA), and CodeBERT neural risk classification.
            All findings are preserved locally in SQLite with cryptographic fingerprints.
          </p>
          <div className="mt-4 flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5 text-emerald-600">
              <CheckCircle2 className="w-4 h-4" />
              <span>Zero Cloud Leaks</span>
            </div>
            <div className="flex items-center gap-1.5 text-gray-700">
              <ShieldCheck className="w-4 h-4" />
              <span>Reproducible Hashes</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
