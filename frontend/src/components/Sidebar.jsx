import React, { useState } from 'react';
import { 
  MessageSquare, 
  Monitor, 
  FolderArchive, 
  Zap, 
  AppWindow, 
  ShieldAlert, 
  Settings, 
  Plus, 
  Trash2, 
  Sparkles,
  Terminal,
  Cpu,
  HardDrive,
  CheckCircle2,
  ExternalLink,
  Edit2,
  Check,
  X,
  Globe,
  Youtube,
  NotebookPen,
  FolderPlus,
  Search,
  Camera,
  Rocket,
  BarChart3,
  Download
} from 'lucide-react';

export default function Sidebar({ 
  activeTab, 
  setActiveTab, 
  conversations = [], 
  currentChatId, 
  onSelectChat, 
  onNewChat, 
  onRenameChat,
  onDeleteChat,
  onClearHistory,
  systemInfo,
  onSendPreset
}) {
  const [editingChatId, setEditingChatId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const handleExportChat = async () => {
    if (!currentChatId) return;
    try {
      const res = await fetch(`/api/export/conversation/${currentChatId}`);
      const data = await res.json();
      if (data.success && data.content) {
        const blob = new Blob([data.content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename || 'conversation.md';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      }
    } catch (e) {
      console.error('Export failed:', e);
    }
  };

  const quickPrompts = [
    { label: 'Open Chrome & Search Minecraft', Icon: Globe, color: 'text-blue-400', query: 'open Chrome and search Minecraft' },
    { label: 'Open YouTube & Play Minecraft', Icon: Youtube, color: 'text-rose-400', query: 'open YouTube and play Minecraft survival' },
    { label: 'Open Notepad & Type Notes', Icon: NotebookPen, color: 'text-cyan-400', query: 'open Notepad and type hello brother' },
    { label: 'Open Discord then Chrome', Icon: Rocket, color: 'text-violet-400', query: 'open Discord then open Chrome' },
    { label: 'Open Chrome', Icon: Globe, color: 'text-blue-400', query: 'Open Chrome' },
    { label: 'Open Notepad', Icon: NotebookPen, color: 'text-cyan-400', query: 'Open Notepad' },
    { label: 'Create Projects Folder', Icon: FolderPlus, color: 'text-amber-400', query: 'Create a folder named Projects' },
    { label: 'Search Web for AI', Icon: Search, color: 'text-emerald-400', query: 'Search for something on the web' },
    { label: 'Organize My Files', Icon: FolderArchive, color: 'text-emerald-400', query: 'Organize my files' },
    { label: 'Take Screenshot', Icon: Camera, color: 'text-purple-400', query: 'Take a screenshot' },
  ];

  const handleStartRename = (e, c) => {
    e.stopPropagation();
    setEditingChatId(c.id);
    setEditTitle(c.title);
  };

  const handleSaveRename = (e, id) => {
    e.stopPropagation();
    if (editTitle.trim() && onRenameChat) {
      onRenameChat(id, editTitle.trim());
    }
    setEditingChatId(null);
  };

  const handleCancelRename = (e) => {
    e.stopPropagation();
    setEditingChatId(null);
  };

  return (
    <aside className="w-72 bg-[#141110] border-r border-white/5 flex flex-col h-full select-none text-zinc-300">
      {/* Header / Brand */}
      <div className="p-4 border-b border-white/5 flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-2.5">
          <div className="w-10 h-10 rounded-xl overflow-hidden ring-1 ring-white/10 shadow-lg shadow-orange-500/20 shrink-0">
            <img src="/assets/logo.png" alt="Zevion" className="w-full h-full object-cover" />
          </div>
          <div>
            <h1 className="font-bold text-sm text-zinc-100 flex items-center space-x-1.5 tracking-tight">
              <span>Zevion</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-amber-500/10 text-amber-400 font-mono border border-amber-500/20">AI</span>
            </h1>
            <p className="text-[11px] text-zinc-400">Your AI Desktop Copilot</p>
          </div>
        </div>
      </div>

      {/* Fixed New Chat Button Control */}
      <div className="p-3 shrink-0 border-b border-white/5">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-between px-3 py-2 rounded-xl bg-accent-gradient hover:opacity-90 text-white text-xs font-semibold transition-all group shadow-lg shadow-orange-600/20 border border-white/10"
        >
          <div className="flex items-center space-x-2">
            <Plus className="w-4 h-4 group-hover:scale-110 transition-transform" />
            <span>New Chat</span>
          </div>
          <span className="text-[10px] text-amber-100/80 bg-black/20 px-1.5 py-0.5 rounded font-mono">⌘N</span>
        </button>
      </div>

      {/* Scrollable Middle Body */}
      <div className="flex-1 min-h-0 overflow-y-auto flex flex-col">
        {/* Conversations / Recent Chats Section */}
        <div className="px-3 py-2 shrink-0">
          <div className="text-[10px] uppercase font-semibold tracking-wider text-zinc-400 px-2 py-1 flex items-center justify-between">
            <span>Recent Chats</span>
            <div className="flex items-center space-x-1.5">
              {currentChatId && (
                <button
                  onClick={handleExportChat}
                  className="text-[9px] font-mono text-zinc-500 hover:text-amber-400 flex items-center space-x-1 transition-colors"
                  title="Export current chat as Markdown"
                >
                  <Download className="w-3 h-3" />
                  <span>Export</span>
                </button>
              )}
              <span className="text-[9px] font-mono text-zinc-500">{conversations?.length || 0}</span>
            </div>
          </div>
          {conversations && conversations.length > 0 ? (
            <div className="space-y-0.5 max-h-48 overflow-y-auto pr-1">
              {conversations.map((c) => {
                const isActive = c.id === currentChatId && activeTab === 'chat';
                const isEditing = editingChatId === c.id;

                return (
                  <div
                    key={c.id}
                    onClick={() => {
                      if (onSelectChat) onSelectChat(c.id);
                      setActiveTab('chat');
                    }}
                    className={`group flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs cursor-pointer transition-all ${
                      isActive
                        ? 'bg-amber-500/15 text-amber-400 font-medium border border-amber-500/30'
                        : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
                    }`}
                  >
                    <div className="flex items-center space-x-2 truncate flex-1 min-w-0">
                      <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-amber-400' : 'text-zinc-500'}`} />
                      {isEditing ? (
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onClick={(e) => e.stopPropagation()}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveRename(e, c.id);
                            if (e.key === 'Escape') handleCancelRename(e);
                          }}
                          className="bg-[#171311] border border-amber-500 rounded px-1 py-0.5 text-xs text-zinc-100 outline-none w-full"
                          autoFocus
                        />
                      ) : (
                        <span className="truncate text-[11px]">{c.title || 'Conversation'}</span>
                      )}
                    </div>

                    <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-1">
                      {isEditing ? (
                        <>
                          <button
                            onClick={(e) => handleSaveRename(e, c.id)}
                            className="p-1 hover:text-amber-400 text-zinc-400"
                            title="Save title"
                          >
                            <Check className="w-3 h-3" />
                          </button>
                          <button
                            onClick={handleCancelRename}
                            className="p-1 hover:text-rose-400 text-zinc-400"
                            title="Cancel"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={(e) => handleStartRename(e, c)}
                            className="p-1 hover:text-zinc-200 text-zinc-500"
                            title="Rename chat"
                          >
                            <Edit2 className="w-3 h-3" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (onDeleteChat) onDeleteChat(c.id);
                            }}
                            className="p-1 hover:text-rose-400 text-zinc-500"
                            title="Delete chat"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="px-2 py-1.5 text-[11px] text-zinc-500 italic">
              No recent chats
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <div className="px-3 py-1 space-y-1 mt-1 border-t border-white/5 shrink-0">
        <div className="text-[10px] uppercase font-semibold tracking-wider text-zinc-400 px-2 py-1">Workspace Modes</div>
        <button
          onClick={() => setActiveTab('chat')}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'chat' 
              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' 
              : 'hover:bg-white/5 text-zinc-300 hover:text-zinc-100'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          <span>AI Chat & Commands</span>
        </button>

        <button
          onClick={() => setActiveTab('organizer')}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'organizer' 
              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' 
              : 'hover:bg-white/5 text-zinc-300 hover:text-zinc-100'
          }`}
        >
          <FolderArchive className="w-4 h-4" />
          <span>File Organizer Studio</span>
        </button>

        <button
          onClick={() => setActiveTab('workflows')}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'workflows' 
              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' 
              : 'hover:bg-white/5 text-zinc-300 hover:text-zinc-100'
          }`}
        >
          <Zap className="w-4 h-4" />
          <span>Smart Workflows</span>
        </button>

        <button
          onClick={() => setActiveTab('apps')}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'apps' 
              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' 
              : 'hover:bg-white/5 text-zinc-300 hover:text-zinc-100'
          }`}
        >
          <AppWindow className="w-4 h-4" />
          <span>Installed Apps Registry</span>
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'audit' 
              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' 
              : 'hover:bg-white/5 text-zinc-300 hover:text-zinc-100'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Safety Audit Logs</span>
        </button>

        <button
          onClick={() => setActiveTab('usage')}
          className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'usage' 
              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' 
              : 'hover:bg-white/5 text-zinc-300 hover:text-zinc-100'
          }`}
        >
          <BarChart3 className="w-4 h-4" />
          <span>AI Usage Stats</span>
        </button>
      </div>

      {/* Quick Prompts Section */}
      <div className="px-3 py-2 border-t border-white/5 mt-1">
        <div className="text-[10px] uppercase font-semibold tracking-wider text-zinc-400 px-2 py-1 mb-1">
          Quick Natural Commands
        </div>
        <div className="grid grid-cols-1 gap-1 max-h-28 overflow-y-auto pr-1">
          {quickPrompts.map((p, idx) => {
            const PromptIcon = p.Icon;
            return (
              <button
                key={idx}
                onClick={() => onSendPreset(p.query)}
                className="w-full text-left flex items-center space-x-2 px-2.5 py-1.5 rounded-lg text-[11px] bg-[#1f1a17] hover:bg-[#2a231d] text-zinc-300 hover:text-zinc-100 border border-white/5 hover:border-amber-500/30 transition-all truncate group"
              >
                <span className={`w-5 h-5 rounded-md bg-white/5 border border-white/5 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform`}>
                  <PromptIcon className={`w-3 h-3 ${p.color}`} />
                </span>
                <span className="truncate">{p.label}</span>
              </button>
            );
          })}
        </div>
      </div>
      </div>

      {/* System Resources Status Card */}
      <div className="mt-auto p-3 border-t border-white/5 bg-[#141110]">
        <div className="p-2.5 rounded-xl bg-[#1f1a17] border border-white/5 text-[11px] space-y-2">
          <div className="flex items-center justify-between text-zinc-400">
            <span className="flex items-center space-x-1.5 font-medium">
              <Cpu className="w-3.5 h-3.5 text-amber-400" />
              <span>Windows Controller</span>
            </span>
            <span className="px-1.5 py-0.5 rounded text-[9px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center space-x-1">
              <span className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
              <span>Active</span>
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[10px] text-zinc-400">
            <div className="bg-[#262019] p-1.5 rounded-lg border border-white/5">
              <div className="text-zinc-400">CPU Load</div>
              <div className="font-semibold text-zinc-100">{(systemInfo?.cpu_usage_pct ?? systemInfo?.cpu_percent ?? 0)}%</div>
            </div>
            <div className="bg-[#262019] p-1.5 rounded-lg border border-white/5">
              <div className="text-zinc-400">RAM Used</div>
              <div className="font-semibold text-zinc-100">{(systemInfo?.ram_usage_pct ?? systemInfo?.ram_percent ?? 0)}%</div>
            </div>
          </div>
        </div>

        {/* Settings button */}
        <button
          onClick={() => setActiveTab('settings')}
          className="w-full mt-2 flex items-center justify-between px-3 py-2 rounded-lg bg-[#1f1a17] hover:bg-[#2a231d] text-zinc-400 hover:text-zinc-200 text-xs transition-all border border-white/5"
        >
          <div className="flex items-center space-x-2">
            <Settings className="w-3.5 h-3.5" />
            <span>Agent Settings</span>
          </div>
          <span className="text-[10px] text-zinc-500">v2.0</span>
        </button>
      </div>
    </aside>
  );
}
