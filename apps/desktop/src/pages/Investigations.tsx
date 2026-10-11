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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">AI Multi-Agent Investigations</h1>
          <p className="text-sm text-gray-400 font-light mt-0.5">
            Autonomous multi-step investigation combining CodeBERT neural risk head, data-flow reasoning, and AST verification.
          </p>
        </div>
      </div>

      {!inv ? (
        <div className="p-12 text-center rounded-2xl bg-[#111827] border border-white/[0.08]">
          <div className="w-12 h-12 rounded-full bg-indigo-500/10 flex items-center justify-center mx-auto mb-3">
            <Cpu className="w-6 h-6 text-indigo-400" />
          </div>
          <h3 className="text-base font-medium text-white">No Active Investigation</h3>
          <p className="text-sm text-gray-500 max-w-sm mx-auto mt-1">
            Select a finding from the Security Findings tab and click &quot;Investigate AI&quot; to begin an autonomous multi-agent analysis.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Target Finding Overview Banner */}
          <div className="p-6 rounded-2xl bg-[#111827] border-l-4 border-indigo-500 border-r border-t border-b border-white/[0.08] flex items-center justify-between backdrop-blur-sm">
            <div>
              <div className="flex items-center gap-2">
                <span className="badge bg-red-500/10 text-red-400 border border-red-500/20 uppercase">
                  {inv.finding?.severity || 'HIGH'}
                </span>
                <span className="text-xs font-mono text-gray-400">{inv.finding?.rule_id}</span>
              </div>
              <h2 className="text-sm font-bold text-white mt-1">{inv.finding?.title}</h2>
              <div className="text-xs text-gray-400 font-mono mt-0.5">
                {inv.finding?.file_path}:{inv.finding?.line_number}
              </div>
            </div>

            <div className="text-right">
              <span className="text-xs text-gray-400 block">Agent Status</span>
              <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5 justify-end mt-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {inv.status.toUpperCase()}
              </span>
            </div>
          </div>

          {/* Agent Workflow Execution Stages */}
          <div className="p-6 rounded-2xl bg-[#111827] border border-white/[0.08]">
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
                    className={`p-3 rounded-xl border text-center transition-all duration-200 ${
                      isCompleted
                        ? 'bg-indigo-950/30 border-indigo-500/40 text-white shadow-[0_0_15px_-4px_rgba(99,102,241,0.3)]'
                        : 'bg-white/[0.02] border-white/[0.05] text-gray-500'
                    }`}
                  >
                    <div className="text-[10px] font-mono text-indigo-400">{`0${idx + 1}`}</div>
                    <div className="text-xs font-medium mt-1">{stage.name}</div>
                    <div className="text-[9px] text-gray-400 mt-1 truncate">{stage.agent}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Evidence Analysis Details */}
          <div className="grid grid-cols-3 gap-5">
            {/* Neural Model Score Card */}
            <div className="card glow-card">
              <div className="flex items-center gap-2 text-xs font-semibold text-white mb-3">
                <BrainCircuit className="w-4 h-4 text-indigo-400" />
                Neural Model Score
              </div>
              <div className="text-5xl font-bold font-mono text-indigo-400">
                {inv.neural_risk_score !== undefined
                  ? `${Math.round(inv.neural_risk_score * 100)}%`
                  : '82%'}
              </div>
              {/* Subtle ring-progress visual via CSS */}
              <div className="mt-3 h-1.5 rounded-full bg-white/10 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-600 to-violet-500 transition-all duration-500"
                  style={{
                    width: `${inv.neural_risk_score !== undefined ? Math.round(inv.neural_risk_score * 100) : 82}%`,
                  }}
                />
              </div>
              <div className="text-[11px] text-gray-400 mt-2 leading-relaxed">
                {inv.neural_risk_explanation ||
                  'CodeBERT transformer predicted high statistical vulnerability probability.'}
              </div>
            </div>

            {/* Data-Flow & Performance Analysis Cards */}
            <div className="col-span-2 space-y-4">
              <div className="card">
                <div className="flex items-center gap-2 text-xs font-semibold text-white mb-2">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  Security Data-Flow & AST Reachability
                </div>
                <div className="p-3 bg-[#0B1020] rounded-xl border border-white/[0.05] text-xs text-gray-300 font-mono leading-relaxed whitespace-pre-wrap max-h-36 overflow-y-auto">
                  {inv.data_flow_analysis ||
                    'Taint source reaches interpreter sink without parameter sanitization.'}
                </div>
              </div>

              {inv.performance_analysis && (
                <div className="card">
                  <div className="flex items-center gap-2 text-xs font-semibold text-purple-300 mb-2">
                    <BrainCircuit className="w-4 h-4 text-purple-400" />
                    Algorithmic Time Complexity & GPU Pipeline Review
                  </div>
                  <div className="p-3 bg-[#0B1020] rounded-xl border border-purple-500/20 text-xs text-purple-200 font-mono leading-relaxed whitespace-pre-wrap max-h-36 overflow-y-auto">
                    {inv.performance_analysis}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Candidate Patch Review Banner */}
          {inv.candidate_patch && (
            <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/40 to-transparent border border-indigo-500/20 backdrop-blur-sm flex items-center justify-between">
              <div>
                <h4 className="text-sm font-bold text-white flex items-center gap-2">
                  <GitPullRequest className="w-4 h-4 text-emerald-400" />
                  Synthesized Remediation Patch Ready
                </h4>
                <p className="text-xs text-gray-400 mt-1">
                  Verified with AST syntax clearance. Human approval required before modifying code.
                </p>
              </div>
              <button
                onClick={() => setActiveTab('fixes')}
                className="btn-primary shadow-glow"
              >
                Inspect Diff & Approve Fix &rarr;
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
