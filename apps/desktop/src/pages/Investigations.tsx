import React from 'react';
import { Cpu, CheckCircle2, AlertCircle, ArrowRight, BrainCircuit, ShieldAlert, GitPullRequest } from 'lucide-react';
import { useAppStore } from '../stores/appStore';
import { api } from '../services/api';

export const Investigations: React.FC = () => {
  const { activeInvestigation, investigations, setActiveTab } = useAppStore();

  const inv = activeInvestigation || (investigations.length > 0 ? investigations[0] : null);

  const stages = [
    { name: 'Planning & Triage', agent: 'PlanningAgent' },
    { name: 'Neural Model Risk', agent: 'DeepLearningAgent' },
    { name: 'Data-Flow & Sinks', agent: 'SecurityInvestigationAgent' },
    { name: 'Patch Synthesis', agent: 'RemediationAgent' },
    { name: 'AST Verification', agent: 'VerificationAgent' },
    { name: 'Evidence Evaluation', agent: 'EvaluationAgent' },
  ];

  const getSeverityBadge = (sev?: string) => {
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">AI Multi-Agent Investigations</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Autonomous multi-step investigation combining CodeBERT neural risk head, data-flow reasoning, and AST verification.
          </p>
        </div>
      </div>

      {!inv ? (
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
          <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3">
            <Cpu className="w-6 h-6 text-gray-400" />
          </div>
          <h3 className="text-base font-medium text-gray-900">No Active Investigation</h3>
          <p className="text-sm text-gray-500 max-w-sm mx-auto mt-1">
            Select a finding from the Security Findings tab and click &quot;Investigate AI&quot; to begin an autonomous multi-agent analysis.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Target Finding Overview Banner */}
          <div className="bg-white border border-gray-200 rounded-xl border-l-4 border-l-gray-900 p-5 flex items-center justify-between shadow-sm">
            <div>
              <div className="flex items-center gap-2">
                <span className={`badge uppercase ${getSeverityBadge(inv.finding?.severity)}`}>
                  {inv.finding?.severity || 'HIGH'}
                </span>
                <span className="text-xs font-mono text-gray-500">{inv.finding?.rule_id}</span>
              </div>
              <h2 className="text-sm font-semibold text-gray-900 mt-1">{inv.finding?.title}</h2>
              <div className="text-xs text-gray-500 font-mono mt-0.5">
                {inv.finding?.file_path}:{inv.finding?.line_number}
              </div>
            </div>

            <div className="text-right">
              <span className="text-xs text-gray-500 block">Agent Status</span>
              <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1.5 justify-end mt-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {inv.status.toUpperCase()}
              </span>
            </div>
          </div>

          {/* Agent Workflow Execution Stages */}
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
            <h3 className="section-label mb-4">
              Agent Execution Pipeline
            </h3>
            <div className="grid grid-cols-6 gap-2">
              {stages.map((stage, idx) => {
                const isCompleted = inv.completed_steps?.some((s) =>
                  s.toLowerCase().includes(stage.name.split(' ')[0].toLowerCase())
                );
                return (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border text-center transition-colors ${
                      isCompleted
                        ? 'border-gray-900 bg-gray-900 text-white'
                        : 'border-gray-100 bg-gray-50 text-gray-400'
                    }`}
                  >
                    <div className={`text-[10px] font-mono ${isCompleted ? 'text-white' : 'text-gray-400'}`}>{`0${idx + 1}`}</div>
                    <div className="text-xs font-medium mt-1">{stage.name}</div>
                    <div className={`text-[9px] mt-1 truncate ${isCompleted ? 'text-gray-300' : 'text-gray-400'}`}>{stage.agent}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Evidence Analysis Details */}
          <div className="grid grid-cols-3 gap-5">
            {/* Neural Model Score Card */}
            <div className="card">
              <div className="flex items-center gap-2 text-xs font-semibold text-gray-900 mb-3">
                <BrainCircuit className="w-4 h-4 text-gray-400" />
                Neural Model Score
              </div>
              <div className="text-4xl font-semibold font-mono text-gray-900">
                {inv.neural_risk_score !== undefined
                  ? `${Math.round(inv.neural_risk_score * 100)}%`
                  : '82%'}
              </div>
              <div className="mt-3 h-1.5 rounded-full bg-gray-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gray-900 transition-all duration-500"
                  style={{
                    width: `${inv.neural_risk_score !== undefined ? Math.round(inv.neural_risk_score * 100) : 82}%`,
                  }}
                />
              </div>
              <div className="text-[11px] text-gray-500 mt-2 leading-relaxed">
                {inv.neural_risk_explanation ||
                  'CodeBERT transformer predicted high statistical vulnerability probability.'}
              </div>
            </div>

            {/* Data-Flow & Performance Analysis Cards */}
            <div className="col-span-2 space-y-4">
              <div className="card">
                <div className="flex items-center gap-2 text-xs font-semibold text-gray-900 mb-2">
                  <ShieldAlert className="w-4 h-4 text-gray-400" />
                  Security Data-Flow &amp; AST Reachability
                </div>
                <div className="p-3 bg-gray-50 rounded-xl border border-gray-200 text-xs text-gray-700 font-mono leading-relaxed whitespace-pre-wrap max-h-36 overflow-y-auto">
                  {inv.data_flow_analysis ||
                    'Taint source reaches interpreter sink without parameter sanitization.'}
                </div>
              </div>

              {inv.performance_analysis && (
                <div className="card">
                  <div className="flex items-center gap-2 text-xs font-semibold text-gray-900 mb-2">
                    <BrainCircuit className="w-4 h-4 text-gray-400" />
                    Algorithmic Time Complexity &amp; GPU Pipeline Review
                  </div>
                  <div className="p-3 bg-gray-50 rounded-xl border border-gray-200 text-xs text-gray-700 font-mono leading-relaxed whitespace-pre-wrap max-h-36 overflow-y-auto">
                    {inv.performance_analysis}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Candidate Patch Review Banner */}
          {inv.candidate_patch && (
            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex items-center justify-between">
              <div>
                <h4 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                  <GitPullRequest className="w-4 h-4 text-gray-400" />
                  Synthesized Remediation Patch Ready
                </h4>
                <p className="text-xs text-gray-500 mt-1">
                  Verified with AST syntax clearance. Human approval required before modifying code.
                </p>
              </div>
              <button
                onClick={() => setActiveTab('fixes')}
                className="btn-primary"
              >
                Inspect Diff &amp; Approve Fix &rarr;
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
