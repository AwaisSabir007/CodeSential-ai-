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
          <h1 className="text-xl font-semibold text-gray-900">
            Code Optimization, Algorithmic &amp; GPU Analysis
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
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
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:border-gray-300 transition-colors">
          <div className="flex items-center justify-between">
            <span className="section-label">Average Cyclomatic CC</span>
            <Activity className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-xl font-semibold text-gray-900 font-mono mt-2">
            {data ? `${data.average_cyclomatic_complexity}` : '---'}
          </div>
          <div className="text-[10px] text-gray-500 mt-1">
            {data && data.average_cyclomatic_complexity <= 5
              ? 'Low Branching Risk'
              : data && data.average_cyclomatic_complexity <= 10
              ? 'Moderate Risk'
              : 'High Complexity Hotspots'}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:border-gray-300 transition-colors">
          <div className="flex items-center justify-between">
            <span className="section-label">Maintainability Index</span>
            <TrendingUp className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-xl font-semibold text-gray-900 font-mono mt-2">
            {data ? `${data.maintainability_index} / 100` : '---'}
          </div>
          <div className="text-[10px] text-gray-500 mt-1">
            {data && data.maintainability_index >= 70
              ? 'Grade A (Highly Maintainable)'
              : 'Grade B (Refactoring Recommended)'}
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:border-gray-300 transition-colors">
          <div className="flex items-center justify-between">
            <span className="section-label">Complexity Hotspots</span>
            <Flame className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-xl font-semibold text-gray-900 font-mono mt-2">
            {data ? `${data.hotspots.length} Detected` : '---'}
          </div>
          <div className="text-[10px] text-gray-500 mt-1">
            Across {data?.total_functions_analyzed || 0} functions in {data?.total_files_analyzed || 0} files
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:border-gray-300 transition-colors">
          <div className="flex items-center justify-between">
            <span className="section-label">GPU / Deep Learning</span>
            <Cpu className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-xl font-semibold text-gray-900 font-mono mt-2">
            {data ? `${data.gpu_optimization_count} Targets` : '---'}
          </div>
          <div className="text-[10px] text-gray-500 mt-1">
            CUDA / PyTorch tensor &amp; pipeline optimizations
          </div>
        </div>
      </div>

      {/* Time Complexity Distribution Banner */}
      {data && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
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
                      ? 'bg-amber-50 border-amber-100 text-amber-700'
                      : 'bg-gray-50 border-gray-100 text-gray-700'
                  }`}
                >
                  <div className="text-xs font-semibold">{key}</div>
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
          <h2 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <Zap className="w-4 h-4 text-gray-400" />
            Detected Hotspots ({data?.hotspots.length || 0})
          </h2>

          {!data || data.hotspots.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
              <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-2">
                <CheckCircle className="w-6 h-6 text-gray-400" />
              </div>
              <div className="text-base font-medium text-gray-900">Optimal Performance</div>
              <p className="text-sm text-gray-500 mt-1">
                No high cyclomatic complexity, quadratic iterations, or GPU bottleneck patterns detected.
              </p>
            </div>
          ) : (
            data.hotspots.map((hs, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedHotspot(hs)}
                className={`p-3.5 rounded-xl border cursor-pointer transition-colors ${
                  selectedHotspot === hs
                    ? 'bg-white border-gray-900 shadow-sm'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-semibold text-gray-900">{hs.function}</span>
                  <span
                    className={`badge text-[10px] border ${
                      hs.category === 'gpu_optimization'
                        ? 'bg-purple-50 text-purple-700 border-purple-100'
                        : hs.severity === 'high'
                        ? 'bg-red-50 text-red-700 border-red-100'
                        : 'bg-amber-50 text-amber-700 border-amber-100'
                    }`}
                  >
                    {hs.time_complexity}
                  </span>
                </div>
                <div className="text-[11px] text-gray-500 font-mono mt-1">{hs.file}</div>
                <p className="text-xs text-gray-600 mt-2 line-clamp-2">{hs.issue}</p>
              </div>
            ))
          )}
        </div>

        {/* Selected Hotspot Deep Dive Panel */}
        <div className="col-span-7">
          {selectedHotspot ? (
            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 font-mono">{selectedHotspot.function}</h3>
                  <div className="text-xs text-gray-500 font-mono mt-0.5">{selectedHotspot.file}</div>
                </div>
                <button
                  onClick={() => handleInvestigateHotspot(selectedHotspot)}
                  className="btn-primary"
                >
                  Investigate AI
                </button>
              </div>

              {/* Badges Bar */}
              <div className="flex items-center gap-2 flex-wrap text-[11px]">
                <span className="px-2.5 py-1 rounded-lg bg-gray-50 text-gray-700 border border-gray-100 font-mono">
                  Time: <strong className="text-amber-600">{selectedHotspot.time_complexity}</strong>
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-gray-50 text-gray-700 border border-gray-100 font-mono">
                  Space: <strong className="text-gray-900">{selectedHotspot.space_complexity}</strong>
                </span>
                <span className="px-2.5 py-1 rounded-lg bg-gray-50 text-gray-700 border border-gray-100 font-mono">
                  Cyclomatic CC: <strong>{selectedHotspot.cyclomatic}</strong>
                </span>
              </div>

              {/* Issue & Hardware Impact */}
              <div className="space-y-2">
                <div className="text-xs text-gray-600 leading-relaxed bg-gray-50 p-3 rounded-lg border border-gray-100">
                  <strong className="text-gray-900 block mb-1">Issue Diagnosis:</strong>
                  {selectedHotspot.issue}
                </div>

                {selectedHotspot.hardware_impact && (
                  <div className="text-xs text-gray-600 leading-relaxed bg-purple-50 p-3 rounded-lg border border-purple-100">
                    <strong className="text-gray-900 block mb-1 flex items-center gap-1.5">
                      <Cpu className="w-3.5 h-3.5 text-gray-400" />
                      Hardware / GPU Architecture Impact:
                    </strong>
                    {selectedHotspot.hardware_impact}
                  </div>
                )}
              </div>

              {/* Before & After Refactoring Code Preview */}
              <div className="space-y-3">
                <div className="text-[10px] text-emerald-600 font-semibold uppercase tracking-wider">
                  Recommended Code Refactor
                </div>

                {selectedHotspot.after_code && (
                  <div>
                    <div className="text-[10px] text-emerald-600 font-semibold mb-1 uppercase tracking-wider">
                      Optimized Replacement (Drop-in):
                    </div>
                    <pre className="p-3 bg-gray-50 rounded-lg border border-emerald-100 font-mono text-xs text-gray-700 overflow-x-auto">
                      {selectedHotspot.after_code}
                    </pre>
                  </div>
                )}

                <div className="text-xs text-gray-600 bg-gray-50 p-3 rounded-lg border border-gray-200 flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-gray-900 block mb-0.5">Engineering Rationale:</strong>
                    {selectedHotspot.optimization}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-xl p-12 text-center text-gray-400 text-xs">
              Select a hotspot on the left to inspect time complexity, space usage, and hardware acceleration diffs.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
