import React, { useState, useEffect } from 'react';
import { BrainCircuit, Play, BarChart2 } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { api } from '../services/api';
import { ModelMetrics } from '../types';

export const ModelInsights: React.FC = () => {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [testCode, setTestCode] = useState<string>(
    'import subprocess\ndef execute_command(user_input):\n    return subprocess.run(f"ping -c 1 {user_input}", shell=True)'
  );
  const [inferenceResult, setInferenceResult] = useState<any>(null);
  const [isInferring, setIsInferring] = useState<boolean>(false);

  useEffect(() => {
    api.getModelMetrics().then(setMetrics).catch(console.warn);
  }, []);

  const handleRunInference = async () => {
    setIsInferring(true);
    try {
      const res = await api.runInference(testCode);
      setInferenceResult(res);
    } catch (err: any) {
      alert(`Inference failed: ${err.message}`);
    } finally {
      setIsInferring(false);
    }
  };

  // Build chart data from metrics, with fallbacks matching the original table
  const chartData = [
    {
      metric: 'Accuracy',
      'Baseline A': Math.round((metrics?.baseline_a_static_only.accuracy ?? 0.70) * 100),
      'Baseline B': Math.round((metrics?.baseline_b_static_plus_neural.accuracy ?? 0.60) * 100),
      'Baseline C': Math.round((metrics?.baseline_c_full_agentic.accuracy ?? 0.90) * 100),
    },
    {
      metric: 'Precision',
      'Baseline A': Math.round((metrics?.baseline_a_static_only.precision ?? 0.75) * 100),
      'Baseline B': Math.round((metrics?.baseline_b_static_plus_neural.precision ?? 1.0) * 100),
      'Baseline C': Math.round((metrics?.baseline_c_full_agentic.precision ?? 0.94) * 100),
    },
    {
      metric: 'Recall',
      'Baseline A': Math.round((metrics?.baseline_a_static_only.recall ?? 0.60) * 100),
      'Baseline B': Math.round((metrics?.baseline_b_static_plus_neural.recall ?? 0.20) * 100),
      'Baseline C': Math.round((metrics?.baseline_c_full_agentic.recall ?? 0.86) * 100),
    },
    {
      metric: 'F1',
      'Baseline A': Math.round((metrics?.baseline_a_static_only.f1_score ?? 0.67) * 100),
      'Baseline B': Math.round((metrics?.baseline_b_static_plus_neural.f1_score ?? 0.33) * 100),
      'Baseline C': Math.round((metrics?.baseline_c_full_agentic.f1_score ?? 0.90) * 100),
    },
    {
      metric: 'Specificity',
      'Baseline A': Math.round((1 - (metrics?.baseline_a_static_only.false_positive_rate ?? 0.20)) * 100),
      'Baseline B': Math.round((1 - (metrics?.baseline_b_static_plus_neural.false_positive_rate ?? 0.00)) * 100),
      'Baseline C': Math.round((1 - (metrics?.baseline_c_full_agentic.false_positive_rate ?? 0.05)) * 100),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">
            Neural Model Insights (ANN / Deep Learning)
          </h1>
          <p className="text-sm text-gray-400 font-light mt-0.5">
            Empirical evaluation and ablation study of the fine-tuned CodeBERT transformer vulnerability
            classifier.
          </p>
        </div>
      </div>

      {/* Model Architecture Specifications */}
      <div className="grid grid-cols-4 gap-5">
        <div className="card">
          <div className="text-xs text-gray-400 section-label">Backbone Model</div>
          <div className="text-sm font-bold text-indigo-400 font-mono mt-2">
            microsoft/codebert-base
          </div>
        </div>

        <div className="card">
          <div className="text-xs text-gray-400 section-label">Classification Head</div>
          <div className="text-sm font-bold text-white font-mono mt-2">
            Dense + Dropout (0.2) + Softmax
          </div>
        </div>

        <div className="card">
          <div className="text-xs text-gray-400 section-label">Training Loss</div>
          <div className="text-sm font-bold text-white font-mono mt-2">
            Cross-Entropy + Imbalance Weights
          </div>
        </div>

        <div className="card">
          <div className="text-xs text-gray-400 section-label">Inference Device</div>
          <div className="text-sm font-bold text-emerald-400 font-mono mt-2">
            Local CPU / MPS Accelerated
          </div>
        </div>
      </div>

      {/* Ablation Study — Grouped Bar Chart */}
      <div className="card">
        <h2 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-indigo-400" />
          Academic Ablation Study Comparison
        </h2>
        <p className="text-xs text-gray-400 mb-4">
          Comparative benchmark across 3 progressive architecture baselines on labeled vulnerability
          datasets.
        </p>

        <div className="overflow-x-auto">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} margin={{ top: 4, right: 16, left: -8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
              <XAxis
                dataKey="metric"
                tick={{ fill: '#9ca3af', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                domain={[0, 100]}
                tickFormatter={(v: number) => v + '%'}
                tick={{ fill: '#9ca3af', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                formatter={(v: number) => v + '%'}
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: 11,
                }}
              />
              <Legend wrapperStyle={{ fontSize: 11, color: '#9ca3af' }} />
              <Bar dataKey="Baseline A" fill="#64748b" radius={[3, 3, 0, 0]} />
              <Bar dataKey="Baseline B" fill="#6366f1" radius={[3, 3, 0, 0]} />
              <Bar dataKey="Baseline C" fill="#10b981" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Interactive Inference Playground */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-indigo-400" />
            Real-Time Neural Inference Playground
          </h2>
          <button
            onClick={handleRunInference}
            disabled={isInferring}
            className="btn-primary flex items-center gap-2 shadow-glow disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {isInferring ? 'Scoring...' : 'Run Neural Prediction'}
          </button>
        </div>

        <textarea
          value={testCode}
          onChange={(e) => setTestCode(e.target.value)}
          rows={4}
          className="input w-full font-mono leading-relaxed"
          placeholder="Paste function or code snippet..."
        />

        {inferenceResult && (
          <div className="rounded-2xl bg-white/[0.03] border border-white/[0.08] grid grid-cols-4 gap-4 p-4">
            <div>
              <div className="text-[10px] text-gray-400 uppercase section-label">Predicted Risk Score</div>
              <div className="text-lg font-bold font-mono text-indigo-400 mt-1">
                {Math.round(inferenceResult.risk_score * 100)}%
              </div>
            </div>
            <div>
              <div className="text-[10px] text-gray-400 uppercase section-label">Classification</div>
              <div
                className={`text-sm font-bold uppercase mt-1 ${
                  inferenceResult.risk_label === 'vulnerable' ? 'text-red-400' : 'text-emerald-400'
                }`}
              >
                {inferenceResult.risk_label}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-gray-400 uppercase section-label">Inference Latency</div>
              <div className="text-sm font-bold font-mono text-white mt-1">
                {inferenceResult.latency_ms} ms
              </div>
            </div>
            <div>
              <div className="text-[10px] text-gray-400 uppercase section-label">CWE Signatures</div>
              <div className="text-xs text-amber-400 truncate mt-1">
                {inferenceResult.cwe_suggestions?.join(', ') || 'None'}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
