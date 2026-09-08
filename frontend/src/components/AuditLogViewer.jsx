import React, { useState } from 'react';
import { 
  ShieldAlert, 
  Search, 
  Download, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  Trash2, 
  Terminal,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export default function AuditLogViewer({ logs }) {
  const [filterLevel, setFilterLevel] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedLogId, setExpandedLogId] = useState(null);

  const defaultSampleLogs = logs?.length > 0 ? logs : [
    {
      id: 'log_17230001',
      tool_name: 'open_application',
      parameters: { app_name: 'chrome' },
      risk_level: 'safe',
      result_summary: 'Success (PID: 8492)',
      duration_ms: 142.5,
      timestamp: Date.now() / 1000 - 300,
      confirmed_by_user: false,
      full_result: { os_launched: true, window_title: 'Google Chrome' }
    },
    {
      id: 'log_17230002',
      tool_name: 'create_folder',
      parameters: { folder_path: 'Projects' },
      risk_level: 'safe',
      result_summary: 'Success (Created Directory)',
      duration_ms: 8.2,
      timestamp: Date.now() / 1000 - 180,
      confirmed_by_user: false,
      full_result: { exists: true }
    },
    {
      id: 'log_17230003',
      tool_name: 'delete_file',
      parameters: { path: 'temporary_cache.tmp' },
      risk_level: 'dangerous',
      result_summary: 'Success (User Confirmed)',
      duration_ms: 12.4,
      timestamp: Date.now() / 1000 - 60,
      confirmed_by_user: true,
      full_result: { was_directory: false }
    }
  ];

  const filtered = defaultSampleLogs.filter(l => {
    const matchesLevel = filterLevel === 'All' || l.risk_level === filterLevel.toLowerCase();
    const matchesSearch = l.tool_name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          JSON.stringify(l.parameters).toLowerCase().includes(searchTerm.toLowerCase());
    return matchesLevel && matchesSearch;
  });

  const exportJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(defaultSampleLogs, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `ai_agent_audit_log_${new Date().toISOString().slice(0,10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="flex-1 bg-[#1a1614] p-6 overflow-y-auto text-zinc-100 space-y-6 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#2e2620] pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-rose-600/20 border border-rose-500/40 flex items-center justify-center text-rose-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-zinc-100 flex items-center space-x-2">
              <span>Safety & Security Audit Logs</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 font-mono font-semibold">
                Tamper-Evident
              </span>
            </h2>
            <p className="text-xs text-zinc-400">Chronological ledger of every computer action executed by the AI</p>
          </div>
        </div>

        <button
          onClick={exportJSON}
          className="px-3.5 py-2 rounded-xl bg-[#2a231d] hover:bg-[#3a3128] text-zinc-200 border border-[#3a3128] font-medium text-xs flex items-center space-x-2 transition-all shadow-sm"
        >
          <Download className="w-3.5 h-3.5 text-emerald-400" />
          <span>Export Audit Trail (JSON)</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search logs by tool name or parameters..."
            className="w-full bg-[#262019] border border-[#3a3128] focus:border-rose-500/60 rounded-xl pl-9 pr-4 py-2 text-xs text-zinc-100 placeholder-zinc-500 outline-none"
          />
        </div>

        <div className="flex items-center space-x-1.5">
          {['All', 'Safe', 'Moderate', 'Dangerous'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setFilterLevel(lvl)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                filterLevel === lvl
                  ? 'bg-rose-600 text-white shadow-md'
                  : 'bg-[#262019] text-zinc-400 hover:text-zinc-200 border border-[#3a3128]'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-[#1a1614] rounded-2xl border border-[#2e2620] overflow-hidden shadow-sm">
        <div className="divide-y divide-[#262019]">
          {filtered.length === 0 ? (
            <div className="p-8 text-center text-zinc-500 text-xs">No audit logs matching your criteria.</div>
          ) : (
            filtered.map((log, idx) => {
              const isDangerous = log.risk_level === 'dangerous';
              const isModerate = log.risk_level === 'moderate';
              const isExpanded = expandedLogId === log.id;

              return (
                <div key={log.id || idx} className="p-4 hover:bg-[#201b18] transition-all">
                  <div 
                    onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                    className="flex items-center justify-between cursor-pointer"
                  >
                    <div className="flex items-center space-x-3">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase border ${
                        isDangerous ? 'bg-rose-500/20 text-rose-400 border-rose-500/40' :
                        isModerate ? 'bg-amber-500/20 text-amber-400 border-amber-500/40' :
                        'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
                      }`}>
                        {log.risk_level}
                      </span>

                      <div>
                        <div className="text-xs font-semibold text-zinc-200 flex items-center space-x-2">
                          <span>Tool: {log.tool_name}</span>
                          {log.confirmed_by_user && (
                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                              User Authorized
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] text-zinc-400 font-mono mt-0.5">
                          {JSON.stringify(log.parameters)}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3 text-xs text-zinc-400">
                      <span className="font-mono text-[10px] text-zinc-500">{log.duration_ms}ms</span>
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </div>
                  </div>

                  {/* Expanded JSON payload */}
                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t border-[#2a231d] text-[11px] font-mono text-zinc-300">
                      <pre className="bg-[#100d0b] p-3 rounded-lg border border-[#262019] overflow-x-auto text-emerald-400">
                        {JSON.stringify(log, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
