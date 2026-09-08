import React, { useState } from 'react';
import { Sparkles, Key, ShieldCheck, ArrowRight, Eye, EyeOff, CheckCircle2, Cpu, AlertCircle, Loader2, Lightbulb } from 'lucide-react';

export default function OnboardingModal({ isOpen, onComplete }) {
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  if (!isOpen) return null;

  const handleContinueWithKey = async (e) => {
    e?.preventDefault();
    if (isSubmitting) return;

    const trimmed = apiKey.trim();
    if (!trimmed) {
      setErrorMessage("Please enter a Gemini API key or click 'Continue without API key'.");
      return;
    }

    setErrorMessage(null);
    setSuccessMessage(null);
    setIsSubmitting(true);

    try {
      const result = await onComplete(trimmed, false);
      if (!result?.success) {
        setErrorMessage(result?.error || result?.message || 'Gemini API key is invalid. Please check your key and try again.');
        setIsSubmitting(false);
      } else {
        setSuccessMessage(result?.message || 'Gemini connected successfully.');
        setIsSubmitting(false);
      }
    } catch (err) {
      setErrorMessage('Gemini network or connection error. Please check your internet connection.');
      setIsSubmitting(false);
    }
  };

  const handleContinueWithoutKey = async () => {
    if (isSubmitting) return;
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsSubmitting(true);

    try {
      await onComplete('', true);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in duration-200 select-none">
      <div className="bg-[#1f1a17] border border-zinc-800 rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden text-zinc-100 flex flex-col">
        {/* Modal Banner Header */}
        <div className="bg-gradient-to-r from-amber-900/40 via-zinc-900 to-rose-900/40 p-6 border-b border-zinc-800/80">
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-12 h-12 rounded-xl overflow-hidden ring-1 ring-amber-500/30 shadow-lg shadow-orange-900/30 shrink-0">
              <img src="/assets/logo.png" alt="Zevion" className="w-full h-full object-cover" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">Zevion</h1>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] uppercase font-mono tracking-wider px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-semibold">
                  v2.0 Native Edition
                </span>
                <span className="text-xs text-zinc-400">First-Launch Setup</span>
              </div>
            </div>
          </div>

          <p className="text-xs text-zinc-300 mt-2 leading-relaxed">
            Connect Gemini to enable smarter natural-language understanding and AI-powered desktop automation.
          </p>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleContinueWithKey} className="p-6 space-y-5">
          {/* Error Message Banner */}
          {errorMessage && (
            <div className="bg-rose-500/10 border border-rose-500/40 rounded-xl p-3.5 flex items-start space-x-3 text-rose-300 text-xs animate-in fade-in">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1 font-medium leading-relaxed">{errorMessage}</div>
            </div>
          )}

          {/* Success Message Banner */}
          {successMessage && (
            <div className="bg-emerald-500/10 border border-emerald-500/40 rounded-xl p-3.5 flex items-start space-x-3 text-emerald-300 text-xs animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div className="flex-1 font-medium leading-relaxed">{successMessage}</div>
            </div>
          )}

          {/* Key Input Section */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-zinc-200 flex items-center space-x-1.5">
                <Key className="w-3.5 h-3.5 text-emerald-400" />
                <span>Gemini API Key</span>
              </label>
              <span className="text-[10px] text-zinc-400 bg-zinc-800/80 px-2 py-0.5 rounded-full border border-zinc-700/50">
                Optional
              </span>
            </div>

            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => {
                  setApiKey(e.target.value);
                  if (errorMessage) setErrorMessage(null);
                }}
                placeholder="Enter your Gemini API key (optional)"
                disabled={isSubmitting}
                className={`w-full bg-[#171311] border rounded-xl pl-3.5 pr-10 py-2.5 text-xs text-zinc-100 font-mono outline-none transition-all placeholder:text-zinc-500 disabled:opacity-60 ${
                  errorMessage
                    ? 'border-rose-500/70 focus:border-rose-400 focus:ring-1 focus:ring-rose-500/30'
                    : 'border-zinc-700/70 focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/30'
                }`}
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-2.5 text-zinc-400 hover:text-zinc-200 transition-colors"
                aria-label="Toggle key visibility"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            <p className="text-[11px] text-zinc-400 flex items-center space-x-1.5">
              <Lightbulb className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              <span>Gemini is optional. You can also run the agent with 100% full local functionality without an API key.</span>
            </p>
          </div>

          {/* Features Highlights */}
          <div className="bg-[#1f1a17] border border-zinc-800/70 rounded-xl p-3.5 space-y-2">
            <div className="text-[11px] font-semibold text-zinc-300 flex items-center space-x-1.5">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              <span>What you can do right away:</span>
            </div>
            <ul className="text-[11px] text-zinc-400 space-y-1 pl-1">
              <li className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                <span>Open, close, minimize, and restore Windows applications</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                <span>Create new instances and windows (CMD, PowerShell, Chrome, Notepad)</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                <span>Browse web, play YouTube videos, organize files, and take screenshots</span>
              </li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="pt-2 flex flex-col sm:flex-row items-center gap-2.5">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full sm:flex-1 py-2.5 px-4 rounded-xl bg-accent-gradient hover:opacity-90 text-white text-xs font-semibold shadow-lg shadow-orange-900/20 flex items-center justify-center space-x-1.5 transition-all disabled:opacity-60"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Verifying...</span>
                </>
              ) : (
                <>
                  <span>Continue</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleContinueWithoutKey}
              disabled={isSubmitting}
              className="w-full sm:w-auto py-2.5 px-4 rounded-xl bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-900 text-zinc-300 hover:text-white text-xs font-medium border border-zinc-700/60 transition-all disabled:opacity-60"
            >
              Continue without API key
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
