import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Cpu, 
  ShieldCheck, 
  Volume2, 
  Key, 
  Check, 
  Sparkles,
  Eye,
  EyeOff,
  Trash2,
  Power,
  ChevronDown,
  AlertCircle,
  Loader2,
  CheckCircle2,
  Brain,
  Plus,
  ShieldAlert,
  Scale,
  Zap,
  ListChecks
} from 'lucide-react';

export default function SettingsModal({ currentSettings, onSaveSettings }) {
  const [providers, setProviders] = useState([]);
  const [activeProvider, setActiveProvider] = useState(currentSettings?.active_provider || 'builtin');
  const [activeNvidiaChoice, setActiveNvidiaChoice] = useState('kimi');
  const [editingProvider, setEditingProvider] = useState(null);
  const [keyInput, setKeyInput] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isSubmittingKey, setIsSubmittingKey] = useState(false);
  const [keyError, setKeyError] = useState(null);
  const [keySuccess, setKeySuccess] = useState(null);
  const [generalError, setGeneralError] = useState(null);
  
  const [safetyMode, setSafetyMode] = useState(currentSettings?.safetyMode || 'balanced');
  const [autoSpeak, setAutoSpeak] = useState(currentSettings?.autoSpeak || false);
  const [dryRun, setDryRun] = useState(currentSettings?.dry_run || false);
  const [planMode, setPlanMode] = useState(currentSettings?.plan_mode || false);
  const [savedToast, setSavedToast] = useState(false);

  // Global Level 2 Memory state
  const [memoryEnabled, setMemoryEnabled] = useState(true);
  const [memories, setMemories] = useState([]);
  const [newMemoryText, setNewMemoryText] = useState('');

  // Fetch configured providers list from backend
  const refreshProviders = () => {
    fetch('/api/providers')
      .then(r => r.json())
      .then(data => {
        if (data.providers) setProviders(data.providers);
        if (data.active_provider) setActiveProvider(data.active_provider);
      })
      .catch(() => {});
  };

  const refreshMemories = () => {
    fetch('/api/memory')
      .then(r => r.json())
      .then(data => {
        if (data.memories) setMemories(data.memories);
        if (data.enabled !== undefined) setMemoryEnabled(data.enabled);
      })
      .catch(() => {});
  };

  useEffect(() => {
    refreshProviders();
    refreshMemories();
  }, []);

  const handleToggleMemory = async () => {
    const nextState = !memoryEnabled;
    setMemoryEnabled(nextState);
    try {
      await fetch('/api/memory/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: nextState })
      });
    } catch (e) {
      console.error('Failed to toggle memory:', e);
    }
  };

  const handleAddMemory = async (e) => {
    e?.preventDefault();
    if (!newMemoryText.trim()) return;
    try {
      const res = await fetch('/api/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          key: `custom_${Date.now()}`,
          value: newMemoryText.trim(),
          text: newMemoryText.trim()
        })
      });
      if (res.ok) {
        setNewMemoryText('');
        refreshMemories();
      }
    } catch (e) {
      console.error('Failed to add memory:', e);
    }
  };

  const handleDeleteMemory = async (id) => {
    try {
      await fetch(`/api/memory/${id}`, { method: 'DELETE' });
      refreshMemories();
    } catch (e) {
      console.error('Failed to delete memory:', e);
    }
  };

  const handleClearAllMemories = async () => {
    try {
      await fetch('/api/memory', { method: 'DELETE' });
      refreshMemories();
    } catch (e) {
      console.error('Failed to clear memories:', e);
    }
  };

  useEffect(() => {
    refreshProviders();
  }, []);

  const handleSelectActive = async (providerId) => {
    setGeneralError(null);
    try {
      const res = await fetch('/api/providers/active', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_id: providerId })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setActiveProvider(providerId);
        setSavedToast(true);
        setTimeout(() => setSavedToast(false), 2000);
      } else {
        setGeneralError(data.detail || data.error || `Cannot activate ${providerId}.`);
      }
      refreshProviders();
    } catch (e) {
      console.error(e);
      setGeneralError('Network error while switching active AI provider.');
    }
  };

  const handleSaveKey = async (providerId) => {
    const trimmed = keyInput.trim();
    if (!trimmed) {
      setKeyError('Please enter a valid API key.');
      return;
    }

    setIsSubmittingKey(true);
    setKeyError(null);
    setKeySuccess(null);

    try {
      const res = await fetch('/api/providers/key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_id: providerId,
          api_key: trimmed,
          enabled: true
        })
      });

      const data = await res.json();

      // Check HTTP status and structured success field
      if (!res.ok || data.success === false) {
        setKeyError(data.error || data.message || `${providerId.toUpperCase()} API key is invalid. Please check your key and try again.`);
        setIsSubmittingKey(false);
        refreshProviders();
        return;
      }

      // Verification succeeded
      setKeySuccess(data.message || `${providerId.toUpperCase()} connected successfully.`);
      setIsSubmittingKey(false);
      refreshProviders();

      setTimeout(() => {
        setEditingProvider(null);
        setKeyInput('');
        setKeySuccess(null);
        setKeyError(null);
        refreshProviders();
      }, 1200);

    } catch (e) {
      console.error(e);
      setKeyError('Network or connection error. Please check your internet connection.');
      setIsSubmittingKey(false);
      refreshProviders();
    }
  };

  const handleToggleEnable = async (providerId, currentEnabled) => {
    setKeyError(null);
    try {
      const res = await fetch('/api/providers/key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_id: providerId,
          api_key: '',
          enabled: !currentEnabled
        })
      });
      const data = await res.json();
      if (!res.ok || data.success === false) {
        setGeneralError(data.error || data.message || 'Cannot toggle provider state.');
      }
      refreshProviders();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRemoveKey = async (providerId) => {
    setKeyError(null);
    setKeySuccess(null);
    try {
      await fetch(`/api/providers/key?provider_id=${providerId}`, {
        method: 'DELETE'
      });
      refreshProviders();
    } catch (e) {
      console.error(e);
    }
  };

  const handleGlobalSave = () => {
    onSaveSettings({
      active_provider: activeProvider,
      safetyMode,
      autoSpeak,
      dry_run: dryRun,
      plan_mode: planMode
    });
    // Also persist dry-run / plan-mode immediately via their own API calls
    fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dry_run: dryRun, plan_mode: planMode })
    }).catch(() => {});
    setSavedToast(true);
    setTimeout(() => setSavedToast(false), 2500);
  };

  // Base list of supported primary providers
  const primaryProviders = [
    { id: 'gemini', name: 'Gemini' },
    { id: 'claude', name: 'Claude' },
    { id: 'chatgpt', name: 'ChatGPT' },
    { id: 'nvidia', name: 'NVIDIA' }
  ];

  const nvidiaChoices = [
    { id: 'kimi', name: 'Kimi' },
    { id: 'deepseek', name: 'DeepSeek' },
    { id: 'qwen', name: 'Qwen' }
  ];

  const nvidiaProviderState = providers.find(p => p.id === 'nvidia') || { is_configured: false, enabled: false, has_key: false };

  return (
    <div className="flex-1 bg-[#1a1614] p-6 overflow-y-auto text-zinc-100 space-y-6 select-none max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#2e2620] pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-zinc-800 border border-zinc-700 flex items-center justify-center text-zinc-200">
            <Settings className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-zinc-100 flex items-center space-x-2">
              <span>AI Provider & Agent Settings</span>
            </h2>
            <p className="text-xs text-zinc-400">Manage AI reasoning providers, API keys, and desktop safety policies</p>
          </div>
        </div>

        <button
          onClick={handleGlobalSave}
          className="px-4 py-2 rounded-xl bg-accent-gradient hover:opacity-90 text-white font-semibold text-xs shadow-lg shadow-orange-600/20 flex items-center space-x-1.5 transition-all"
        >
          {savedToast ? <Check className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
          <span>{savedToast ? 'Settings Saved!' : 'Save Preferences'}</span>
        </button>
      </div>

      {/* General Error Banner */}
      {generalError && (
        <div className="bg-rose-500/10 border border-rose-500/40 rounded-xl p-3.5 flex items-start space-x-3 text-rose-300 text-xs animate-in fade-in">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1 font-medium leading-relaxed">{generalError}</div>
        </div>
      )}

      {/* Active AI Selector */}
      <div className="bg-[#262019] p-5 rounded-2xl border border-[#3a3128] space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs font-bold text-zinc-200 uppercase tracking-wider">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <span>Active AI</span>
          </div>
          <span className="text-[11px] text-zinc-400">Selected provider is used for natural language planning</span>
        </div>

        <div className="flex items-center space-x-3">
          <div className="relative flex-1 max-w-xs">
            <select
              value={activeProvider}
              onChange={(e) => handleSelectActive(e.target.value)}
              className="w-full bg-[#1a1614] border border-[#3a3128] rounded-xl px-3.5 py-2.5 text-xs text-zinc-100 font-semibold outline-none appearance-none cursor-pointer focus:border-emerald-500"
            >
              <option value="builtin">Built-in</option>
              {providers
                .filter(p => p.id !== 'builtin' && (p.enabled || p.is_configured))
                .map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
            </select>
            <ChevronDown className="w-4 h-4 text-zinc-400 absolute right-3 top-3 pointer-events-none" />
          </div>

          <div className="text-xs text-zinc-400 flex items-center space-x-2">
            <span>Current Status:</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              {activeProvider === 'builtin' ? 'Built-in (Zero Config)' : `${providers.find(p => p.id === activeProvider)?.name || activeProvider} Active`}
            </span>
          </div>
        </div>
      </div>

      {/* Configured Providers Management */}
      <div className="bg-[#262019] p-5 rounded-2xl border border-[#3a3128] space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs font-bold text-zinc-200 uppercase tracking-wider">
            <Key className="w-4 h-4 text-emerald-400" />
            <span>Configured Providers</span>
          </div>
          <span className="text-[11px] text-zinc-400">Keys are stored securely and never leaked in logs</span>
        </div>

        <div className="space-y-3">
          {primaryProviders.map(p => {
            const state = providers.find(item => item.id === p.id) || {
              is_configured: false,
              enabled: false,
              has_key: false
            };
            const isEditing = editingProvider === p.id;

            return (
              <div 
                key={p.id} 
                className="bg-[#241e1a] border border-[#3a3128] rounded-xl p-4 flex flex-col space-y-3"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center space-x-2.5">
                      <span className="font-semibold text-xs text-zinc-100">{p.name}</span>
                      <span 
                        className={`text-[10px] px-2 py-0.5 rounded-md font-medium border ${
                          state.enabled && state.has_key
                            ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                            : state.has_key
                            ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                            : 'bg-zinc-800 text-zinc-400 border-zinc-700'
                        }`}
                      >
                        Status: {state.enabled && state.has_key ? 'Enabled' : state.has_key ? 'Disabled' : 'Not configured'}
                      </span>
                    </div>

                    {!isEditing && (
                      <p className="text-[11px] text-zinc-400 mt-1">
                        {state.has_key ? 'API key configured and verified' : 'Requires API key to enable'}
                      </p>
                    )}
                  </div>

                  {!isEditing && (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => { 
                          setEditingProvider(p.id); 
                          setKeyInput(''); 
                          setKeyError(null);
                          setKeySuccess(null);
                        }}
                        className="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium border border-zinc-700 transition-colors"
                      >
                        {state.has_key ? 'Change API Key' : 'Add API Key'}
                      </button>

                      {state.has_key && (
                        <>
                          <button
                            onClick={() => handleToggleEnable(p.id, state.enabled)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors flex items-center space-x-1 ${
                              state.enabled
                                ? 'bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20'
                                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20'
                            }`}
                          >
                            <Power className="w-3 h-3" />
                            <span>{state.enabled ? 'Disable' : 'Enable'}</span>
                          </button>

                          <button
                            onClick={() => handleRemoveKey(p.id)}
                            className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/30 transition-colors"
                            title="Remove API Key"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </div>

                {/* Edit Box */}
                {isEditing && (
                  <div className="pt-2 border-t border-zinc-800/80 space-y-2.5">
                    {keyError && (
                      <div className="bg-rose-500/10 border border-rose-500/40 rounded-xl p-2.5 flex items-start space-x-2 text-rose-300 text-xs animate-in fade-in">
                        <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                        <div className="flex-1 font-medium leading-relaxed">{keyError}</div>
                      </div>
                    )}

                    {keySuccess && (
                      <div className="bg-emerald-500/10 border border-emerald-500/40 rounded-xl p-2.5 flex items-start space-x-2 text-emerald-300 text-xs animate-in fade-in">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <div className="flex-1 font-medium leading-relaxed">{keySuccess}</div>
                      </div>
                    )}

                    <div className="flex items-center space-x-2">
                      <div className="relative flex-1 max-w-md">
                        <input
                          type={showKey ? 'text' : 'password'}
                          value={keyInput}
                          onChange={(e) => {
                            setKeyInput(e.target.value);
                            if (keyError) setKeyError(null);
                          }}
                          placeholder={`Enter ${p.name} API key`}
                          disabled={isSubmittingKey}
                          className={`w-full bg-[#171311] border rounded-lg px-3 py-1.5 text-xs text-zinc-100 font-mono outline-none pr-8 disabled:opacity-60 ${
                            keyError 
                              ? 'border-rose-500/70 focus:border-rose-400' 
                              : 'border-zinc-700 focus:border-emerald-500'
                          }`}
                        />
                        <button
                          type="button"
                          onClick={() => setShowKey(!showKey)}
                          className="absolute right-2 top-2 text-zinc-400 hover:text-zinc-200"
                          aria-label="Toggle key visibility"
                        >
                          {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                      </div>

                      <button
                        onClick={() => handleSaveKey(p.id)}
                        disabled={isSubmittingKey || !keyInput.trim()}
                        className="px-3.5 py-1.5 rounded-lg bg-accent-gradient hover:opacity-90 text-white text-xs font-semibold flex items-center space-x-1.5 transition-all disabled:opacity-50"
                      >
                        {isSubmittingKey ? (
                          <>
                            <Loader2 className="w-3 h-3 animate-spin" />
                            <span>Verifying...</span>
                          </>
                        ) : (
                          <span>Save</span>
                        )}
                      </button>

                      <button
                        onClick={() => { 
                          setEditingProvider(null); 
                          setKeyInput(''); 
                          setKeyError(null);
                          setKeySuccess(null);
                        }}
                        disabled={isSubmittingKey}
                        className="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs transition-colors disabled:opacity-50"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* NVIDIA AI Choices */}
        <div className="pt-3 border-t border-[#3a3128] space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs font-semibold text-zinc-300">NVIDIA AI choices:</div>
            <span className="text-[10px] text-zinc-500">
              {nvidiaProviderState.has_key ? 'Configured via NVIDIA API key' : 'Configure NVIDIA API key above to enable'}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {nvidiaChoices.map(c => {
              const isSelected = activeNvidiaChoice === c.id;
              const isOverallActive = activeProvider === c.id || (activeProvider === 'nvidia' && activeNvidiaChoice === c.id);

              return (
                <button
                  key={c.id}
                  onClick={() => {
                    setActiveNvidiaChoice(c.id);
                    if (nvidiaProviderState.has_key && nvidiaProviderState.enabled) {
                      handleSelectActive(c.id);
                    }
                  }}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    isOverallActive
                      ? 'bg-emerald-500/15 border-emerald-500/60 text-white shadow-sm'
                      : isSelected
                      ? 'bg-zinc-800/80 border-zinc-600 text-zinc-200'
                      : 'bg-[#241e1a] border-[#3a3128] text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <div className="font-semibold text-xs flex items-center justify-between">
                    <span>{c.name}</span>
                    {isOverallActive && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-mono">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-zinc-500 mt-1">NVIDIA-hosted AI choice</p>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Safety System Policy */}
      <div className="bg-[#262019] p-5 rounded-2xl border border-[#3a3128] space-y-4">
        <div className="flex items-center space-x-2 text-xs font-bold text-zinc-200 uppercase tracking-wider">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Safety Guard & Risk Interception Level</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <button
            onClick={() => setSafetyMode('strict')}
            className={`p-3 rounded-xl border text-left transition-all ${
              safetyMode === 'strict'
                ? 'bg-rose-500/15 border-rose-500/60 text-white'
                : 'bg-[#211c18] border-white/5 text-zinc-400 hover:border-white/10'
            }`}
          >
            <div className="font-semibold text-xs text-zinc-200 flex items-center space-x-1.5">
              <ShieldAlert className={`w-3.5 h-3.5 ${safetyMode === 'strict' ? 'text-rose-400' : 'text-zinc-400'}`} />
              <span>Strict Mode</span>
            </div>
            <p className="text-[10px] text-zinc-400 mt-1">Requires confirmation for creating files, editing folders, and all shell commands.</p>
          </button>

          <button
            onClick={() => setSafetyMode('balanced')}
            className={`p-3 rounded-xl border text-left transition-all ${
              safetyMode === 'balanced'
                ? 'bg-emerald-500/15 border-emerald-500/60 text-white'
                : 'bg-[#211c18] border-white/5 text-zinc-400 hover:border-white/10'
            }`}
          >
            <div className="font-semibold text-xs text-emerald-400 flex items-center space-x-1.5">
              <Scale className="w-3.5 h-3.5" />
              <span>Balanced (Recommended)</span>
            </div>
            <p className="text-[10px] text-zinc-400 mt-1">Auto-executes safe file operations; requires human authorization for deletions & dangerous scripts.</p>
          </button>

          <button
            onClick={() => setSafetyMode('developer')}
            className={`p-3 rounded-xl border text-left transition-all ${
              safetyMode === 'developer'
                ? 'bg-amber-500/15 border-amber-500/60 text-white'
                : 'bg-[#211c18] border-white/5 text-zinc-400 hover:border-white/10'
            }`}
          >
            <div className="font-semibold text-xs text-amber-400 flex items-center space-x-1.5">
              <Zap className="w-3.5 h-3.5" />
              <span>Developer Mode</span>
            </div>
            <p className="text-[10px] text-zinc-400 mt-1">Minimizes prompts for maximum automation velocity.</p>
          </button>
        </div>
      </div>

      {/* Voice Synthesis */}
      <div className="bg-[#262019] p-5 rounded-2xl border border-[#3a3128] flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Volume2 className="w-5 h-5 text-emerald-400" />
          <div>
            <div className="text-xs font-semibold text-zinc-200">Auto-Read AI Voice Responses</div>
            <div className="text-[11px] text-zinc-400">Synthesize spoken speech automatically whenever the AI completes an action</div>
          </div>
        </div>

        <button
          onClick={() => setAutoSpeak(!autoSpeak)}
          className={`w-12 h-6 rounded-full transition-all relative ${
            autoSpeak ? 'bg-emerald-600' : 'bg-zinc-700'
          }`}
        >
          <div className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-all ${
            autoSpeak ? 'left-[26px]' : 'left-0.5'
          }`} />
        </button>
      </div>

      {/* Dry-Run & Plan Mode */}
      <div className="bg-[#262019] p-5 rounded-2xl border border-[#3a3128] space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Eye className="w-5 h-5 text-amber-400" />
            <div>
              <div className="text-xs font-semibold text-zinc-200">Dry-Run Mode (Show but don't run)</div>
              <div className="text-[11px] text-zinc-400">Zevion shows the plan but never actually executes anything — perfect for testing.</div>
            </div>
          </div>
          <button
            onClick={() => setDryRun(!dryRun)}
            className={`w-12 h-6 rounded-full transition-all relative ${dryRun ? 'bg-amber-600' : 'bg-zinc-700'}`}
          >
            <div className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-all ${dryRun ? 'left-[26px]' : 'left-0.5'}`} />
          </button>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <ListChecks className="w-5 h-5 text-cyan-400" />
            <div>
              <div className="text-xs font-semibold text-zinc-200">Plan-Then-Do (multi-step approval)</div>
              <div className="text-[11px] text-zinc-400">For multi-step commands, Zevion shows the plan first and waits for your OK before running.</div>
            </div>
          </div>
          <button
            onClick={() => setPlanMode(!planMode)}
            className={`w-12 h-6 rounded-full transition-all relative ${planMode ? 'bg-cyan-600' : 'bg-zinc-700'}`}
          >
            <div className={`w-5 h-5 rounded-full bg-white absolute top-0.5 transition-all ${planMode ? 'left-[26px]' : 'left-0.5'}`} />
          </button>
        </div>
      </div>

      {/* Level 2 Global Memory Management */}
      <div className="bg-[#262019] p-5 rounded-2xl border border-[#3a3128] space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <Brain className="w-4 h-4 text-emerald-400" />
            <div>
              <div className="text-xs font-bold text-zinc-200 uppercase tracking-wider">Level 2 Global Memory</div>
              <div className="text-[11px] text-zinc-400">Remember preferences and facts across all conversations</div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleToggleMemory}
              className={`px-3 py-1 rounded-lg text-xs font-medium border transition-all ${
                memoryEnabled 
                  ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' 
                  : 'bg-zinc-800 text-zinc-400 border-zinc-700'
              }`}
            >
              {memoryEnabled ? 'Memory Enabled' : 'Memory Disabled'}
            </button>
            {memories.length > 0 && (
              <button
                onClick={handleClearAllMemories}
                className="px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-medium transition-all flex items-center space-x-1"
                title="Clear all memories"
              >
                <Trash2 className="w-3 h-3" />
                <span>Clear All</span>
              </button>
            )}
          </div>
        </div>

        {/* Add Memory Form */}
        <form onSubmit={handleAddMemory} className="flex items-center space-x-2">
          <input
            type="text"
            value={newMemoryText}
            onChange={(e) => setNewMemoryText(e.target.value)}
            placeholder="Add memory manually (e.g. 'User prefers Python and Tailwind CSS')..."
            className="flex-1 bg-[#241e1a] border border-[#3a3128] focus:border-emerald-500/60 rounded-xl px-3.5 py-2 text-xs text-zinc-100 placeholder-zinc-500 outline-none"
          />
          <button
            type="submit"
            disabled={!newMemoryText.trim()}
            className="px-3.5 py-2 rounded-xl bg-accent-gradient hover:opacity-90 text-white font-semibold text-xs transition-all disabled:opacity-40 flex items-center space-x-1"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add</span>
          </button>
        </form>

        {/* Memories List */}
        <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
          {memories.length > 0 ? (
            memories.map((m) => (
              <div
                key={m.id}
                className="bg-[#241e1a] border border-[#3a3128] hover:border-zinc-500 rounded-xl p-2.5 flex items-center justify-between text-xs text-zinc-200 group transition-all"
              >
                <div className="flex items-center space-x-2 truncate flex-1 min-w-0 pr-2">
                  <span className="text-emerald-400 shrink-0"><Brain className="w-3.5 h-3.5" /></span>
                  <span className="truncate">{m.text || `${m.key}: ${m.value}`}</span>
                </div>
                <button
                  onClick={() => handleDeleteMemory(m.id)}
                  className="p-1 rounded-md text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors opacity-0 group-hover:opacity-100"
                  title="Delete memory"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))
          ) : (
            <div className="text-[11px] text-zinc-500 italic p-2 bg-[#241e1a] rounded-xl border border-[#2e2620]">
              No persistent memories saved yet. Say "Remember that my name is xyz" or add one above!
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
