import React, { useState, useEffect } from 'react';
import { BarChart3, Activity, Zap, CheckCircle2, XCircle, Cpu, RefreshCw } from 'lucide-react';

export default function UsageDashboard() {
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUsage = () => {
    setLoading(true);
    fetch('/api/usage')
      .then(r => r.json())
      .then(data => setUsage(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchUsage();
  }, []);

  const today = usage?.today || {};
  const last7 = usage?.last_7_days || {};
  const providers = today.providers || {};

  return (
    <div className="flex-1 bg-[#1a1614] p-6 overflow-y-auto text-zinc-100 space-y-6 select-none max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-amber-600/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-zinc-100 flex items-center space-x-2">
              <span>AI Usage Dashboard</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 font-mono font-semibold">Token Tracker</span>
            </h2>
            <p className="text-xs text-zinc-400">Track AI requests, tokens, and success rates across providers</p>
          </div>
        </div>
        <button
          onClick={fetchUsage}
          className="px-3.5 py-2 rounded-xl bg-[#262019] hover:bg-[#2a231d] text-zinc-300 border border-white/10 font-medium text-xs flex items-center space-x-2 transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Today's Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-[#262019] p-4 rounded-2xl border border-white/5">
          <div className="flex items-center space-x-2 text-[11px] text-zinc-400">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>Requests Today</span>
          </div>
          <div className="text-2xl font-bold text-zinc-100 mt-1">{today.requests || 0}</div>
        </div>
        <div className="bg-[#262019] p-4 rounded-2xl border border-white/5">
          <div className="flex items-center space-x-2 text-[11px] text-zinc-400">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span>Tokens Today</span>
          </div>
          <div className="text-2xl font-bold text-zinc-100 mt-1">{today.tokens || 0}</div>
        </div>
        <div className="bg-[#262019] p-4 rounded-2xl border border-white/5">
          <div className="flex items-center space-x-2 text-[11px] text-zinc-400">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Success</span>
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{today.success || 0}</div>
        </div>
        <div className="bg-[#262019] p-4 rounded-2xl border border-white/5">
          <div className="flex items-center space-x-2 text-[11px] text-zinc-400">
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
            <span>Failed</span>
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-1">{today.failed || 0}</div>
        </div>
      </div>

      {/* Last 7 days */}
      <div className="bg-[#262019] p-5 rounded-2xl border border-white/5">
        <div className="flex items-center space-x-2 text-xs font-bold text-zinc-200 uppercase tracking-wider mb-4">
          <Activity className="w-4 h-4 text-emerald-400" />
          <span>Last 7 Days</span>
        </div>
        <div className="grid grid-cols-4 gap-3 text-center">
          <div>
            <div className="text-[11px] text-zinc-400">Requests</div>
            <div className="text-xl font-bold text-zinc-100">{last7.requests || 0}</div>
          </div>
          <div>
            <div className="text-[11px] text-zinc-400">Tokens</div>
            <div className="text-xl font-bold text-zinc-100">{last7.tokens || 0}</div>
          </div>
          <div>
            <div className="text-[11px] text-zinc-400">Success</div>
            <div className="text-xl font-bold text-emerald-400">{last7.success || 0}</div>
          </div>
          <div>
            <div className="text-[11px] text-zinc-400">Failed</div>
            <div className="text-xl font-bold text-rose-400">{last7.failed || 0}</div>
          </div>
        </div>
      </div>

      {/* Per-provider breakdown */}
      <div className="bg-[#262019] p-5 rounded-2xl border border-white/5">
        <div className="flex items-center space-x-2 text-xs font-bold text-zinc-200 uppercase tracking-wider mb-4">
          <Cpu className="w-4 h-4 text-amber-400" />
          <span>Per-Provider Breakdown (Today)</span>
        </div>
        {Object.keys(providers).length > 0 ? (
          <div className="space-y-2">
            {Object.entries(providers).map(([name, p]) => (
              <div key={name} className="flex items-center justify-between bg-[#1f1a17] rounded-xl p-3 border border-white/5">
                <span className="text-xs font-semibold text-zinc-200 capitalize">{name}</span>
                <div className="flex items-center space-x-4 text-[11px] text-zinc-400">
                  <span>{p.requests} requests</span>
                  <span className="text-amber-400">{p.tokens} tokens</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-[11px] text-zinc-500 italic p-4 bg-[#1f1a17] rounded-xl border border-white/5">
            No requests recorded yet. Usage is tracked automatically when you chat with an external AI provider.
          </div>
        )}
      </div>
    </div>
  );
}
