import React, { useState, useEffect } from 'react';
import { Activity } from 'lucide-react';
import { useAppStore } from '../stores/appStore';

export const LiveMonitoring: React.FC = () => {
  const { activeProject, scans, liveEvents, wsConnected } = useAppStore();

  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 10000);
    return () => clearInterval(id);
  }, []);

  // suppress unused variable lint warning — now is used inside relTime via closure
  void now;

  const relTime = (ts?: string): string => {
    if (!ts) return '';
    const diff = (Date.now() - new Date(ts).getTime()) / 1000;
    if (diff < 60) return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    return new Date(ts).toLocaleTimeString();
  };

  const dotColor = (type: string): string => {
    if (type === 'file_changed') return 'bg-indigo-500';
    if (type === 'scan_started' || type === 'scan_completed') return 'bg-emerald-500';
    if (type === 'finding_detected') return 'bg-red-500';
    if (type === 'agent_step') return 'bg-amber-500';
    return 'bg-gray-500';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Live Filesystem Monitoring</h1>
          <p className="text-sm text-gray-400 font-light mt-0.5">
            Observing local files for writes, renames, and deletions with debounced SHA-256 change
            detection.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {wsConnected ? (
            <>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-xs font-semibold text-emerald-400">Stream Online</span>
            </>
          ) : (
            <>
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-xs font-semibold text-amber-400">Connecting...</span>
            </>
          )}
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-5">
        <div className="card hover:scale-[1.01]">
          <div className="text-xs text-gray-400 section-label">Watchdog Status</div>
          <div className="text-base font-semibold text-white mt-2 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            {activeProject?.is_monitored ? 'Active Observer' : 'Idle / Paused'}
          </div>
        </div>

        <div className="card hover:scale-[1.01]">
          <div className="text-xs text-gray-400 section-label">Debounce Window</div>
          <div className="text-base font-semibold text-white mt-2 font-mono">1.5s Coalesced</div>
        </div>

        <div className="card hover:scale-[1.01]">
          <div className="text-xs text-gray-400 section-label">Queue Processing</div>
          <div className="text-base font-semibold text-white mt-2 font-mono">0 Backlog Items</div>
        </div>
      </div>

      {/* Events Stream Panel */}
      <div className="p-6 rounded-2xl bg-[#111827] border border-white/[0.08] backdrop-blur-sm">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-indigo-400" />
          Recent Filesystem Events
        </h2>
        <div className="space-y-2">
          {liveEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <span className="w-12 h-12 rounded-full bg-indigo-500/10 flex items-center justify-center">
                <Activity className="w-6 h-6 text-indigo-400" />
              </span>
              <p className="text-base font-medium text-white">No Events Yet</p>
              <p className="text-sm text-gray-500">Waiting for filesystem events…</p>
            </div>
          ) : (
            liveEvents.slice(0, 50).map((evt, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:border-white/10 flex items-center justify-between transition-all duration-200"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`w-2 h-2 rounded-full flex-shrink-0 ${dotColor(evt.type)}`}
                  />
                  <div>
                    <span className="text-xs font-mono text-gray-200">
                      {(evt.data?.file as string) || evt.message || evt.type}
                    </span>
                    <div className="text-[10px] text-gray-400 uppercase tracking-wide mt-0.5">
                      {evt.type}
                    </div>
                  </div>
                </div>
                <span className="text-[11px] text-gray-400 font-mono">
                  {evt.timestamp ? relTime(evt.timestamp) : 'live'}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
