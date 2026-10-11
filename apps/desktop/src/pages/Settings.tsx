import React, { useState } from 'react';
import { Sliders, Shield, Lock, Cpu, Server, Check } from 'lucide-react';
import { api } from '../services/api';

export const Settings: React.FC = () => {
  const [routingMode, setRoutingMode] = useState<string>('local_first_fallback');
  const [allowCloudCode, setAllowCloudCode] = useState<boolean>(false);
  const [ollamaModel, setOllamaModel] = useState<string>('codellama:7b');
  const [debounceSeconds, setDebounceSeconds] = useState<number>(1.5);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  const handleSave = async () => {
    try {
      await api.updateProviderSettings({
        routing_mode: routingMode,
        allow_cloud_code_sharing: allowCloudCode,
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 2000);
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Platform Settings</h1>
          <p className="text-sm text-gray-400 font-light mt-0.5">
            Configure LLM providers, privacy boundaries, scanner sensitivities, and local execution thresholds.
          </p>
        </div>
        <button
          onClick={handleSave}
          className="btn-primary flex items-center gap-2 shadow-glow"
        >
          {savedSuccess ? <Check className="w-4 h-4 text-emerald-400" /> : null}
          {savedSuccess ? 'Settings Saved' : 'Save Configuration'}
        </button>
      </div>

      {/* Privacy Guard (Local-First Guarantee) */}
      <div className="card space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Lock className="w-4 h-4 text-emerald-400" />
          Developer Privacy & Local-First Boundaries
        </h2>
        <div className="flex items-center justify-between p-3.5 bg-white/[0.03] rounded-xl border border-white/[0.08]">
          <div className="space-y-0.5">
            <div className="text-xs font-semibold text-white">
              Cloud Source Code Transmission Consent
            </div>
            <p className="text-[11px] text-gray-400">
              When disabled, private repository source code will NEVER leave localhost. Only Ollama and local models run.
            </p>
          </div>
          {/* Styled toggle switch */}
          <label className="relative inline-flex items-center cursor-pointer ml-4">
            <input
              type="checkbox"
              checked={allowCloudCode}
              onChange={(e) => setAllowCloudCode(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-10 h-5 rounded-full bg-white/10 border border-white/15 peer-checked:bg-indigo-600 transition-all duration-200 after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-4 after:h-4 after:rounded-full after:bg-white after:transition-all after:duration-200 peer-checked:after:translate-x-5" />
          </label>
        </div>
      </div>

      {/* LLM Routing Architecture */}
      <div className="card space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Cpu className="w-4 h-4 text-indigo-400" />
          LLM Provider Orchestration
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Routing Mode</label>
            <select
              value={routingMode}
              onChange={(e) => setRoutingMode(e.target.value)}
              className="input w-full"
            >
              <option value="local_only">Local Only (Ollama / Heuristic)</option>
              <option value="local_first_fallback">Local-First with Cloud Fallback</option>
              <option value="openai_only">OpenAI Only (Cloud)</option>
              <option value="gemini_only">Google Gemini Only (Cloud)</option>
              <option value="hybrid">Hybrid Task Routing</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Ollama Model Identifier
            </label>
            <input
              type="text"
              value={ollamaModel}
              onChange={(e) => setOllamaModel(e.target.value)}
              className="input w-full font-mono"
            />
          </div>
        </div>
      </div>

      {/* Filesystem Watchdog Settings */}
      <div className="card space-y-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Server className="w-4 h-4 text-amber-400" />
          Watchdog & Resource Scheduling
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Debounce Window (Seconds)
            </label>
            <input
              type="number"
              step="0.5"
              min="0.5"
              max="10"
              value={debounceSeconds}
              onChange={(e) => setDebounceSeconds(parseFloat(e.target.value))}
              className="input w-full font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">
              Max Agent Tool Budget
            </label>
            <input
              type="number"
              defaultValue={15}
              disabled
              className="input w-full font-mono opacity-50 cursor-not-allowed"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
