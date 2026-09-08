import {
  AppWindow,
  Gamepad2,
  FolderPlus,
  FilePlus2,
  BookOpen,
  Trash2,
  Globe,
  Terminal,
  Keyboard,
  Camera,
  MousePointer2,
  BarChart3,
  Brain,
  Target,
  ShieldCheck,
  ShieldAlert,
  Zap,
  CheckCircle2,
  Rocket,
  FolderArchive,
  Mouse,
  FileText,
  Clipboard,
  ClipboardPaste,
  Search,
  PlayCircle,
  SkipForward,
  Battery,
  BatteryCharging,
  NotebookPen,
  FolderOpen,
  ListChecks,
  FileSearch,
  Pencil,
  ExternalLink,
  Download,
  Undo2,
  BellRing,
  ScanEye,
} from 'lucide-react';

/**
 * Central, consistent icon map for desktop tool actions.
 * Every action card in the app renders its icon through this helper so the
 * whole UI shares one crisp SVG icon set (no emojis anywhere).
 */

const TOOL_META = {
  open_application: { Icon: Rocket, color: 'text-blue-400', bg: 'bg-blue-500/15', border: 'border-blue-500/30' },
  create_project: { Icon: Gamepad2, color: 'text-violet-400', bg: 'bg-violet-500/15', border: 'border-violet-500/30' },
  create_folder: { Icon: FolderPlus, color: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/30' },
  create_file: { Icon: FilePlus2, color: 'text-sky-400', bg: 'bg-sky-500/15', border: 'border-sky-500/30' },
  write_file: { Icon: FilePlus2, color: 'text-sky-400', bg: 'bg-sky-500/15', border: 'border-sky-500/30' },
  read_file: { Icon: BookOpen, color: 'text-cyan-400', bg: 'bg-cyan-500/15', border: 'border-cyan-500/30' },
  delete_file: { Icon: Trash2, color: 'text-rose-400', bg: 'bg-rose-500/15', border: 'border-rose-500/30' },
  open_website: { Icon: Globe, color: 'text-indigo-400', bg: 'bg-indigo-500/15', border: 'border-indigo-500/30' },
  organize_files: { Icon: FolderArchive, color: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30' },
  execute_command: { Icon: Terminal, color: 'text-violet-400', bg: 'bg-violet-500/15', border: 'border-violet-500/30' },
  type_text: { Icon: Keyboard, color: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/30' },
  take_screenshot: { Icon: Camera, color: 'text-purple-400', bg: 'bg-purple-500/15', border: 'border-purple-500/30' },
  control_mouse: { Icon: MousePointer2, color: 'text-pink-400', bg: 'bg-pink-500/15', border: 'border-pink-500/30' },
  get_system_info: { Icon: BarChart3, color: 'text-teal-400', bg: 'bg-teal-500/15', border: 'border-teal-500/30' },
  open_application_window: { Icon: AppWindow, color: 'text-blue-400', bg: 'bg-blue-500/15', border: 'border-blue-500/30' },
  confirmed_action: { Icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30' },
  clipboard_set: { Icon: Clipboard, color: 'text-cyan-400', bg: 'bg-cyan-500/15', border: 'border-cyan-500/30' },
  clipboard_get: { Icon: ClipboardPaste, color: 'text-cyan-400', bg: 'bg-cyan-500/15', border: 'border-cyan-500/30' },
  find_files: { Icon: Search, color: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30' },
  media_control: { Icon: PlayCircle, color: 'text-rose-400', bg: 'bg-rose-500/15', border: 'border-rose-500/30' },
  press_keys: { Icon: Keyboard, color: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/30' },
  get_battery: { Icon: Battery, color: 'text-emerald-400', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30' },
  add_note: { Icon: NotebookPen, color: 'text-yellow-400', bg: 'bg-yellow-500/15', border: 'border-yellow-500/30' },
  list_directory: { Icon: FolderOpen, color: 'text-orange-400', bg: 'bg-orange-500/15', border: 'border-orange-500/30' },
  web_search: { Icon: Globe, color: 'text-blue-400', bg: 'bg-blue-500/15', border: 'border-blue-500/30' },
  web_fetch: { Icon: ExternalLink, color: 'text-indigo-400', bg: 'bg-indigo-500/15', border: 'border-indigo-500/30' },
  download_file: { Icon: Download, color: 'text-sky-400', bg: 'bg-sky-500/15', border: 'border-sky-500/30' },
  grep_files: { Icon: FileSearch, color: 'text-cyan-400', bg: 'bg-cyan-500/15', border: 'border-cyan-500/30' },
  edit_file: { Icon: Pencil, color: 'text-violet-400', bg: 'bg-violet-500/15', border: 'border-violet-500/30' },
  undo_edit: { Icon: Undo2, color: 'text-fuchsia-400', bg: 'bg-fuchsia-500/15', border: 'border-fuchsia-500/30' },
  set_reminder: { Icon: BellRing, color: 'text-amber-400', bg: 'bg-amber-500/15', border: 'border-amber-500/30' },
  analyze_screenshot: { Icon: ScanEye, color: 'text-teal-400', bg: 'bg-teal-500/15', border: 'border-teal-500/30' },
};

export function getToolIcon(toolName) {
  const meta = TOOL_META[toolName] || { Icon: Mouse, color: 'text-zinc-400', bg: 'bg-zinc-500/15', border: 'border-zinc-500/30' };
  return meta;
}

const THOUGHT_META = {
  understanding: { Icon: Brain, color: 'text-emerald-400' },
  planning: { Icon: Target, color: 'text-blue-400' },
  safety: { Icon: ShieldCheck, color: 'text-emerald-400', dangerColor: 'text-rose-400', dangerIcon: ShieldAlert },
  execution: { Icon: Zap, color: 'text-amber-400' },
  completed: { Icon: CheckCircle2, color: 'text-emerald-400' },
};

export function getThoughtIcon(step, level) {
  const meta = THOUGHT_META[step] || { Icon: Brain, color: 'text-emerald-400' };
  if (step === 'safety' && level === 'dangerous') {
    return { Icon: ShieldAlert, color: meta.dangerColor };
  }
  return meta;
}

// Re-export the raw icons for direct use elsewhere (quick prompts, workflows)
export {
  Rocket,
  Gamepad2,
  FolderPlus,
  FilePlus2,
  BookOpen,
  Trash2,
  Globe,
  Terminal,
  Keyboard,
  Camera,
  MousePointer2,
  BarChart3,
  Brain,
  Target,
  ShieldCheck,
  ShieldAlert,
  Zap,
  CheckCircle2,
  AppWindow,
  FolderArchive,
  FileText,
  Clipboard,
  ClipboardPaste,
  Search,
  PlayCircle,
  SkipForward,
  Battery,
  BatteryCharging,
  NotebookPen,
  FolderOpen,
  ListChecks,
  FileSearch,
  Pencil,
  ExternalLink,
  Download,
  Undo2,
  BellRing,
  ScanEye,
};
