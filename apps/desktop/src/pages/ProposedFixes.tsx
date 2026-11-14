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

  const invPatch = activeInvestigation?.candidate_patch;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Proposed Code Remediation</h1>
          <p className="text-sm text-gray-500 mt-0.5">
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
        <div className="p-3 rounded-lg bg-blue-50 border border-blue-100 text-xs text-blue-700 flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="text-blue-400 hover:text-blue-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Container */}
      {patches.length === 0 && !invPatch ? (
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mx-auto">
            <GitPullRequest className="w-6 h-6 text-gray-400" />
          </div>
          <h3 className="text-base font-medium text-gray-900">No Pending Remediation Patches</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto">
            Remediation patches are automatically generated when you launch an AI investigation on any security finding or performance hotspot.
          </p>
          <button
            onClick={() => setActiveTab('findings')}
            className="btn-primary inline-flex items-center gap-1.5"
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
                className={`p-3 rounded-xl border cursor-pointer transition-colors ${
                  selectedPatch?.patch_id === p.patch_id
                    ? 'bg-white border-gray-900 shadow-sm'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-semibold text-gray-900 truncate max-w-[180px]">
                    {p.file_path}
                  </span>
                  <span
                    className={`badge text-[10px] border ${
                      p.status === 'applied'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-100'
                        : p.status === 'rejected'
                        ? 'bg-red-50 text-red-700 border-red-100'
                        : 'bg-gray-100 text-gray-600 border-gray-200'
                    }`}
                  >
                    {p.status}
                  </span>
                </div>
                <div className="text-[11px] text-gray-500 mt-1">
                  +{p.diff?.additions || 0} / -{p.diff?.deletions || 0} lines
                </div>
              </div>
            ))}
          </div>

          {/* Active Patch Details Box */}
          <div className="col-span-8">
            {selectedPatch ? (
              <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                  <div className="flex items-center gap-2">
                    <FileCode className="w-4 h-4 text-gray-400" />
                    <span className="text-xs font-mono font-semibold text-gray-900">{selectedPatch.file_path}</span>
                    <span className="badge bg-emerald-50 text-emerald-700 border border-emerald-100 flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3 text-emerald-600" />
                      AST Syntax Validated
                    </span>
                  </div>
                  <span className="text-xs font-mono text-gray-500">
                    Status: <span className="text-gray-900 font-semibold uppercase">{selectedPatch.status}</span>
                  </span>
                </div>

                {/* Diff Content Preview */}
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-xl font-mono text-xs overflow-x-auto leading-relaxed max-h-[380px] overflow-y-auto">
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
                              ? 'bg-emerald-50 text-emerald-800'
                              : isDel
                              ? 'bg-red-50 text-red-800'
                              : isHeader
                              ? 'text-gray-500 font-medium'
                              : 'text-gray-700'
                          } px-2 py-0.5 rounded`}
                        >
                          {line}
                        </div>
                      );
                    })}
                </div>

                {/* Explanation */}
                <div className="p-3 bg-gray-50 rounded-xl border border-gray-100 text-xs text-gray-600 space-y-1">
                  <div className="font-semibold text-gray-900">Correction Rationale:</div>
                  <p className="leading-relaxed whitespace-pre-line">
                    {selectedPatch.explanation}
                  </p>
                </div>

                {/* Action Controls */}
                <div className="pt-2 flex items-center justify-between">
                  <div className="text-[11px] text-gray-400">
                    {appliedBackup && (
                      <span>
                        &bull; Backup saved at: <span className="font-mono text-emerald-600">{appliedBackup}</span>
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3">
                    {selectedPatch.status === 'applied' ? (
                      <button
                        onClick={handleRollback}
                        className="btn-secondary flex items-center gap-1.5"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        Rollback to Original
                      </button>
                    ) : selectedPatch.status === 'rejected' ? (
                      <span className="text-xs text-gray-400 italic">Patch rejected — no further actions</span>
                    ) : (
                      <>
                        <button
                          onClick={handleReject}
                          className="btn-secondary flex items-center gap-1.5"
                        >
                          <X className="w-3.5 h-3.5" />
                          Reject Proposal
                        </button>
                        <button
                          onClick={handleApprove}
                          disabled={isLoading}
                          className="bg-gray-900 hover:bg-gray-800 text-white rounded-lg text-xs font-medium px-5 py-2 flex items-center gap-1.5 transition-colors disabled:opacity-50"
                        >
                          <Check className="w-3.5 h-3.5" />
                          Approve &amp; Apply Patch
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
