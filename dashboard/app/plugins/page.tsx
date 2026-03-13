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
  Plus,
  ShieldCheck,
  Zap,
  Globe,
  FileCode,
  Terminal,
  Cpu
} from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '@/services/utils';

const plugins = [
  { 
    name: 'file_editor', 
    version: '2.1.0',
    description: 'Autonomous multi-file editing and code generation.',
    status: 'active',
    category: 'Core',
    icon: FileCode,
    color: 'blue',
    permissions: ['filesystem', 'read-write'],
    computeIndex: 'LOW'
  },
  { 
    name: 'python_executor', 
    version: '1.4.0',
    description: 'Execute Python scripts in a secure sandbox (bubblewrap).',
    status: 'active',
    category: 'Runtime',
    icon: Terminal,
    color: 'emerald',
    permissions: ['sandbox', 'terminal'],
    computeIndex: 'MEDIUM'
  },
  { 
    name: 'web_search', 
    version: '0.9.5',
    description: 'Tavily-powered real-time web search for information retrieval.',
    status: 'disabled',
    category: 'Network',
    icon: Globe,
    color: 'amber',
    permissions: ['internet'],
    computeIndex: 'HIGH'
  },
  { 
    name: 'git_tool', 
    version: '1.2.1',
    description: 'Full Git workflow integration for agents.',
    status: 'disabled',
    category: 'Core',
    icon: Puzzle,
    color: 'slate',
    permissions: ['terminal', 'filesystem'],
    computeIndex: 'LOW'
  }
];

export default function PluginManager() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-top-4 duration-500">
      <div className="flex justify-between items-center bg-slate-900 border border-slate-800 p-8 rounded-3xl backdrop-blur-md shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
           <Puzzle size={200} className="text-blue-500" />
        </div>
        
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
             <div className="flex items-center gap-1.5 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full">
                <ShieldCheck className="w-3 h-3 text-blue-400" />
                <span className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Runtime Security Active</span>
             </div>
             <span className="text-[10px] font-mono text-slate-600 tracking-tighter uppercase">Sandbox Architecture: BWRAP-S1</span>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Plugin Ecosystem</h1>
          <p className="text-slate-500 mt-2 italic text-sm">Extend the swarm's capabilities by hot-loading secure tools and runtimes.</p>
        </div>
        
        <div className="flex gap-3 relative z-10">
          <button className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-2xl text-white font-bold text-xs transition-all shadow-xl shadow-blue-900/40 uppercase tracking-widest">
            <Plus className="w-4 h-4" />
            Registry
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {plugins.map((plugin) => (
          <div 
            key={plugin.name} 
            className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6 group hover:border-slate-600 transition-all backdrop-blur-sm relative overflow-hidden h-full flex flex-col"
          >
            <div className="flex justify-between items-start mb-8">
               <div className="flex items-center gap-4">
                  <div className={cn(
                    "p-3 rounded-2xl border transition-all shadow-2xl",
                    plugin.status === 'active' 
                      ? `bg-${plugin.color}-500/10 border-${plugin.color}-500/20 text-${plugin.color}-400`
                      : "bg-slate-950 border-slate-800 text-slate-500"
                  )}>
                    <plugin.icon className="w-6 h-6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="text-xl font-black text-white uppercase tracking-tighter">{plugin.name}</h3>
                      <span className="text-[9px] font-black px-2 py-0.5 rounded-full bg-slate-950 border border-slate-800 text-slate-600">v{plugin.version}</span>
                    </div>
                    <div className="flex items-center gap-3 mt-1.5">
                       <span className={cn(
                         "text-[10px] font-black uppercase tracking-widest",
                         plugin.status === 'active' ? "text-emerald-500" : "text-slate-600"
                       )}>{plugin.status}</span>
                       <span className="text-slate-800 font-bold">•</span>
                       <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">{plugin.category}</span>
                    </div>
                  </div>
               </div>
               <div className="flex gap-2">
                 <button className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-slate-500 hover:text-white hover:border-slate-600 transition-all">
                    <Settings2 className="w-4 h-4" />
                 </button>
                 <button className={cn(
                    "p-2.5 rounded-xl border transition-all",
                    plugin.status === 'active' 
                      ? "bg-red-500/10 border-red-500/20 text-red-500 hover:bg-red-500/20" 
                      : "bg-emerald-500/10 border-emerald-500/20 text-emerald-500 hover:bg-emerald-500/20"
                 )}>
                    <Power className="w-4 h-4" />
                 </button>
               </div>
            </div>

            <p className="text-sm text-slate-400 leading-relaxed h-[48px] line-clamp-2 px-1 mb-8">
              {plugin.description}
            </p>

            <div className="grid grid-cols-3 gap-4 mb-8">
               <div className="bg-slate-950/40 p-3 rounded-2xl border border-slate-800/50">
                  <span className="text-[9px] text-slate-600 uppercase font-black block mb-1 tracking-widest">Recall</span>
                  <span className="text-xs font-bold text-slate-300">99.8%</span>
               </div>
               <div className="bg-slate-950/40 p-3 rounded-2xl border border-slate-800/50">
                  <span className="text-[9px] text-slate-600 uppercase font-black block mb-1 tracking-widest">Compute</span>
                  <span className={cn(
                    "text-xs font-bold",
                    plugin.computeIndex === 'LOW' ? "text-emerald-500" : 
                    plugin.computeIndex === 'MEDIUM' ? "text-blue-500" : "text-amber-500"
                  )}>{plugin.computeIndex}</span>
               </div>
               <div className="bg-slate-950/40 p-3 rounded-2xl border border-slate-800/50">
                  <span className="text-[9px] text-slate-600 uppercase font-black block mb-1 tracking-widest">Sandbox</span>
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-500" />
               </div>
            </div>

            <div className="mt-auto pt-6 border-t border-slate-800/50 flex flex-wrap gap-2">
               {plugin.permissions.map((p) => (
                  <div key={p} className="flex items-center gap-1.5 px-2 py-1 bg-slate-950 rounded-lg border border-slate-800">
                    <Lock className="w-2.5 h-2.5 text-slate-600" />
                    <span className="text-[9px] text-slate-500 font-bold uppercase tracking-tight">{p}</span>
                  </div>
               ))}
            </div>
          </div>
        ))}
      </div>

      <div className="bg-blue-600/5 border border-blue-500/20 rounded-3xl p-8 relative overflow-hidden group">
         <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none group-hover:rotate-12 transition-transform duration-700">
            <Cpu size={120} className="text-blue-400" />
         </div>
         <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
            <div className="max-w-xl">
               <h3 className="text-xl font-bold text-white mb-2">Automated Optimization Required</h3>
               <p className="text-sm text-slate-400 leading-relaxed">
                  The current swarm is utilizing a legacy version of the <strong>Web Search</strong> node. 
                  Upgrade to v1.0.0 is recommended to reduce token latency by approx. 40%.
               </p>
            </div>
            <button className="flex items-center gap-2 px-8 py-3 bg-white text-slate-950 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-slate-200 transition-all whitespace-nowrap">
               Run Cluster Update
            </button>
         </div>
      </div>
    </div>
  );
}
