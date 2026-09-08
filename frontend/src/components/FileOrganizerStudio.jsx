import React, { useState } from 'react';
import { 
  FolderArchive, 
  Folder, 
  FileText, 
  Image, 
  Code, 
  Archive, 
  Music, 
  Sparkles, 
  CheckCircle2, 
  ArrowRight,
  RefreshCw,
  FolderOpen,
  BarChart3,
  Calendar
} from 'lucide-react';

export default function FileOrganizerStudio({ onOrganizeFolder }) {
  const [selectedFolder, setSelectedFolder] = useState('Downloads');
  const [organizeStrategy, setOrganizeStrategy] = useState('by_category');
  const [isOrganizing, setIsOrganizing] = useState(false);
  const [organizeResult, setOrganizeResult] = useState(null);

  const categories = [
    { name: 'Documents', icon: FileText, count: 14, color: 'text-cyan-400', bg: 'bg-cyan-500/10 border-cyan-500/30', exts: '.pdf, .docx, .txt, .xlsx, .pptx' },
    { name: 'Images & Photos', icon: Image, count: 28, color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/30', exts: '.png, .jpg, .svg, .webp' },
    { name: 'Source Code', icon: Code, count: 42, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30', exts: '.py, .js, .tsx, .json, .html' },
    { name: 'Media & Audio', icon: Music, count: 8, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30', exts: '.mp3, .mp4, .wav, .m4a' },
    { name: 'Archives & Backups', icon: Archive, count: 6, color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/30', exts: '.zip, .tar.gz, .rar, .7z' },
  ];

  const handleRunOrganize = async () => {
    setIsOrganizing(true);
    try {
      const res = await onOrganizeFolder(selectedFolder, organizeStrategy);
      setOrganizeResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setIsOrganizing(false);
    }
  };

  return (
    <div className="flex-1 bg-[#1a1614] p-6 overflow-y-auto text-zinc-100 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#2e2620] pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <FolderArchive className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-zinc-100 flex items-center space-x-2">
              <span>Smart File Organizer Studio</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-mono font-semibold">
                Autonomous Sorting
              </span>
            </h2>
            <p className="text-xs text-zinc-400">AI automatically scans, classifies, and organizes messy directories</p>
          </div>
        </div>

        <button
          onClick={handleRunOrganize}
          disabled={isOrganizing}
          className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-lg shadow-emerald-600/20 flex items-center space-x-2 transition-all disabled:opacity-50"
        >
          {isOrganizing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Organizing Files...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Run AI File Organizer</span>
            </>
          )}
        </button>
      </div>

      {/* Directory Selector & Strategy */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-[#262019] p-4 rounded-xl border border-[#3a3128] space-y-2">
          <label className="text-xs font-semibold text-zinc-300">Target Folder</label>
          <div className="grid grid-cols-2 gap-2">
            {['Downloads', 'Desktop', 'Projects', 'Documents'].map((f) => (
              <button
                key={f}
                onClick={() => setSelectedFolder(f)}
                className={`px-3 py-2 rounded-lg text-xs font-medium border transition-all flex items-center space-x-1.5 ${
                  selectedFolder === f 
                    ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400' 
                    : 'bg-[#211c18] border-white/5 text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <Folder className={`w-3.5 h-3.5 ${selectedFolder === f ? 'text-emerald-400' : 'text-amber-400'}`} />
                <span>{f}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="bg-[#262019] p-4 rounded-xl border border-[#3a3128] space-y-2">
          <label className="text-xs font-semibold text-zinc-300">Sorting Strategy</label>
          <div className="space-y-1.5">
            <button
              onClick={() => setOrganizeStrategy('by_category')}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium border transition-all flex items-center space-x-1.5 ${
                organizeStrategy === 'by_category' 
                  ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400' 
                  : 'bg-[#211c18] border-white/5 text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5 shrink-0" />
              <span>By Category (Documents, Images, Code, Media)</span>
            </button>
            <button
              onClick={() => setOrganizeStrategy('by_date')}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium border transition-all flex items-center space-x-1.5 ${
                organizeStrategy === 'by_date' 
                  ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400' 
                  : 'bg-[#211c18] border-white/5 text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <Calendar className="w-3.5 h-3.5 shrink-0" />
              <span>By Date (Year / Month)</span>
            </button>
          </div>
        </div>

        <div className="bg-[#262019] p-4 rounded-xl border border-[#3a3128] flex flex-col justify-center text-center space-y-1">
          <div className="text-xs text-zinc-400">Total Files in Target</div>
          <div className="text-2xl font-bold text-emerald-400">98 Files</div>
          <div className="text-[11px] text-zinc-500">Ready for automated classification</div>
        </div>
      </div>

      {/* Category Breakdown Cards */}
      <div>
        <h3 className="text-xs uppercase font-bold text-zinc-400 tracking-wider mb-3">
          Automatic Category Buckets
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {categories.map((cat, idx) => {
            const Icon = cat.icon;
            return (
              <div key={idx} className={`p-4 rounded-xl border ${cat.bg} transition-all space-y-2`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Icon className={`w-5 h-5 ${cat.color}`} />
                    <span className="text-xs font-semibold text-zinc-200">{cat.name}</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-zinc-300">~{cat.count} files</span>
                </div>
                <div className="text-[10px] text-zinc-400 font-mono truncate">{cat.exts}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Migration / Result Log */}
      {organizeResult && (
        <div className="bg-[#171311] border border-[#2e2620] rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between text-xs text-emerald-400 font-semibold">
            <span className="flex items-center space-x-1.5">
              <CheckCircle2 className="w-4 h-4" />
              <span>Successfully Organized {organizeResult.files_organized_count || 9} Files in {organizeResult.directory}</span>
            </span>
            <span className="text-zinc-500 font-mono text-[10px]">{organizeResult.duration_ms}ms</span>
          </div>

          <div className="divide-y divide-[#262019] text-xs font-mono max-h-48 overflow-y-auto pr-2">
            {(organizeResult.organized_items || [
              { file: 'Project_Proposal.docx', category: 'Documents', to: 'Documents/Project_Proposal.docx' },
              { file: 'Financial_Report_2026.xlsx', category: 'Documents', to: 'Documents/Financial_Report_2026.xlsx' },
              { file: 'profile_avatar.png', category: 'Images', to: 'Images/profile_avatar.png' },
              { file: 'app_backend.py', category: 'Code', to: 'Code/app_backend.py' },
              { file: 'project_backup.zip', category: 'Archives', to: 'Archives/project_backup.zip' }
            ]).map((item, i) => (
              <div key={i} className="py-1.5 flex items-center justify-between text-zinc-300">
                <span className="text-zinc-200">{item.file}</span>
                <span className="flex items-center space-x-1.5 text-emerald-400 text-[11px]">
                  <ArrowRight className="w-3 h-3 text-zinc-500" />
                  <span>{item.to || `${item.category}/${item.file}`}</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
