"use client";

import { 
  Puzzle, 
  Settings2, 
  Power, 
  RefreshCw, 
  Download,
  AlertCircle,
  CheckCircle2,
  Lock,
  Search,
  Plus
} from 'lucide-react';
import { cn } from '@/services/utils';

const plugins = [
  { 
    name: 'file_editor', 
    version: '2.1.0',
    description: 'Autonomous multi-file editing and code generation.',
    status: 'active',
    category: 'Core',
    permissions: ['filesystem', 'read-write']
  },
  { 
    name: 'python_executor', 
    version: '1.4.0',
    description: 'Execute Python scripts in a secure sandbox (bubblewrap).',
    status: 'active',
    category: 'Runtime',
    permissions: ['sandbox', 'terminal']
  },
  { 
    name: 'web_search', 
    version: '0.9.5',
    description: 'Tavily-powered real-time web search for information retrieval.',
    status: 'disabled',
    category: 'Network',
    permissions: ['internet']
  },
  { 
    name: 'git_tool', 
    version: '1.2.1',
    description: 'Full Git workflow integration for agents.',
    status: 'disabled',
    category: 'Core',
    permissions: ['terminal', 'filesystem']
  }
];

export default function PluginManager() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-top-4 duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Plugin Manager</h1>
          <p className="text-slate-400 mt-2">Manage tools and capabilities for the agent swarm.</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search plugins..." 
              className="pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all w-64"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium transition-all shadow-lg shadow-blue-500/20">
            <Plus className="w-4 h-4" />
            Install Plugin
          </button>
        </div>
      </div>

      <div className="grid gap-6">
        {plugins.map((plugin) => (
          <div 
            key={plugin.name} 
            className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 group hover:border-slate-700 transition-all backdrop-blur-sm"
          >
            <div className="flex justify-between items-start gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className={cn(
                    "p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 group-hover:text-blue-400 group-hover:border-blue-500/30 transition-all shadow-xl",
                    plugin.status === 'active' ? "border-blue-500/20 text-blue-400" : ""
                  )}>
                    <Puzzle className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-bold text-white uppercase tracking-tight">{plugin.name}</h3>
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">v{plugin.version}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-blue-400 font-bold uppercase tracking-widest">{plugin.category}</span>
                      <span className="text-[10px] text-slate-600">•</span>
                      <div className="flex gap-1.5">
                        {plugin.permissions.map((p) => (
                          <div key={p} className="flex items-center gap-1">
                            <Lock className="w-2.5 h-2.5 text-slate-500" />
                            <span className="text-[10px] text-slate-500 font-medium">{p}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
                <p className="text-sm text-slate-400 max-w-2xl mt-4 leading-relaxed line-clamp-2">
                  {plugin.description}
                </p>
              </div>

              <div className="flex flex-col gap-3 min-w-[140px]">
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/50 border border-slate-800/50 mb-1">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Status</span>
                  <div className="flex items-center gap-2">
                    <span className={cn(
                      "w-1.5 h-1.5 rounded-full",
                      plugin.status === 'active' ? "bg-green-500" : "bg-slate-600"
                    )}></span>
                    <span className={cn(
                      "text-[10px] font-bold uppercase",
                      plugin.status === 'active' ? "text-green-400" : "text-slate-500"
                    )}>
                      {plugin.status}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className={cn(
                    "flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all",
                    plugin.status === 'active' 
                      ? "bg-red-500/10 text-red-400 hover:bg-red-500/20" 
                      : "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
                  )}>
                    <Power className="w-3.5 h-3.5" />
                    {plugin.status === 'active' ? 'Disable' : 'Enable'}
                  </button>
                  <button className="p-2 aspect-square rounded-lg bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white transition-all">
                    <Settings2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-slate-800/50 flex justify-between items-center text-[10px] font-medium text-slate-500">
               <div className="flex gap-4">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                    Passed security audit
                  </span>
                  <span className="flex items-center gap-1.5">
                    <RefreshCw className="w-3.5 h-3.5 text-blue-500" />
                    Auto-updates enabled
                  </span>
               </div>
               <button className="flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors">
                  <Download className="w-3.5 h-3.5" />
                  Update to v2.1.1
               </button>
            </div>
          </div>
        ))}
        
        {/* Placeholder for warning */}
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-4 flex items-center gap-4">
           <div className="p-2 rounded-lg bg-amber-500/20 text-amber-500">
             <AlertCircle className="w-5 h-5" />
           </div>
           <p className="text-xs text-amber-500/80 font-medium">
             Wait! 2 plugins are currently disabled and may affect <strong>Research</strong> and <strong>Deployment</strong> capabilities.
           </p>
        </div>
      </div>
    </div>
  );
}
