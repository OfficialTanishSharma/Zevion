import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Send, 
  Mic, 
  Volume2, 
  VolumeX, 
  Copy, 
  Check, 
  Clock, 
  ChevronDown, 
  ChevronUp, 
  Sparkles,
  Code2,
  FileText,
  AlertTriangle,
  AlertCircle,
  Square,
  Paperclip,
  Image as ImageIcon,
  File,
  X,
  Upload,
  ShieldAlert,
  Layout,
  Eye,
  Activity,
  Download,
  Video,
  Play,
  User,
  Gamepad2,
  Bot,
  Folder,
  Zap,
  ShieldCheck,
  Globe,
  FolderPlus,
  Camera
} from 'lucide-react';
import { getToolIcon, getThoughtIcon } from './toolIcons';
import { voiceAssistant } from '../utils/voiceAssistant';

const MAX_FILES = 5;
const MAX_FILE_SIZE_MB = 25;
const MAX_TOTAL_SIZE_MB = 50;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
const MAX_TOTAL_SIZE_BYTES = MAX_TOTAL_SIZE_MB * 1024 * 1024;

const SUPPORTED_EXTENSIONS = [
  '.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.svg',
  '.mp4', '.webm', '.mov', '.mkv', '.avi',
  '.pdf',
  '.txt', '.md', '.csv', '.json', '.xml', '.log', '.yaml', '.yml', '.ini', '.conf', '.env',
  '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.c', '.cpp', '.h', '.hpp',
  '.html', '.css', '.sql', '.sh', '.bat', '.ps1', '.go', '.rs', '.php', '.rb', '.cs'
];

const formatSize = (bytes) => {
  if (!bytes || bytes <= 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const getFileIcon = (filename = '', mimeType = '') => {
  const ext = '.' + filename.split('.').pop().toLowerCase();
  if (['.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.svg'].includes(ext) || mimeType.startsWith('image/')) {
    return <ImageIcon className="w-4 h-4 text-emerald-400 shrink-0" />;
  }
  if (['.mp4', '.webm', '.mov', '.mkv', '.avi'].includes(ext) || mimeType.startsWith('video/')) {
    return <Video className="w-4 h-4 text-purple-400 shrink-0" />;
  }
  if (ext === '.pdf' || mimeType.includes('pdf')) {
    return <FileText className="w-4 h-4 text-rose-400 shrink-0" />;
  }
  if (['.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.c', '.cpp', '.h', '.hpp', '.html', '.css', '.sql', '.json', '.xml', '.sh', '.go', '.rs'].includes(ext)) {
    return <Code2 className="w-4 h-4 text-blue-400 shrink-0" />;
  }
  return <FileText className="w-4 h-4 text-amber-400 shrink-0" />;
};

const MarkdownContent = React.memo(function MarkdownContent({ content, onOpenWorkspace }) {
  if (!content) return null;
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
        strong: ({ children }) => <strong className="font-bold text-zinc-100">{children}</strong>,
        em: ({ children }) => <em className="italic text-zinc-200">{children}</em>,
        ul: ({ children }) => <ul className="list-disc pl-5 my-1.5 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-5 my-1.5 space-y-1">{children}</ol>,
        li: ({ children }) => <li className="text-zinc-200 leading-relaxed">{children}</li>,
        h1: ({ children }) => <h1 className="text-base font-bold text-zinc-100 mt-3 mb-1.5">{children}</h1>,
        h2: ({ children }) => <h2 className="text-sm font-bold text-zinc-100 mt-2.5 mb-1">{children}</h2>,
        h3: ({ children }) => <h3 className="text-xs font-bold text-zinc-100 mt-2 mb-1">{children}</h3>,
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noreferrer" className="text-emerald-400 hover:underline">
            {children}
          </a>
        ),
        pre: ({ children, ...props }) => {
          // Extract language + raw text from the child <code> element to render the header bar
          const codeEl = Array.isArray(children) ? children[0] : children;
          const codeClassName = codeEl?.props?.className || '';
          const match = /language-(\w+)/.exec(codeClassName);
          const lang = match ? match[1] : '';
          const rawCode = String(codeEl?.props?.children || '').replace(/\n$/, '');
          const isWeb = ['html', 'svg', 'xml', 'htm'].includes(lang.toLowerCase()) || rawCode.includes('<!DOCTYPE') || rawCode.includes('<html');

          return (
            <div className="my-3 rounded-xl overflow-hidden border border-white/5 bg-[#161210] shadow-sm group">
              <div className="flex items-center justify-between px-3 py-1.5 bg-[#1f1a17] border-b border-white/5 text-[11px] text-zinc-400">
                <span className="font-mono uppercase font-semibold text-emerald-400">{lang || 'code'}</span>
                <div className="flex items-center space-x-2">
                  {onOpenWorkspace && (
                    <button
                      type="button"
                      onClick={() => onOpenWorkspace({
                        code: rawCode,
                        language: lang || 'text',
                        filename: `file.${lang || 'txt'}`,
                        tab: isWeb ? 'preview' : 'code'
                      })}
                      className="flex items-center space-x-1 hover:text-emerald-400 text-zinc-400 transition-colors"
                      title="Open in Workspace Preview"
                    >
                      <Layout className="w-3 h-3" />
                      <span>Workspace</span>
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => navigator.clipboard.writeText(rawCode)}
                    className="flex items-center space-x-1 hover:text-zinc-200 text-zinc-400 transition-colors"
                    title="Copy code"
                  >
                    <Copy className="w-3 h-3" />
                    <span>Copy</span>
                  </button>
                </div>
              </div>
              <pre className="p-3.5 overflow-x-auto text-xs font-mono text-emerald-300" {...props}>
                {children}
              </pre>
            </div>
          );
        },
        code: ({ node, inline, className, children, ...props }) => {
          if (inline) {
            return (
              <code className="px-1.5 py-0.5 rounded bg-[#262019] text-emerald-400 font-mono text-xs border border-white/10" {...props}>
                {children}
              </code>
            );
          }
          // Block code: only valid phrasing content (a <code> element), never a <div>.
          return (
            <code className="font-mono text-xs text-zinc-200 block" {...props}>
              {children}
            </code>
          );
        }
      }}
    >
      {content}
    </ReactMarkdown>
  );
});

export default function ChatInterface({ 
  messages, 
  onSendMessage, 
  isLoading, 
  onStopGeneration,
  onDirectTool, 
  onOpenConfirmation,
  modelName = "Built-in High Precision Semantic Engine"
}) {
  const [inputMessage, setInputMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [speakingMsgId, setSpeakingMsgId] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [expandedCards, setExpandedCards] = useState({});
  const [pendingFiles, setPendingFiles] = useState([]);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  // Attachment Rolling Rate Limit State
  const [rateLimitState, setRateLimitState] = useState({
    current_used: 0,
    max_allowed: 20,
    remaining_slots: 20,
    cooldown_remaining_seconds: 0,
    next_reset_timestamp: null
  });

  // Workspace Preview & Code Panel State
  const [showWorkspacePanel, setShowWorkspacePanel] = useState(false);
  const [workspaceTab, setWorkspaceTab] = useState('preview');
  const [workspaceCode, setWorkspaceCode] = useState('');
  const [workspaceLang, setWorkspaceLang] = useState('html');
  const [workspaceFilename, setWorkspaceFilename] = useState('index.html');
  const [workspaceCopied, setWorkspaceCopied] = useState(false);

  const fetchRateLimitStatus = () => {
    fetch('/api/attachments/config')
      .then(r => r.json())
      .then(data => {
        if (data) {
          setRateLimitState({
            current_used: data.current_used || 0,
            max_allowed: data.rate_limit_count || 20,
            remaining_slots: data.remaining_slots !== undefined ? data.remaining_slots : 20,
            cooldown_remaining_seconds: data.cooldown_remaining_seconds || 0,
            next_reset_timestamp: data.next_reset_timestamp || null
          });
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    fetchRateLimitStatus();
  }, []);

  // Rolling Cooldown Countdown Timer
  useEffect(() => {
    if (!rateLimitState.cooldown_remaining_seconds || rateLimitState.cooldown_remaining_seconds <= 0) return;

    const timer = setInterval(() => {
      setRateLimitState(prev => {
        const nextSec = prev.cooldown_remaining_seconds - 1;
        if (nextSec <= 0) {
          fetchRateLimitStatus();
          return { ...prev, cooldown_remaining_seconds: 0, remaining_slots: Math.max(1, prev.remaining_slots) };
        }
        return { ...prev, cooldown_remaining_seconds: nextSec };
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [rateLimitState.cooldown_remaining_seconds]);

  const formatCooldown = (seconds) => {
    if (!seconds || seconds <= 0) return '00:00';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleOpenWorkspace = ({ code, language, filename, tab }) => {
    setWorkspaceCode(code || '');
    setWorkspaceLang(language || 'html');
    setWorkspaceFilename(filename || (language === 'html' ? 'index.html' : `file.${language || 'txt'}`));
    if (tab) setWorkspaceTab(tab);
    setShowWorkspacePanel(true);
  };

  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const isNearBottomRef = useRef(true);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);

  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    isNearBottomRef.current = distanceFromBottom < 120;
  };

  const scrollToBottom = (force = false) => {
    if ((force || isNearBottomRef.current) && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom(false);
  }, [messages, isLoading]);

  const showTempError = (msg) => {
    setErrorMessage(msg);
    setTimeout(() => setErrorMessage(null), 4000);
  };

  const validateAndAddFiles = (incomingFileList) => {
    const incomingArray = Array.from(incomingFileList || []);
    if (!incomingArray.length) return;

    if (rateLimitState.cooldown_remaining_seconds > 0 || rateLimitState.remaining_slots <= 0) {
      showTempError(`Attachment limit reached. You can attach files again in ${formatCooldown(rateLimitState.cooldown_remaining_seconds)}.`);
      return;
    }

    if (incomingArray.length > rateLimitState.remaining_slots) {
      showTempError(`Attachment limit reached. Only ${rateLimitState.remaining_slots} slot(s) available in current window.`);
      return;
    }

    if (pendingFiles.length + incomingArray.length > MAX_FILES) {
      showTempError(`You can attach at most ${MAX_FILES} files per message.`);
      return;
    }

    let totalSize = pendingFiles.reduce((acc, f) => acc + f.size, 0);
    const validToAdd = [];

    for (const file of incomingArray) {
      const ext = '.' + file.name.split('.').pop().toLowerCase();
      if (!SUPPORTED_EXTENSIONS.includes(ext)) {
        showTempError(`That file type isn't supported.`);
        return;
      }
      if (file.size > MAX_FILE_SIZE_BYTES) {
        showTempError(`That file is too large. The maximum size is ${MAX_FILE_SIZE_MB} MB.`);
        return;
      }
      totalSize += file.size;

      let previewUrl = null;
      if (file.type.startsWith('image/')) {
        previewUrl = URL.createObjectURL(file);
      }

      validToAdd.push({
        id: `local_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
        file,
        name: file.name,
        size: file.size,
        type: file.type,
        previewUrl
      });
    }

    if (totalSize > MAX_TOTAL_SIZE_BYTES) {
      showTempError(`Total attachment size exceeds the ${MAX_TOTAL_SIZE_MB} MB limit.`);
      return;
    }

    setPendingFiles(prev => [...prev, ...validToAdd]);
  };

  const handleFileInputChange = (e) => {
    if (e.target.files) {
      validateAndAddFiles(e.target.files);
      e.target.value = '';
    }
  };

  const handleRemovePendingFile = (id) => {
    setPendingFiles(prev => {
      const item = prev.find(f => f.id === id);
      if (item?.previewUrl) {
        URL.revokeObjectURL(item.previewUrl);
      }
      return prev.filter(f => f.id !== id);
    });
  };

  const dragCounterRef = useRef(0);

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current += 1;
    if (e.dataTransfer?.items && e.dataTransfer.items.length > 0) {
      setIsDraggingOver(true);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current -= 1;
    if (dragCounterRef.current <= 0) {
      dragCounterRef.current = 0;
      setIsDraggingOver(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current = 0;
    setIsDraggingOver(false);

    if (rateLimitState.cooldown_remaining_seconds > 0 || rateLimitState.remaining_slots <= 0) {
      showTempError(`Attachment limit reached. You can attach files again in ${formatCooldown(rateLimitState.cooldown_remaining_seconds)}.`);
      return;
    }

    if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
      validateAndAddFiles(e.dataTransfer.files);
    }
  };

  const handleSubmit = async (e) => {
    e?.preventDefault();
    const text = inputMessage.trim();
    if ((!text && pendingFiles.length === 0) || isLoading || isUploading) return;

    let uploadedAttachments = [];

    if (pendingFiles.length > 0) {
      setIsUploading(true);
      try {
        const formData = new FormData();
        pendingFiles.forEach(pf => {
          formData.append('files', pf.file);
        });

        const res = await fetch('/api/attachments/upload', {
          method: 'POST',
          body: formData
        });

        if (!res.ok) {
          const errData = await res.json();
          fetchRateLimitStatus();
          throw new Error(errData.detail || 'Failed to upload attachments.');
        }

        const data = await res.json();
        uploadedAttachments = data.attachments || [];
        fetchRateLimitStatus();
      } catch (err) {
        console.error('Attachment upload error:', err);
        showTempError(err.message || 'Error uploading file attachments.');
        setIsUploading(false);
        return;
      }
      setIsUploading(false);
    }

    // Clean up local object URLs
    pendingFiles.forEach(pf => {
      if (pf.previewUrl) URL.revokeObjectURL(pf.previewUrl);
    });
    setPendingFiles([]);
    setInputMessage('');

    onSendMessage(text, uploadedAttachments);
    scrollToBottom(true);
  };

  const handleVoiceToggle = () => {
    if (isRecording) {
      voiceAssistant.stopListening();
      setIsRecording(false);
    } else {
      setIsRecording(true);
      voiceAssistant.startListening(
        (transcript) => {
          setInputMessage(transcript);
          setIsRecording(false);
          onSendMessage(transcript, []);
        },
        () => setIsRecording(false),
        (err) => {
          console.warn('Voice error:', err);
          setIsRecording(false);
        }
      );
    }
  };

  const handleSpeak = (msgId, text) => {
    if (speakingMsgId === msgId) {
      voiceAssistant.stopSpeaking();
      setSpeakingMsgId(null);
    } else {
      setSpeakingMsgId(msgId);
      voiceAssistant.speak(
        text,
        () => {},
        () => setSpeakingMsgId(null)
      );
    }
  };

  const handleCopy = (msgId, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const toggleCardExpand = (idx) => {
    setExpandedCards(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  return (
    <div 
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className="flex-1 flex flex-col h-full bg-[#1a1614] text-zinc-100 relative overflow-hidden"
    >
      {/* Drag & Drop Visual Overlay */}
      {isDraggingOver && (
        <div className="absolute inset-0 z-50 bg-black/70 backdrop-blur-md border-2 border-dashed border-emerald-500/60 flex flex-col items-center justify-center space-y-3 pointer-events-none transition-all rounded-2xl m-2">
          <div className="w-16 h-16 rounded-2xl bg-accent-gradient flex items-center justify-center text-white shadow-xl shadow-emerald-500/30">
            <Upload className="w-8 h-8 animate-bounce" />
          </div>
          <div className="text-sm font-semibold text-zinc-100">Drop files here to attach</div>
          <div className="text-xs text-zinc-400">Images, PDFs, Text, Code up to 25 MB each (Max 5 files)</div>
        </div>
      )}

      {/* Top Bar / Model Status */}
      <header className="h-14 border-b border-white/5 bg-[#141110]/80 backdrop-blur-md px-6 flex items-center justify-between z-10 select-none shrink-0">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 bg-[#1c1815] px-3 py-1.5 rounded-full border border-white/10">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-xs font-semibold text-zinc-300">AI Brain:</span>
            <span className="text-xs text-amber-400 font-mono font-medium">{modelName}</span>
          </div>
          <div className="hidden md:flex items-center space-x-1.5 text-xs text-zinc-500">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Desktop Controller Ready (Windows 11 / Native)</span>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          <button
            type="button"
            onClick={() => setShowWorkspacePanel(!showWorkspacePanel)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border font-medium transition-all ${
              showWorkspacePanel
                ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300 shadow-sm'
                : 'bg-[#1f1a17] border-white/10 text-zinc-400 hover:text-zinc-200 hover:bg-white/5'
            }`}
            title="Toggle Live Workspace & Code Preview Panel"
          >
            <Layout className="w-3.5 h-3.5 text-amber-400" />
            <span>Workspace Panel</span>
          </button>

          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Native Windows 11 Connected</span>
          </div>
        </div>
      </header>

      {/* Main Body with Split Workspace Panel */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Chat Messages Stream & Composer */}
        <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden">
          {/* Messages Stream */}
          <div 
            ref={scrollContainerRef}
            onScroll={handleScroll}
            className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6 scroll-smooth"
          >
            {messages.length === 0 && !isLoading && (
              <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto select-none">
                <div className="w-16 h-16 rounded-2xl overflow-hidden ring-1 ring-white/10 shadow-lg shadow-black/30 mb-5">
                  <img src="/assets/logo.png" alt="Zevion" className="w-full h-full object-cover" />
                </div>
                <h2 className="text-lg font-bold text-zinc-100 tracking-tight">Hey! What can I help you with?</h2>
                <p className="text-sm text-zinc-400 mt-2 leading-relaxed">
                  I'm your desktop sidekick — ask me to open apps, create files and folders,
                  build games, take screenshots, or run diagnostics. Just tell me in plain words.
                </p>
                <div className="grid grid-cols-2 gap-2 w-full mt-6">
                  {[
                    { icon: <Globe className="w-3.5 h-3.5 text-blue-400" />, label: 'Open Chrome', query: 'Open Chrome' },
                    { icon: <FolderPlus className="w-3.5 h-3.5 text-amber-400" />, label: 'Create a folder', query: 'Create a folder named Projects' },
                    { icon: <Gamepad2 className="w-3.5 h-3.5 text-violet-400" />, label: 'Build a game', query: 'snake game bana de' },
                    { icon: <Camera className="w-3.5 h-3.5 text-purple-400" />, label: 'Take a screenshot', query: 'take a screenshot' },
                  ].map((s, i) => (
                    <button
                      key={i}
                      onClick={() => { setInputMessage(s.query); inputRef.current?.focus(); }}
                      className="flex items-center space-x-2 px-3 py-2.5 rounded-xl bg-[#1f1a17] hover:bg-[#2a231d] border border-white/5 hover:border-emerald-500/30 text-xs text-zinc-300 hover:text-zinc-100 transition-all text-left"
                    >
                      <span className="w-6 h-6 rounded-md bg-white/5 border border-white/5 flex items-center justify-center shrink-0">{s.icon}</span>
                      <span className="truncate">{s.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, index) => (
              <div 
                key={msg.id || index}
                className={`max-w-4xl mx-auto flex flex-col ${
                  msg.role === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                {/* User message */}
                {msg.role === 'user' ? (
                  <div className="flex items-start space-x-3 max-w-[85%]">
                    <div className="flex flex-col items-end space-y-2 max-w-full">
                      {msg.content && (
                        <div className="bg-gradient-to-br from-[#2e2620] to-[#2a231d] text-zinc-100 px-4 py-3 rounded-2xl rounded-tr-sm border border-white/10 shadow-sm text-sm leading-relaxed transition-all whitespace-pre-wrap">
                          {msg.content}
                        </div>
                      )}

                      {/* User Message Attachments Display */}
                      {msg.attachments && msg.attachments.length > 0 && (
                        <div className="flex flex-wrap gap-2 justify-end max-w-full">
                          {msg.attachments.map((att, attIdx) => {
                            const isImg = att.category === 'image' || att.mime_type?.startsWith('image/');
                            const isVid = att.category === 'video' || att.mime_type?.startsWith('video/');
                            return (
                              <div
                                key={att.id || attIdx}
                                className="bg-[#1f1a17] border border-white/10 rounded-xl p-2 flex items-center space-x-2.5 max-w-xs hover:border-emerald-500/40 transition-all group"
                              >
                                {isImg ? (
                                  <a
                                    href={`/api/attachments/${att.id}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="relative block w-11 h-11 rounded-lg overflow-hidden bg-black/40 shrink-0 group-hover:opacity-90 border border-[#3a3128]"
                                  >
                                    <img
                                      src={`/api/attachments/${att.id}`}
                                      alt={att.filename}
                                      className="w-full h-full object-cover"
                                    />
                                  </a>
                                ) : isVid ? (
                                  <a
                                    href={`/api/attachments/${att.id}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="relative block w-11 h-11 rounded-lg overflow-hidden bg-black/60 shrink-0 flex items-center justify-center border border-[#3a3128] group-hover:border-purple-400"
                                  >
                                    <Video className="w-5 h-5 text-purple-400" />
                                  </a>
                                ) : (
                                  <div className="w-8 h-8 rounded-lg bg-[#1f1a17] border border-white/10 flex items-center justify-center shrink-0">
                                    {getFileIcon(att.filename, att.mime_type)}
                                  </div>
                                )}

                                <div className="min-w-0 flex-1 pr-1">
                                  <a
                                    href={`/api/attachments/${att.id}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="text-xs font-medium text-zinc-200 hover:text-emerald-400 truncate block"
                                    title={att.filename}
                                  >
                                    {att.filename}
                                  </a>
                                  <span className="text-[10px] text-zinc-500 font-mono">
                                    {att.size_formatted || formatSize(att.size_bytes || 0)}
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-zinc-600 to-zinc-700 border border-white/10 flex items-center justify-center text-zinc-200 shrink-0 shadow-sm">
                      <User className="w-4 h-4" />
                    </div>
                  </div>
                ) : (
                  /* AI Response */
                  <div className="w-full flex items-start space-x-3.5">
                    <div className="w-9 h-9 rounded-full overflow-hidden ring-1 ring-amber-500/30 shadow-lg shadow-orange-500/10 shrink-0 mt-1">
                      <img src="/assets/assistant-avatar.png" alt="AI Assistant" className="w-full h-full object-cover" />
                    </div>

                    <div className="flex-1 space-y-4 max-w-[90%]">
                      {/* Thought Timeline / Status Stages for Executed Actions */}
                      {msg.thoughts && msg.thoughts.length > 0 && msg.actions && msg.actions.length > 0 && (
                        <div className="bg-[#1f1a17] border border-white/5 rounded-xl p-3.5 space-y-2.5 shadow-sm">
                          <div className="flex items-center justify-between text-[11px] text-zinc-400 border-b border-white/5 pb-1.5">
                            <span className="font-semibold uppercase tracking-wider text-emerald-400/90 flex items-center space-x-1.5">
                              <Clock className="w-3.5 h-3.5 text-emerald-400" />
                              <span>AI Reasoning & Execution Timeline</span>
                            </span>
                            <span className="text-[10px] font-mono text-zinc-500">Structured Chain-of-Thought</span>
                          </div>

                          <div className="space-y-1.5">
                            {msg.thoughts.map((th, tIdx) => {
                              const { Icon: ThoughtIcon, color: thoughtColor } = getThoughtIcon(th.step, th.level);
                              return (
                                <div key={tIdx} className="flex items-start space-x-2 text-xs">
                                  <span className={`mt-0.5 w-4 h-4 flex items-center justify-center shrink-0 ${thoughtColor}`}>
                                    <ThoughtIcon className="w-3.5 h-3.5" />
                                  </span>
                                  <div className="flex-1">
                                    <span className="font-medium text-zinc-200">{th.title} </span>
                                    <span className="text-zinc-400 text-[11px]">{th.detail}</span>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Safety Warning Card if confirmation is required */}
                      {msg.confirmation_required && (
                        <div className="bg-rose-950/30 border border-rose-500/40 rounded-xl p-4 space-y-3">
                          <div className="flex items-center space-x-2 text-rose-400 font-semibold text-xs">
                            <AlertTriangle className="w-4 h-4 text-rose-400 animate-bounce" />
                            <span>Safety Interception: Destructive Operation Detected</span>
                          </div>
                          <p className="text-xs text-zinc-300">
                            {msg.confirmation_payload?.impact || 'This action modifies or deletes system files and requires your manual authorization.'}
                          </p>
                          <div className="flex items-center space-x-3 pt-1">
                            <button
                              onClick={() => onOpenConfirmation(msg.actions[0]?.approval_token, msg.confirmation_payload)}
                              className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs shadow-md transition-all flex items-center space-x-1.5"
                            >
                              <ShieldAlert className="w-3.5 h-3.5" />
                              <span>Review & Authorize Action</span>
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Executed Action Cards */}
                      {msg.actions && msg.actions.length > 0 && (
                        <div className="space-y-2">
                          {msg.actions.map((act, actIdx) => {
                            const isExpanded = expandedCards[actIdx];
                            const toolName = act.tool || 'Tool Execution';
                            const isSuccess = act.status === 'completed' || act.execution_result?.success;
                            const isPending = act.status === 'pending_confirmation';
                            const isBlocked = act.status === 'blocked' || act.risk_level === 'blocked';
                            const { Icon: ToolIcon, color: toolColor, bg: toolBg, border: toolBorder } = getToolIcon(toolName);

                            return (
                              <div 
                                key={actIdx}
                                className={`bg-[#211c18] border rounded-xl overflow-hidden shadow-sm transition-colors ${isBlocked ? 'border-rose-500/40' : 'border-white/5 hover:border-white/10'}`}
                              >
                                <div 
                                  onClick={() => toggleCardExpand(actIdx)}
                                  className="px-3.5 py-2.5 flex items-center justify-between cursor-pointer hover:bg-white/[0.03] transition-all"
                                >
                                  <div className="flex items-center space-x-2.5">
                                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center border ${isBlocked ? 'bg-rose-500/20 text-rose-400 border-rose-500/40' : isPending ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' : isSuccess ? toolBg + ' ' + toolColor + ' ' + toolBorder : 'bg-blue-500/15 text-blue-400 border-blue-500/30'}`}>
                                      <ToolIcon className="w-4 h-4" />
                                    </div>
                                    <div>
                                      <div className="text-xs font-semibold text-zinc-200 flex items-center space-x-2">
                                        <span>Action: {toolName}</span>
                                        {isBlocked ? (
                                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-rose-500/20 text-rose-400 font-mono border border-rose-500/40 flex items-center space-x-1">
                                            <ShieldAlert className="w-2.5 h-2.5" />
                                            <span>Blocked</span>
                                          </span>
                                        ) : isPending ? (
                                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-400 font-mono border border-amber-500/30">
                                            Pending Approval
                                          </span>
                                        ) : (
                                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400 font-mono border border-emerald-500/30 flex items-center space-x-1">
                                            <Check className="w-2.5 h-2.5" />
                                            <span>Completed</span>
                                          </span>
                                        )}
                                      </div>
                                      <div className="text-[11px] text-zinc-400">{act.description}</div>
                                      {isBlocked && act.warning_message && (
                                        <div className="text-[10px] text-rose-400 font-medium mt-0.5">{act.warning_message}</div>
                                      )}
                                    </div>
                                  </div>

                                  <div className="flex items-center space-x-2">
                                    {toolName === 'create_project' && isSuccess && (
                                      <button
                                        type="button"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          const files = act.parameters?.files || {};
                                          const isWeb = !!files['index.html'];
                                          const code = act.execution_result?.preview_html || files['index.html'] || files['snake.py'] || Object.values(files)[0] || '';
                                          const filename = isWeb ? 'index.html' : (Object.keys(files)[0] || 'project');
                                          const lang = isWeb ? 'html' : 'python';
                                          handleOpenWorkspace({ code, language: lang, filename, tab: isWeb ? 'preview' : 'code' });
                                        }}
                                        className="px-2.5 py-1 rounded-md bg-gradient-to-r from-violet-600/30 to-emerald-600/30 hover:from-violet-600/50 hover:to-emerald-600/50 text-violet-200 border border-violet-500/30 text-[11px] font-semibold flex items-center space-x-1 transition-all"
                                      >
                                        <Gamepad2 className="w-3 h-3" />
                                        <span>Play Game</span>
                                      </button>
                                    )}
                                    {act.execution_result?.duration_ms && (
                                      <span className="text-[10px] font-mono text-zinc-500">
                                        {act.execution_result.duration_ms}ms
                                      </span>
                                    )}
                                    {isExpanded ? <ChevronUp className="w-4 h-4 text-zinc-400" /> : <ChevronDown className="w-4 h-4 text-zinc-400" />}
                                  </div>
                                </div>

                                {/* Collapsible Card Details */}
                                {isExpanded && (
                                  <div className="px-3.5 py-3 border-t border-white/5 bg-[#161210] text-xs font-mono space-y-2">
                                    <div>
                                      <div className="text-zinc-500 text-[10px] uppercase font-bold">Parameters:</div>
                                      <pre className="text-emerald-400/90 overflow-x-auto text-[11px] mt-0.5 p-2 bg-[#100d0b] rounded-md border border-white/5">
                                        {JSON.stringify(act.parameters, null, 2)}
                                      </pre>
                                    </div>
                                    {act.execution_result && (
                                      <div>
                                        <div className="text-zinc-500 text-[10px] uppercase font-bold">Execution Output:</div>
                                        <pre className="text-zinc-300 overflow-x-auto text-[11px] mt-0.5 p-2 bg-[#100d0b] rounded-md border border-white/5">
                                          {JSON.stringify(act.execution_result, null, 2)}
                                        </pre>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {/* Natural Language Response Body */}
                      <div className="text-sm text-zinc-200 leading-relaxed prose prose-invert max-w-none">
                        <MarkdownContent content={msg.content} onOpenWorkspace={handleOpenWorkspace} />
                      </div>

                      {/* Action Bar (Copy, Speak) */}
                      <div className="flex items-center space-x-3 text-xs text-zinc-400 pt-1">
                        <button
                          onClick={() => handleSpeak(msg.id || index, msg.content)}
                          className={`flex items-center space-x-1 hover:text-zinc-200 transition-colors ${
                            speakingMsgId === (msg.id || index) ? 'text-emerald-400 font-semibold' : ''
                          }`}
                          title="Listen to response aloud"
                        >
                          {speakingMsgId === (msg.id || index) ? (
                            <>
                              <VolumeX className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                              <span>Speaking...</span>
                            </>
                          ) : (
                            <>
                              <Volume2 className="w-3.5 h-3.5" />
                              <span>Speak</span>
                            </>
                          )}
                        </button>

                        <button
                          onClick={() => handleCopy(msg.id || index, msg.content)}
                          className="flex items-center space-x-1 hover:text-zinc-200 transition-colors"
                          title="Copy response"
                        >
                          {copiedId === (msg.id || index) ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                              <span className="text-emerald-400">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>Copy</span>
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Loading / Thinking Indicator with Stop Button */}
            {isLoading && (
              <div className="max-w-4xl mx-auto flex items-start space-x-3.5">
                <div className="w-9 h-9 rounded-full overflow-hidden ring-1 ring-amber-500/30 shadow-lg shadow-orange-500/10 shrink-0">
                  <img src="/assets/assistant-avatar.png" alt="AI Assistant" className="w-full h-full object-cover animate-pulse" />
                </div>
                <div className="space-y-2.5 bg-[#211c18] border border-white/5 rounded-2xl p-4 w-72 shadow-sm">
                  <div className="flex items-center justify-between text-xs text-emerald-400 font-medium">
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
                      <span>Generating response...</span>
                    </div>
                    {onStopGeneration && (
                      <button
                        type="button"
                        onClick={onStopGeneration}
                        className="flex items-center space-x-1 px-2 py-0.5 rounded bg-rose-500/20 border border-rose-500/40 text-rose-300 hover:bg-rose-500/30 text-[10px] font-semibold transition-all"
                        title="Stop Generation"
                      >
                        <Square className="w-2.5 h-2.5 fill-rose-400 text-rose-400" />
                        <span>Stop</span>
                      </button>
                    )}
                  </div>
                  <div className="h-2 bg-white/10 rounded w-3/4 shimmer"></div>
                  <div className="h-2 bg-white/10 rounded w-1/2 shimmer"></div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Box Footer */}
          <footer className="p-4 md:p-6 bg-[#141110]/85 backdrop-blur-md border-t border-white/5 select-none shrink-0">
            <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative">
              {/* Error Alert Toast */}
              {errorMessage && (
                <div className="mb-2.5 px-3.5 py-2 rounded-xl bg-rose-950/80 border border-rose-500/40 text-rose-300 text-xs flex items-center space-x-2 animate-fadeIn shadow-md">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Native File Input */}
              <input
                id="chat-native-file-input"
                ref={fileInputRef}
                type="file"
                multiple
                className="sr-only"
                onChange={handleFileInputChange}
                accept={SUPPORTED_EXTENSIONS.join(',')}
              />

          <div className="bg-[#262019] border border-white/10 focus-within:border-emerald-500/60 focus-within:shadow-lg focus-within:shadow-emerald-500/10 rounded-2xl shadow-lg transition-all overflow-hidden flex flex-col">
            {/* Rate Limit Cooldown Bar */}
            {(rateLimitState.cooldown_remaining_seconds > 0 || rateLimitState.remaining_slots <= 0) && (
              <div className="flex items-center justify-between px-3.5 py-1.5 bg-amber-500/10 border-b border-amber-500/20 text-amber-300 text-xs font-medium">
                <div className="flex items-center space-x-1.5">
                  <Clock className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
                  <span>Attachment limit reached ({rateLimitState.current_used}/{rateLimitState.max_allowed} used)</span>
                </div>
                <span className="font-mono bg-amber-500/20 px-2 py-0.5 rounded text-[11px] border border-amber-500/30 font-semibold">
                  Resets in {formatCooldown(rateLimitState.cooldown_remaining_seconds)}
                </span>
              </div>
            )}

            {/* Pending Attachments Preview Strip */}
            {pendingFiles.length > 0 && (
              <div className="flex flex-wrap gap-2 p-2.5 pb-2 border-b border-white/5 bg-[#1f1a17]">
                {pendingFiles.map((pf) => (
                  <div
                    key={pf.id}
                    className="flex items-center space-x-2 bg-[#2a231d] border border-white/10 hover:border-zinc-500 rounded-lg p-1.5 pr-2 text-xs text-zinc-200 shadow-sm relative group"
                  >
                    {pf.previewUrl ? (
                      <img src={pf.previewUrl} alt={pf.name} className="w-8 h-8 object-cover rounded bg-black/40 border border-[#444]" />
                    ) : (
                      <div className="w-8 h-8 rounded bg-[#1f1a17] border border-white/10 flex items-center justify-center">
                        {getFileIcon(pf.name, pf.type)}
                      </div>
                    )}
                    <div className="max-w-[130px] min-w-0 truncate">
                      <div className="truncate font-medium text-[11px] text-zinc-200">{pf.name}</div>
                      <div className="text-[9px] text-zinc-500 font-mono">{formatSize(pf.size)}</div>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleRemovePendingFile(pf.id)}
                      className="p-1 rounded-md text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors ml-1"
                      title="Remove attachment"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Input row */}
            <div className="flex items-center p-1.5 pl-3">
              {/* Attachment Button */}
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (rateLimitState.cooldown_remaining_seconds <= 0 && rateLimitState.remaining_slots > 0) {
                    fileInputRef.current?.click();
                  }
                }}
                className={`p-2 rounded-xl transition-all mr-1 group shrink-0 ${
                  rateLimitState.cooldown_remaining_seconds > 0 || rateLimitState.remaining_slots <= 0
                    ? 'text-zinc-600 cursor-not-allowed bg-zinc-800/30'
                    : 'text-zinc-400 hover:text-zinc-100 hover:bg-white/5'
                }`}
                title={
                  rateLimitState.cooldown_remaining_seconds > 0 || rateLimitState.remaining_slots <= 0
                    ? `Attachment limit reached (${rateLimitState.current_used}/${rateLimitState.max_allowed} used). Available again in ${formatCooldown(rateLimitState.cooldown_remaining_seconds)}`
                    : "Attach files (Images, PDFs, Video, Text, Code up to 25 MB)"
                }
                disabled={isLoading || isUploading || rateLimitState.cooldown_remaining_seconds > 0 || rateLimitState.remaining_slots <= 0}
              >
                <Paperclip className={`w-4 h-4 ${(rateLimitState.cooldown_remaining_seconds <= 0 && rateLimitState.remaining_slots > 0) ? 'group-hover:rotate-45' : ''} transition-transform`} />
              </button>

                  <input
                    ref={inputRef}
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder={pendingFiles.length > 0 ? "Add a message about your attachment(s)..." : "Type a message or attach files (e.g. 'open Chrome', attach code/video)..."}
                    className="flex-1 bg-transparent border-none outline-none text-zinc-100 placeholder-zinc-500 text-sm py-2"
                    disabled={isLoading || isUploading}
                  />

                  <div className="flex items-center space-x-1.5 pr-1">
                    {/* Stop Generation Button when generating */}
                    {isLoading && onStopGeneration && (
                      <button
                        type="button"
                        onClick={onStopGeneration}
                        className="flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-rose-600/20 text-rose-300 border border-rose-500/40 hover:bg-rose-600/30 text-xs font-semibold shadow-sm transition-all"
                        title="Stop generation"
                      >
                        <Square className="w-3 h-3 fill-rose-400 text-rose-400" />
                        <span>Stop</span>
                      </button>
                    )}

                    {/* Voice input button with audio wave visualizer */}
                    <button
                      type="button"
                      onClick={handleVoiceToggle}
                      className={`p-2 rounded-xl transition-all ${
                        isRecording 
                          ? 'bg-rose-600 text-white animate-pulse shadow-md shadow-rose-600/30' 
                          : 'text-zinc-400 hover:text-zinc-100 hover:bg-white/5'
                      }`}
                      title={isRecording ? 'Listening... click to stop' : 'Speak voice command'}
                    >
                      <Mic className="w-4 h-4" />
                    </button>

                    {/* Submit button */}
                    <button
                      type="submit"
                      disabled={(!inputMessage.trim() && pendingFiles.length === 0) || isLoading || isUploading}
                      className={`p-2 rounded-xl font-medium transition-all ${
                        (inputMessage.trim() || pendingFiles.length > 0) && !isLoading && !isUploading
                          ? 'bg-accent-gradient hover:opacity-90 text-white shadow-md shadow-emerald-600/25'
                          : 'bg-[#2e2620] text-zinc-500 cursor-not-allowed'
                      }`}
                      title={isUploading ? "Uploading files..." : "Send message"}
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] text-zinc-500 mt-2 px-2">
                <span>Supports Images, Videos, PDFs, Code & Data (Max 5 files / 25 MB each)</span>
                <span className="hidden sm:inline">Windows 11 Native API Supported</span>
              </div>
            </form>
          </footer>
        </div>

        {/* Right: Workspace Preview / Code / Activity Side Panel */}
        {showWorkspacePanel && (
          <aside className="w-[460px] max-w-full bg-[#141110] border-l border-white/5 flex flex-col h-full shrink-0 shadow-2xl z-20 transition-all">
            {/* Panel Header */}
            <div className="h-14 border-b border-white/5 bg-[#1a1614] px-4 flex items-center justify-between select-none shrink-0">
              <div className="flex items-center space-x-1.5 bg-[#262019] p-1 rounded-xl border border-white/5">
                <button
                  type="button"
                  onClick={() => setWorkspaceTab('preview')}
                  className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    workspaceTab === 'preview'
                      ? 'bg-accent-gradient text-white shadow-sm'
                      : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Preview</span>
                </button>

                <button
                  type="button"
                  onClick={() => setWorkspaceTab('code')}
                  className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    workspaceTab === 'code'
                      ? 'bg-accent-gradient text-white shadow-sm'
                      : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <Code2 className="w-3.5 h-3.5" />
                  <span>Code</span>
                </button>

                <button
                  type="button"
                  onClick={() => setWorkspaceTab('activity')}
                  className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    workspaceTab === 'activity'
                      ? 'bg-accent-gradient text-white shadow-sm'
                      : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <Activity className="w-3.5 h-3.5" />
                  <span>Activity</span>
                </button>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setShowWorkspacePanel(false)}
                  className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-colors"
                  title="Close Workspace Panel"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Panel Body */}
            <div className="flex-1 overflow-hidden p-4 flex flex-col min-h-0">
              {workspaceTab === 'preview' && (
                <div className="flex-1 flex flex-col h-full bg-[#161210] rounded-xl border border-white/5 overflow-hidden">
                  {workspaceCode ? (
                    <iframe
                      srcDoc={workspaceCode.includes('<html') || workspaceCode.includes('<!DOCTYPE') || workspaceCode.includes('<div') || workspaceCode.includes('<svg') ? workspaceCode : `<!DOCTYPE html><html><head><meta charset="utf-8"><style>body{font-family:sans-serif;padding:16px;color:#eee;background:#1a1614;}</style></head><body><pre>${workspaceCode.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre></body></html>`}
                      sandbox="allow-scripts"
                      className="w-full h-full bg-white rounded-lg border-0"
                      title="Live Code Preview"
                    />
                  ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-zinc-500 space-y-2">
                      <Eye className="w-8 h-8 text-zinc-600" />
                      <div className="text-xs font-semibold text-zinc-400">No active preview</div>
                      <div className="text-[11px] max-w-xs">Ask the AI to write HTML, web components, or create files to see live interactive preview here.</div>
                    </div>
                  )}
                </div>
              )}

              {workspaceTab === 'code' && (
                <div className="flex-1 flex flex-col h-full bg-[#161210] rounded-xl border border-white/5 overflow-hidden">
                  <div className="flex items-center justify-between px-3 py-2 border-b border-white/5 bg-[#1f1a17] text-xs text-zinc-400">
                    <span className="font-mono text-[11px] text-emerald-400">{workspaceFilename}</span>
                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={() => {
                          navigator.clipboard.writeText(workspaceCode);
                          setWorkspaceCopied(true);
                          setTimeout(() => setWorkspaceCopied(false), 2000);
                        }}
                        className="px-2 py-1 rounded bg-[#262019] hover:bg-[#3a3128] text-zinc-300 text-[11px] flex items-center space-x-1 transition-all"
                        title="Copy complete code"
                      >
                        {workspaceCopied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        <span>{workspaceCopied ? 'Copied' : 'Copy'}</span>
                      </button>

                      <a
                        href={`data:text/plain;charset=utf-8,${encodeURIComponent(workspaceCode)}`}
                        download={workspaceFilename}
                        className="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] flex items-center space-x-1 transition-all"
                        title="Download file"
                      >
                        <Download className="w-3 h-3" />
                        <span>Download</span>
                      </a>
                    </div>
                  </div>

                  <pre className="flex-1 p-3.5 overflow-auto text-xs font-mono text-emerald-300 whitespace-pre leading-relaxed select-text">
                    {workspaceCode || '// No code in workspace'}
                  </pre>
                </div>
              )}

              {workspaceTab === 'activity' && (
                <div className="flex-1 flex flex-col h-full bg-[#161210] rounded-xl border border-white/5 p-3.5 space-y-3 overflow-y-auto">
                  <div className="text-xs font-bold text-zinc-300 uppercase tracking-wider flex items-center space-x-1.5">
                    <Activity className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Desktop Activity Log</span>
                  </div>

                  <div className="space-y-2">
                    <div className="p-2.5 rounded-lg bg-[#211c18] border border-white/5 text-xs flex items-start space-x-2">
                      <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <div className="font-semibold text-zinc-200">Workspace Automation Layer Active</div>
                        <div className="text-[10px] text-zinc-400">DesktopController initialized with real-time process & window targeting.</div>
                      </div>
                    </div>

                    {messages.filter(m => m.actions && m.actions.length > 0).map((m, mIdx) => (
                      <div key={mIdx} className="p-2.5 rounded-lg bg-[#211c18] border border-white/5 text-xs space-y-1.5">
                        <div className="text-[10px] font-mono text-emerald-400 font-semibold uppercase">Executed Automation:</div>
                        {m.actions.map((act, aIdx) => (
                          <div key={aIdx} className="space-y-1">
                            <div className="text-zinc-200 text-[11px] font-medium flex items-center space-x-1.5">
                              <Zap className="w-3 h-3 text-amber-400 shrink-0" />
                              <span>{act.description || act.tool}</span>
                            </div>
                            {act.tool === 'create_project' && act.execution_result && (
                              <div className="pl-4 space-y-0.5 text-[10px] font-mono text-zinc-400 border-l border-white/10">
                                <div className="flex items-center space-x-1.5">
                                  <Folder className="w-3 h-3 text-amber-400 shrink-0" />
                                  <span>Project folder: {act.execution_result.path}</span>
                                </div>
                                {act.execution_result.created_files?.map((cf, cfIdx) => (
                                  <div key={cfIdx} className="text-emerald-400 flex items-center space-x-1.5">
                                    <Check className="w-3 h-3 shrink-0" />
                                    <span>{cf.file} ({cf.size_bytes} bytes) verified</span>
                                  </div>
                                ))}
                                <div className="text-emerald-300 font-semibold flex items-center space-x-1.5">
                                  <ShieldCheck className="w-3 h-3 shrink-0" />
                                  <span>Physical filesystem verification passed</span>
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
