import React, { useEffect, useState } from 'react';
import {
  Zap,
  Cpu,
  Layers,
  CheckCircle,
  TrendingUp,
  RefreshCw,
  HardDrive,
  Activity,
  ArrowRight,
  Flame,
} from 'lucide-react';
import { useAppStore } from '../stores/appStore';
import { api } from '../services/api';

interface Hotspot {
  function: string;
  file: string;
  file_path: string;
  line_start: number;
  line_end: number;
  cyclomatic: number;
  loop_depth: number;
  time_complexity: string;
  space_complexity: string;
  category: string;
  severity: string;
  issue: string;
  optimization: string;
  before_code: string;
  after_code: string;
  hardware_impact: string;
}

interface OptimizationData {
  project_id: string;
  total_files_analyzed: number;
  total_functions_analyzed: number;
  average_cyclomatic_complexity: number;
  maintainability_index: number;
  time_complexity_distribution: Record<string, number>;
  gpu_optimization_count: number;
  hotspots: Hotspot[];
}

export const Optimization: React.FC = () => {
  const { activeProject, setActiveTab, setActiveInvestigation } = useAppStore();
  const [data, setData] = useState<OptimizationData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot | null>(null);

  const loadOptimization = async () => {
    if (!activeProject) return;
    setIsLoading(true);
    try {
      const res = await api.getProjectOptimization(activeProject.id);
      setData(res);
      if (res.hotspots && res.hotspots.length > 0) {
        setSelectedHotspot(res.hotspots[0]);
      } else {
        setSelectedHotspot(null);
      }
    } catch (err) {
      console.warn('Failed to load project optimization:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadOptimization();
  }, [activeProject?.id]);

  const handleInvestigateHotspot = async (hs: Hotspot) => {
    if (!activeProject) return;
    try {
      const inv = await api.triggerInvestigation({
        project_id: activeProject.id,
        finding_id: `perf_${hs.function}_${hs.line_start}`,
        scanner_name: 'complexity',
        rule_id: `PERF_${hs.category.toUpperCase()}`,
        category: hs.category,
        severity: hs.severity,
        file_path: hs.file_path,
        line_number: hs.line_start,
        snippet: hs.before_code || hs.function,
        title: `[${hs.time_complexity}] ${hs.issue.split('.')[0]}`,
        description: `${hs.issue}\n\nHardware Impact: ${hs.hardware_impact}`,
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
          <h1 className="text-2xl font-semibold text-white tracking-tight">
            Code Optimization, Algorithmic & GPU Analysis
          </h1>
          <p className="text-sm text-gray-400 font-light mt-0.5">
            Real-time AST time complexity analysis, space efficiency, memory allocations, and PyTorch / GPU hardware bottlenecks.
          </p>
        </div>
        <button
          onClick={loadOptimization}
          disabled={isLoading}
          className="btn-secondary flex items-center gap-2 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Analyze Project
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-4 gap-5">
        <div className="card glow-card hover:scale-[1.01]">
          <div className="text-xs text-gray-400 flex items-center justify-between">
            <span className="section-label">Average Cyclomatic CC</span>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-xl font-semibold text-white font-mono mt-2">
            {data ? `${data.average_cyclomatic_complexity}` : '---'}
          </div>
          <div className="text-[10px] text-gray-400 mt-1">
            {data && data.average_cyclomatic_complexity <= 5
              ? 'Low Branching Risk'
              : data && data.average_cyclomatic_complexity <= 10
              ? 'Moderate Risk'
              : 'High Complexity Hotspots'}
          </div>
        </div>

        <div className="card glow-card hover:scale-[1.01]">
          <div className="text-xs text-gray-400 flex items-center justify-between">
            <span className="section-label">Maintainability Index</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-xl font-semibold text-emerald-400 font-mono mt-2">
            {data ? `${data.maintainability_index} / 100` : '---'}
          </div>
          <div className="text-[10px] text-gray-400 mt-1">
            {data && data.maintainability_index >= 70
              ? 'Grade A (Highly Maintainable)'
              : 'Grade B (Refactoring Recommended)'}
          </div>
        </div>

        <div className="card glow-card hover:scale-[1.01]">
          <div className="text-xs text-gray-400 flex items-center justify-between">
            <span className="section-label">Complexity Hotspots</span>
            <Flame className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-xl font-semibold text-amber-400 font-mono mt-2">
            {data ? `${data.hotspots.length} Detected` : '---'}
          </div>
          <div className="text-[10px] text-gray-400 mt-1">
            Across {data?.total_functions_analyzed || 0} functions in {data?.total_files_analyzed || 0} files
          </div>
        </div>

        <div className="card glow-card hover:scale-[1.01]">
          <div className="text-xs text-gray-400 flex items-center justify-between">
            <span className="section-label">GPU / Deep Learning</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-xl font-semibold text-purple-400 font-mono mt-2">
            {data ? `${data.gpu_optimization_count} Targets` : '---'}
          </div>
          <div className="text-[10px] text-gray-400 mt-1">
            CUDA / PyTorch tensor & pipeline optimizations
          </div>
        </div>
      </div>

      {/* Time Complexity Distribution Banner */}
      {data && (
        <div className="p-6 rounded-2xl bg-[#111827] border border-white/[0.08] backdrop-blur-sm">
          <div className="section-label mb-3">
            Algorithmic Time Complexity Profile
          </div>
          <div className="grid grid-cols-5 gap-3 font-mono text-center">
            {Object.entries(data.time_complexity_distribution || {}).map(([key, count]) => {
              const isHigh = key.includes('N^2') || key.includes('N^3') || key.includes('2^N');
              return (
                <div
                  key={key}
                  className={`p-2.5 rounded-lg border ${
                    isHigh && count > 0
                      ? 'bg-amber-950/20 border-amber-500/30 text-amber-300'
                      : 'bg-white/[0.02] border-white/[0.05] text-gray-300'
                  }`}
                >
                  <div className="text-xs font-bold">{key}</div>
                  <div className="text-sm font-semibold mt-0.5">{count} functions</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Main Hotspots Section */}
      <div className="grid grid-cols-12 gap-6">
        {/* Hotspots List */}
        <div className="col-span-5 space-y-3">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            Detected Hotspots ({data?.hotspots.length || 0})
          </h2>

          {!data || data.hotspots.length === 0 ? (
            <div className="p-8 text-center rounded-2xl bg-[#111827] border border-white/[0.08]">
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-2">
                <CheckCircle className="w-6 h-6 text-emerald-400" />
              </div>
              <div className="text-base font-medium text-white">Optimal Performance</div>
              <p className="text-sm text-gray-500 mt-1">
                No high cyclomatic complexity, quadratic iterations, or GPU bottleneck patterns detected.
              </p>
            </div>
          ) : (
            data.hotspots.map((hs, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedHotspot(hs)}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all duration-200 ${
                  selectedHotspot === hs
                    ? 'bg-indigo-950/30 border-indigo-500/50 shadow-glow'
                    : 'bg-[#111827] border-white/[0.08] hover:border-white/15'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-white">{hs.function}</span>
                  <span
                    className={`badge border text-[10px] font-semibold uppercase ${
                      hs.category === 'gpu_optimization'
                        ? 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                        : hs.severity === 'high'
                        ? 'bg-red-500/10 text-red-400 border-red-500/20'
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                    }`}
                  >
                    {hs.time_complexity}
                  </span>
                </div>
                <div className="text-[11px] text-gray-400 font-mono mt-1">{hs.file}</div>
                <p className="text-xs text-gray-300 mt-2 line-clamp-2">{hs.issue}</p>
              </div>
            ))
          )}
        </div>

        {/* Selected Hotspot Deep Dive Panel */}
        <div className="col-span-7">
          {selectedHotspot ? (
            <div className="p-6 rounded-2xl bg-[#111827] border border-white/[0.08] space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.05]">
                <div>
                  <h3 className="text-sm font-bold text-white font-mono">{selectedHotspot.function}</h3>
                  <div className="text-xs text-gray-400 font-mono mt-0.5">{selectedHotspot.file}</div>
                </div>
                <button
                  onClick={() => handleInvestigateHotspot(selectedHotspot)}
                  className="btn-primary shadow-glow"
                >
                  Investigate AI
                </button>
              </div>

              {/* Badges Bar */}
              <div className="flex items-center gap-2 flex-wrap text-[11px]">
                <span className="px-2.5 py-1 rounded bg-white/[0.05] text-gray-300 border border-white/[0.08] font-mono">
                  Time: <strong className="text-amber-400">{selectedHotspot.time_complexity}</strong>
                </span>
                <span className="px-2.5 py-1 rounded bg-white/[0.05] text-gray-300 border border-white/[0.08] font-mono">
                  Space: <strong className="text-indigo-400">{selectedHotspot.space_complexity}</strong>
                </span>
                <span className="px-2.5 py-1 rounded bg-white/[0.05] text-gray-300 border border-white/[0.08] font-mono">
                  Cyclomatic CC: <strong>{selectedHotspot.cyclomatic}</strong>
                </span>
              </div>

              {/* Issue & Hardware Impact */}
              <div className="space-y-2">
                <div className="text-xs text-gray-300 leading-relaxed bg-white/[0.03] p-3 rounded-lg border border-white/[0.05]">
                  <strong className="text-white block mb-1">Issue Diagnosis:</strong>
                  {selectedHotspot.issue}
                </div>

                {selectedHotspot.hardware_impact && (
                  <div className="text-xs text-purple-300 leading-relaxed bg-purple-950/20 p-3 rounded-lg border border-purple-500/20">
                    <strong className="text-purple-200 block mb-1 flex items-center gap-1.5">
                      <Cpu className="w-3.5 h-3.5 text-purple-400" />
                      Hardware / GPU Architecture Impact:
                    </strong>
                    {selectedHotspot.hardware_impact}
                  </div>
                )}
              </div>

              {/* Before & After Refactoring Code Preview */}
              <div className="space-y-3">
                <div className="text-xs font-semibold text-gray-300">Recommended Code Refactor</div>

                {selectedHotspot.after_code && (
                  <div>
                    <div className="text-[10px] text-emerald-400 font-semibold mb-1 uppercase tracking-wider">
                      Optimized Replacement (Drop-in):
                    </div>
                    <pre className="p-3 bg-[#0B1020] rounded-lg border border-emerald-500/30 font-mono text-xs text-emerald-300 overflow-x-auto">
                      {selectedHotspot.after_code}
                    </pre>
                  </div>
                )}

                <div className="text-xs text-indigo-300 bg-indigo-950/20 p-3 rounded-lg border border-indigo-500/20 flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="block text-white mb-0.5">Engineering Rationale:</strong>
                    {selectedHotspot.optimization}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center rounded-2xl bg-[#111827] border border-white/[0.08] text-gray-500 text-xs">
              Select a hotspot on the left to inspect time complexity, space usage, and hardware acceleration diffs.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
