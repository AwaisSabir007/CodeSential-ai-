import React, { useEffect, useState } from 'react';
import {
  GitPullRequest,
  Check,
  X,
  RotateCcw,
  ShieldCheck,
  FileCode,
  RefreshCw,
  AlertCircle,
  ArrowRight,
} from 'lucide-react';
import { useAppStore } from '../stores/appStore';
import { api } from '../services/api';

interface PatchItem {
  patch_id: string;
  finding_id: string;
  file_path: string;
  original_code: string;
  modified_code: string;
  diff: {
    unified_diff: string;
    additions: number;
    deletions: number;
  };
  explanation: string;
  status: string;
}

export const ProposedFixes: React.FC = () => {
  const { activeInvestigation, setActiveTab } = useAppStore();
  const [patches, setPatches] = useState<PatchItem[]>([]);
  const [selectedPatch, setSelectedPatch] = useState<PatchItem | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [appliedBackup, setAppliedBackup] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadPatches = async () => {
    setIsLoading(true);
    try {
      const res = await api.getPatches();
      setPatches(res || []);
      if (res && res.length > 0) {
        setSelectedPatch(res[0]);
      } else {
        setSelectedPatch(null);
      }
    } catch (err) {
      console.warn('Failed to load patches:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPatches();
  }, [activeInvestigation?.investigation_id]);

  const handleApprove = async () => {
    if (!selectedPatch || isLoading) return;
    // Already applied — nothing to do
    if (selectedPatch.status === 'applied') return;
    setIsLoading(true);
    try {
      const res = await api.approvePatch(selectedPatch.patch_id, true);
      setSelectedPatch((prev) => (prev ? { ...prev, status: res.status ?? 'applied' } : null));
      if (res.backup_path) {
        setAppliedBackup(res.backup_path);
      }
      setActionMessage('Patch successfully applied to source file with safety backup created.');
      await loadPatches();
    } catch (err: any) {
      alert(`Failed to apply patch: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRollback = async () => {
    if (!selectedPatch) return;
    try {
      await api.rollbackPatch(selectedPatch.patch_id);
      setSelectedPatch((prev) => (prev ? { ...prev, status: 'verified' } : null));
      setAppliedBackup(null);
      setActionMessage('Source file restored to original state from backup.');
      await loadPatches();
    } catch (err: any) {
      alert(`Rollback failed: ${err.message}`);
    }
  };

  const handleReject = async () => {
    if (!selectedPatch) return;
    try {
      await api.rejectPatch(selectedPatch.patch_id);
      setSelectedPatch((prev) => (prev ? { ...prev, status: 'rejected' } : null));
      setActionMessage('Patch proposal rejected.');
      await loadPatches();
    } catch (err: any) {
      alert(`Reject failed: ${err.message}`);
    }
  };

  // If active investigation produced a patch, generate Diff preview if not already cached
  const invPatch = activeInvestigation?.candidate_patch;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Proposed Code Remediation</h1>
          <p className="text-sm text-gray-400 font-light mt-0.5">
            Non-negotiable human review gate: inspect unified diff and syntax verification before applying changes.
          </p>
        </div>
        <button
          onClick={loadPatches}
          disabled={isLoading}
          className="btn-secondary flex items-center gap-2 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Patches
        </button>
      </div>

      {actionMessage && (
        <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/30 text-xs text-indigo-300 flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-gray-400 hover:text-white rounded-full">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Container */}
      {patches.length === 0 && !invPatch ? (
        <div className="p-12 text-center rounded-2xl bg-[#111827] border border-white/[0.08] space-y-3">
          <div className="w-12 h-12 rounded-full bg-indigo-500/10 flex items-center justify-center mx-auto">
            <GitPullRequest className="w-6 h-6 text-gray-400" />
          </div>
          <h3 className="text-base font-medium text-white">No Pending Remediation Patches</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            Remediation patches are automatically generated when you launch an AI investigation on any security finding or performance hotspot.
          </p>
          <button
            onClick={() => setActiveTab('findings')}
            className="btn-primary shadow-glow inline-flex items-center gap-1.5"
          >
            <span>View Security Findings</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-12 gap-6">
          {/* Patch Selector List */}
          <div className="col-span-4 space-y-2">
            <div className="section-label mb-2">
              Available Candidate Patches ({patches.length})
            </div>
            {patches.map((p) => (
              <div
                key={p.patch_id}
                onClick={() => setSelectedPatch(p)}
                className={`p-3 rounded-xl border cursor-pointer transition-all duration-200 ${
                  selectedPatch?.patch_id === p.patch_id
                    ? 'bg-indigo-950/30 border-indigo-500/50 ring-1 ring-indigo-500/50 shadow-glow'
                    : 'bg-[#111827] border-white/[0.08] hover:border-white/15'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-white truncate max-w-[180px]">
                    {p.file_path}
                  </span>
                  <span
                    className={`badge border text-[10px] font-semibold uppercase ${
                      p.status === 'applied'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        : p.status === 'rejected'
                        ? 'bg-red-500/10 text-red-400 border-red-500/20'
                        : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                    }`}
                  >
                    {p.status}
                  </span>
                </div>
                <div className="text-[11px] text-gray-400 mt-1 line-clamp-1">
                  +{p.diff?.additions || 0} / -{p.diff?.deletions || 0} lines
                </div>
              </div>
            ))}
          </div>

          {/* Active Patch Details Box */}
          <div className="col-span-8">
            {selectedPatch ? (
              <div className="p-6 rounded-2xl bg-[#111827] border border-white/[0.08] space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-white/[0.05]">
                  <div className="flex items-center gap-2">
                    <FileCode className="w-4 h-4 text-indigo-400" />
                    <span className="text-xs font-mono font-bold text-white">{selectedPatch.file_path}</span>
                    <span className="badge bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3" />
                      AST Syntax Validated
                    </span>
                  </div>

                  <span className="text-xs font-mono text-gray-400">
                    Status: <span className="text-indigo-400 font-bold uppercase">{selectedPatch.status}</span>
                  </span>
                </div>

                {/* Diff Content Preview */}
                <div className="p-4 bg-[#0B1020] rounded-2xl border border-white/[0.05] font-mono text-xs overflow-x-auto leading-relaxed max-h-[380px] overflow-y-auto">
                  {(selectedPatch.diff?.unified_diff || selectedPatch.modified_code)
                    .split('\n')
                    .map((line, idx) => {
                      const isAdd = line.startsWith('+') && !line.startsWith('+++');
                      const isDel = line.startsWith('-') && !line.startsWith('---');
                      const isHeader =
                        line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++');

                      return (
                        <div
                          key={idx}
                          className={`${
                            isAdd
                              ? 'bg-emerald-950/40 text-emerald-300'
                              : isDel
                              ? 'bg-red-950/40 text-red-300'
                              : isHeader
                              ? 'text-indigo-400 font-bold'
                              : 'text-gray-300'
                          } px-2 py-0.5 rounded`}
                        >
                          {line}
                        </div>
                      );
                    })}
                </div>

                {/* Explanation */}
                <div className="p-3 bg-white/[0.03] rounded-xl border border-white/[0.08] text-xs text-gray-300 space-y-1">
                  <div className="font-semibold text-white">Correction Rationale:</div>
                  <p className="text-gray-400 leading-relaxed whitespace-pre-line">
                    {selectedPatch.explanation}
                  </p>
                </div>

                {/* Action Controls */}
                <div className="pt-2 flex items-center justify-between">
                  <div className="text-[11px] text-gray-400">
                    {appliedBackup && (
                      <span className="text-emerald-400">
                        &bull; Backup saved at: <span className="font-mono">{appliedBackup}</span>
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3">
                    {selectedPatch.status === 'applied' ? (
                      <button
                        onClick={handleRollback}
                        className="btn-secondary flex items-center gap-1.5 hover:text-amber-400"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Rollback to Original
                      </button>
                    ) : selectedPatch.status === 'rejected' ? (
                      <span className="text-xs text-gray-500 italic">Patch rejected — no further actions</span>
                    ) : (
                      <>
                        <button
                          onClick={handleReject}
                          className="btn-secondary flex items-center gap-1.5 hover:text-red-400"
                        >
                          <X className="w-3.5 h-3.5" />
                          Reject Proposal
                        </button>
                        <button
                          onClick={handleApprove}
                          disabled={isLoading}
                          className="rounded-full bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium px-5 py-2 flex items-center gap-1.5 shadow-glow-success transition-all duration-200 active:scale-95 disabled:opacity-50"
                        >
                          <Check className="w-3.5 h-3.5" />
                          Approve & Apply Patch
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
