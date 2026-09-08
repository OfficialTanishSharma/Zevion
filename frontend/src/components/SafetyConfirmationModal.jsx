import React from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle, XCircle, FileWarning, Terminal, Trash2 } from 'lucide-react';

export default function SafetyConfirmationModal({ isOpen, payload, tokenId, onConfirm, onCancel }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in select-none">
      <div className="bg-[#201b18] border-2 border-rose-500/60 rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden glow-danger">
        {/* Header */}
        <div className="bg-rose-950/60 border-b border-rose-500/30 p-4 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-rose-600/30 border border-rose-500/60 flex items-center justify-center text-rose-400">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h2 className="text-base font-bold text-rose-200">Security Guard: Authorization Required</h2>
            <p className="text-xs text-rose-300/80">Potentially destructive action detected by AI safety engine</p>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 text-xs">
          <div className="bg-[#1a1614] p-3.5 rounded-xl border border-[#3a3128] space-y-2">
            <div className="flex items-center justify-between text-zinc-400">
              <span className="font-semibold text-zinc-200">Requested Action:</span>
              <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-mono text-[10px] font-bold border border-rose-500/30">
                CRITICAL RISK
              </span>
            </div>
            <div className="text-sm font-semibold text-zinc-100">
              {payload?.action_title || 'File Deletion or System Modification'}
            </div>
            <p className="text-zinc-300 leading-relaxed">
              {payload?.impact || 'This action may permanently modify or remove files from your workspace or OS.'}
            </p>
          </div>

          {/* Parameters Details */}
          {payload?.parameters && (
            <div>
              <div className="text-[11px] uppercase font-bold text-zinc-400 mb-1">Action Parameters:</div>
              <pre className="bg-[#161210] p-3 rounded-lg border border-[#2a231d] text-emerald-400 font-mono text-[11px] overflow-x-auto">
                {JSON.stringify(payload.parameters, null, 2)}
              </pre>
            </div>
          )}

          <div className="bg-amber-950/30 border border-amber-500/30 p-3 rounded-xl flex items-start space-x-2.5 text-amber-200 text-xs">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <span>
              Zevion will NOT execute this command unless you explicitly authorize it.
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="p-4 bg-[#1a1614] border-t border-[#2e2620] flex items-center justify-end space-x-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-xl bg-[#2a231d] hover:bg-[#3a3128] text-zinc-300 font-medium text-xs transition-all flex items-center space-x-1.5"
          >
            <XCircle className="w-4 h-4 text-zinc-400" />
            <span>Cancel & Reject</span>
          </button>

          <button
            onClick={() => onConfirm(tokenId, true)}
            className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs shadow-lg shadow-rose-600/30 transition-all flex items-center space-x-1.5"
          >
            <CheckCircle className="w-4 h-4" />
            <span>Authorize & Execute Once</span>
          </button>
        </div>
      </div>
    </div>
  );
}
