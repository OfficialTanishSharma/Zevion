import React, { useState } from 'react';
import { 
  Zap, 
  Play, 
  CheckCircle2, 
  Clock, 
  ArrowRight, 
  Plus, 
  Sparkles,
  Layers,
  FileCode,
  Globe,
  FileText,
  Folder,
  Sun,
  Monitor,
  FolderArchive
} from 'lucide-react';

export default function WorkflowBuilder({ onRunWorkflow }) {
  const [runningWorkflowId, setRunningWorkflowId] = useState(null);
  const [workflowStatus, setWorkflowStatus] = useState({});

  const predefinedWorkflows = [
    {
      id: 'morning_routine',
      title: 'Morning Workstation Setup',
      Icon: Sun,
      iconColor: 'text-amber-400',
      iconBg: 'bg-amber-500/15 border-amber-500/30',
      description: 'Launches Google Chrome with search tabs, opens Notepad for notes, and performs system diagnostics.',
      steps: [
        { tool: 'open_application', params: { app_name: 'chrome' }, label: 'Open Google Chrome' },
        { tool: 'open_application', params: { app_name: 'notepad' }, label: 'Open Notepad for daily notes' },
        { tool: 'type_text', params: { text: 'Daily Priorities - 2026-08-07:\n1. Review AI Agent tasks\n2. Ship desktop updates\n', target_app: 'notepad' }, label: 'Insert morning checklist' },
        { tool: 'get_system_info', params: {}, label: 'Inspect CPU & RAM diagnostics' }
      ]
    },
    {
      id: 'scaffold_project',
      title: 'Developer Project Scaffolder',
      Icon: Monitor,
      iconColor: 'text-blue-400',
      iconBg: 'bg-blue-500/15 border-blue-500/30',
      description: 'Creates a Projects directory, initializes project files, and opens File Explorer.',
      steps: [
        { tool: 'create_folder', params: { folder_path: 'Projects/Agent_Workspace' }, label: 'Create Projects/Agent_Workspace folder' },
        { tool: 'create_file', params: { path: 'Projects/Agent_Workspace/README.md', content: '# AI Agent Project\nCreated automatically.' }, label: 'Write initial README.md' },
        { tool: 'open_application', params: { app_name: 'explorer' }, label: 'Launch File Explorer' }
      ]
    },
    {
      id: 'research_flow',
      title: 'Quick Web Research & Summary',
      Icon: Globe,
      iconColor: 'text-emerald-400',
      iconBg: 'bg-emerald-500/15 border-emerald-500/30',
      description: 'Searches Google for AI research topics, opens Notepad, and saves summary notes.',
      steps: [
        { tool: 'open_website', params: { url: 'https://www.google.com/search?q=Autonomous+AI+Desktop+Agents+2026', search_query: 'Autonomous AI Desktop Agents 2026' }, label: 'Search Google for AI trends' },
        { tool: 'open_application', params: { app_name: 'notepad' }, label: 'Open Notepad' },
        { tool: 'type_text', params: { text: 'Research Summary:\nAutonomous desktop agents represent the shift towards natural language computer control.\n', target_app: 'notepad' }, label: 'Write research findings' }
      ]
    },
    {
      id: 'clean_organize',
      title: 'Automated Desktop & Downloads Cleaner',
      Icon: FolderArchive,
      iconColor: 'text-violet-400',
      iconBg: 'bg-violet-500/15 border-violet-500/30',
      description: 'Scans directory and organizes files into Documents, Images, Code, and Archives.',
      steps: [
        { tool: 'organize_files', params: { directory: 'Downloads', strategy: 'by_category' }, label: 'Sort Downloads files by category' },
        { tool: 'take_screenshot', params: { region: 'fullscreen', save_path: 'clean_desktop.png' }, label: 'Take screenshot of organized workspace' }
      ]
    }
  ];

  const handleExecute = async (wf) => {
    setRunningWorkflowId(wf.id);
    setWorkflowStatus(prev => ({ ...prev, [wf.id]: 'running' }));

    for (let i = 0; i < wf.steps.length; i++) {
      const step = wf.steps[i];
      await onRunWorkflow(step.tool, step.params);
      // Small pause between steps for realistic simulation
      await new Promise(r => setTimeout(r, 600));
    }

    setWorkflowStatus(prev => ({ ...prev, [wf.id]: 'completed' }));
    setRunningWorkflowId(null);
  };

  return (
    <div className="flex-1 bg-[#1a1614] p-6 overflow-y-auto text-zinc-100 space-y-6 select-none">
      <div className="flex items-center justify-between border-b border-[#2e2620] pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-amber-600/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-zinc-100 flex items-center space-x-2">
              <span>Smart Workflow Automation Engine</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 font-mono font-semibold">
                Multi-Step Planner
              </span>
            </h2>
            <p className="text-xs text-zinc-400">Chain multiple desktop tools together into automated routines</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {predefinedWorkflows.map((wf) => {
          const isRunning = runningWorkflowId === wf.id;
          const isDone = workflowStatus[wf.id] === 'completed';
          const WfIcon = wf.Icon;

          return (
            <div 
              key={wf.id}
              className="bg-[#1f1a17] border border-white/5 hover:border-white/10 rounded-2xl p-5 space-y-4 transition-all shadow-sm flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <span className={`w-9 h-9 rounded-lg border flex items-center justify-center ${wf.iconBg}`}>
                      <WfIcon className={`w-5 h-5 ${wf.iconColor}`} />
                    </span>
                    <h3 className="text-sm font-bold text-zinc-100">{wf.title}</h3>
                  </div>
                  {isDone && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-mono border border-emerald-500/30 flex items-center space-x-1">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Completed</span>
                    </span>
                  )}
                </div>

                <p className="text-xs text-zinc-400 leading-relaxed">{wf.description}</p>
              </div>

              {/* Step Sequence */}
              <div className="space-y-1.5 bg-[#241e1a] p-3 rounded-xl border border-[#2a231d]">
                <div className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Step Sequence:</div>
                <div className="space-y-1">
                  {wf.steps.map((st, sIdx) => (
                    <div key={sIdx} className="flex items-center space-x-2 text-[11px] text-zinc-300">
                      <span className="w-4 h-4 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-[9px] font-mono text-zinc-400">
                        {sIdx + 1}
                      </span>
                      <span>{st.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Run button */}
              <button
                onClick={() => handleExecute(wf)}
                disabled={isRunning}
                className={`w-full py-2.5 rounded-xl font-semibold text-xs transition-all flex items-center justify-center space-x-2 ${
                  isRunning 
                    ? 'bg-amber-600/30 text-amber-400 border border-amber-500/40 animate-pulse'
                    : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/20'
                }`}
              >
                {isRunning ? (
                  <>
                    <Clock className="w-4 h-4 animate-spin" />
                    <span>Executing Workflow Steps...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Run Automated Workflow</span>
                  </>
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
