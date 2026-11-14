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
          <h1 className="text-xl font-semibold text-gray-900">Live Filesystem Monitoring</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Observing local files for writes, renames, and deletions with debounced SHA-256 change
            detection.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {wsConnected ? (
            <span className="bg-emerald-50 text-emerald-700 border border-emerald-100 text-xs px-3 py-1 rounded-lg flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              Stream Online
            </span>
          ) : (
            <span className="text-amber-500 text-xs font-medium flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
              Connecting...
            </span>
          )}
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-5">
        <div className="card">
          <div className="section-label">Watchdog Status</div>
          <div className="text-base font-semibold text-gray-900 mt-2 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            {activeProject?.is_monitored ? 'Active Observer' : 'Idle / Paused'}
          </div>
        </div>

        <div className="card">
          <div className="section-label">Debounce Window</div>
          <div className="text-base font-semibold text-gray-900 mt-2 font-mono">1.5s Coalesced</div>
        </div>

        <div className="card">
          <div className="section-label">Queue Processing</div>
          <div className="text-base font-semibold text-gray-900 mt-2 font-mono">0 Backlog Items</div>
        </div>
      </div>

      {/* Events Stream Panel */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-gray-400" />
          Recent Filesystem Events
        </h2>
        <div className="space-y-2">
          {liveEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <span className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
                <Activity className="w-6 h-6 text-gray-400" />
              </span>
              <p className="text-base font-medium text-gray-900">No Events Yet</p>
              <p className="text-sm text-gray-500">Waiting for filesystem events…</p>
            </div>
          ) : (
            liveEvents.slice(0, 50).map((evt, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-lg bg-gray-50 border border-gray-100 hover:border-gray-200 flex items-center justify-between transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`w-2 h-2 rounded-full flex-shrink-0 ${dotColor(evt.type)}`}
                  />
                  <div>
                    <span className="text-xs font-mono text-gray-700">
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
