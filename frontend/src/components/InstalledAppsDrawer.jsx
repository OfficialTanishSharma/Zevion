import React, { useState } from 'react';
import { 
  AppWindow, 
  Search, 
  Play, 
  ExternalLink, 
  CheckCircle2, 
  Globe, 
  FileText, 
  Code, 
  Calculator, 
  Terminal, 
  Folder, 
  Music, 
  Image, 
  Settings 
} from 'lucide-react';

export default function InstalledAppsDrawer({ apps, onLaunchApp }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('All');

  const defaultApps = apps?.length > 0 ? apps : [
    { id: 'chrome', name: 'Google Chrome', category: 'Browser', aliases: ['chrome', 'browser'], icon: 'globe', description: 'Fast, secure web browser by Google' },
    { id: 'notepad', name: 'Notepad', category: 'Productivity', aliases: ['notepad', 'notes', 'editor'], icon: 'file-text', description: 'Standard plain text editor' },
    { id: 'vscode', name: 'Visual Studio Code', category: 'Development', aliases: ['vscode', 'code'], icon: 'code', description: 'Code editing and debugging suite' },
    { id: 'calculator', name: 'Windows Calculator', category: 'Utilities', aliases: ['calc', 'math'], icon: 'calculator', description: 'Standard and scientific calculations' },
    { id: 'terminal', name: 'PowerShell / Terminal', category: 'System', aliases: ['powershell', 'cmd', 'bash'], icon: 'terminal', description: 'System command line shell' },
    { id: 'explorer', name: 'File Explorer', category: 'System', aliases: ['explorer', 'files'], icon: 'folder', description: 'Browse and manage local files' },
    { id: 'spotify', name: 'Spotify Music', category: 'Media', aliases: ['spotify', 'music'], icon: 'music', description: 'Digital music & podcast player' },
    { id: 'paint', name: 'Paint', category: 'Graphics', aliases: ['paint', 'mspaint'], icon: 'image', description: 'Image creation and editor' },
    { id: 'settings', name: 'Windows Settings', category: 'System', aliases: ['settings', 'config'], icon: 'settings', description: 'System preferences and control panel' },
  ];

  const categories = ['All', 'Browser', 'Productivity', 'Development', 'System', 'Utilities', 'Media'];

  const filteredApps = defaultApps.filter(app => {
    const matchesSearch = app.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          app.aliases.some(a => a.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCat = activeCategory === 'All' || app.category === activeCategory;
    return matchesSearch && matchesCat;
  });

  const getAppIcon = (iconName) => {
    switch (iconName) {
      case 'globe': case 'chrome': return <Globe className="w-5 h-5 text-blue-400" />;
      case 'file-text': case 'notepad': return <FileText className="w-5 h-5 text-cyan-400" />;
      case 'code': case 'vscode': return <Code className="w-5 h-5 text-emerald-400" />;
      case 'calculator': return <Calculator className="w-5 h-5 text-amber-400" />;
      case 'terminal': return <Terminal className="w-5 h-5 text-emerald-400" />;
      case 'folder': case 'explorer': return <Folder className="w-5 h-5 text-amber-400" />;
      case 'music': case 'spotify': return <Music className="w-5 h-5 text-green-400" />;
      case 'image': case 'paint': return <Image className="w-5 h-5 text-purple-400" />;
      default: return <Settings className="w-5 h-5 text-zinc-400" />;
    }
  };

  return (
    <div className="flex-1 bg-[#1a1614] p-6 overflow-y-auto text-zinc-100 space-y-6 select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#2e2620] pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400">
            <AppWindow className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-zinc-100 flex items-center space-x-2">
              <span>Windows Installed Applications Registry</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-mono font-semibold">
                Auto-Detected
              </span>
            </h2>
            <p className="text-xs text-zinc-400">Applications scanned from Windows Registry and Start Menu</p>
          </div>
        </div>

        <div className="text-xs font-mono text-zinc-400 bg-[#262019] px-3 py-1.5 rounded-lg border border-[#3a3128]">
          {defaultApps.length} Apps Registered
        </div>
      </div>

      {/* Search & Category Filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search application by name or alias (e.g. 'chrome', 'browser', 'code')..."
            className="w-full bg-[#262019] border border-[#3a3128] focus:border-blue-500/60 rounded-xl pl-9 pr-4 py-2 text-xs text-zinc-100 placeholder-zinc-500 outline-none"
          />
        </div>

        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1">
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setActiveCategory(c)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeCategory === c
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-[#262019] text-zinc-400 hover:text-zinc-200 border border-[#3a3128]'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Applications Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredApps.map((app) => (
          <div
            key={app.id}
            className="bg-[#1f1a17] border border-white/5 hover:border-blue-500/40 rounded-2xl p-5 space-y-3 transition-all shadow-sm flex flex-col justify-between"
          >
            <div className="space-y-2">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-[#241e1a] border border-[#3a3128] flex items-center justify-center shadow-inner">
                    {getAppIcon(app.icon || app.id)}
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-zinc-100">{app.name}</h3>
                    <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono">
                      {app.category}
                    </span>
                  </div>
                </div>

                <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono text-[9px] border border-emerald-500/20">
                  Ready
                </span>
              </div>

              <p className="text-xs text-zinc-400 leading-relaxed line-clamp-2">{app.description}</p>
            </div>

            <div className="pt-2 border-t border-[#2e2620] flex items-center justify-between">
              <div className="text-[10px] text-zinc-500 font-mono truncate max-w-36">
                alias: {app.aliases?.join(', ')}
              </div>

              <button
                onClick={() => onLaunchApp(app.id)}
                className="px-3 py-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600 text-blue-300 hover:text-white font-medium text-xs border border-blue-500/30 transition-all flex items-center space-x-1"
              >
                <Play className="w-3 h-3 fill-current" />
                <span>Launch App</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
