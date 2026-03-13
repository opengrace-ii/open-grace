"use client";

import { 
  Cpu, 
  Cloud, 
  Zap, 
  Settings2, 
  ExternalLink,
  ChevronRight,
  Database,
  ArrowRightLeft,
  Search,
  CheckCircle2,
  Lock,
  RefreshCw
} from 'lucide-react';
import { cn } from '@/services/utils';

const localModels = [
  { name: 'llama3', provider: 'Ollama', status: 'Active', latency: '45ms', context: '8k' },
  { name: 'codellama', provider: 'Ollama', status: 'Active', latency: '120ms', context: '16k' },
  { name: 'qwen', provider: 'Ollama', status: 'Available', latency: 'N/A', context: '32k' },
];

const externalProviders = [
  { name: 'GPT-4o', provider: 'OpenAI', status: 'Connected', latency: '450ms', cost: '$0.03/1k' },
  { name: 'Claude 3.5 Sonnet', provider: 'Anthropic', status: 'Connected', latency: '620ms', cost: '$0.015/1k' },
  { name: 'Gemini 1.5 Pro', provider: 'Google', status: 'Connected', latency: '380ms', cost: 'Free/Tier' },
];

export default function ModelRouter() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Model Router</h1>
          <p className="text-slate-400 mt-2">Configure and monitor AI models used for task execution.</p>
        </div>
        <div className="flex gap-2">
           <button className="flex items-center gap-2 px-4 py-2 bg-slate-900/50 border border-slate-800 hover:bg-slate-800 rounded-lg text-slate-300 font-medium transition-all">
            <RefreshCw className="w-4 h-4" />
            Scan Local Models
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium transition-all shadow-lg shadow-blue-500/20">
            <Settings2 className="w-4 h-4" />
            Router Logic
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Local Models */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 px-2">
            <Cpu className="w-5 h-5 text-blue-500" />
            Local Models (Ollama)
          </h2>
          <div className="space-y-3">
            {localModels.map((model) => (
              <div key={model.name} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex justify-between items-center hover:border-blue-500/30 transition-all group">
                <div className="flex items-center gap-4">
                  <div className={cn(
                    "w-10 h-10 rounded-lg flex items-center justify-center bg-slate-950 border border-slate-800 text-slate-400 group-hover:text-blue-400 transition-colors",
                    model.status === 'Active' ? "border-blue-500/20 text-blue-400" : ""
                  )}>
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-wide uppercase">{model.name}</h3>
                    <div className="flex gap-3 mt-1">
                       <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">{model.context} ctx</span>
                       <span className="text-[10px] text-slate-700">•</span>
                       <span className="text-[10px] text-blue-500 font-bold uppercase tracking-widest">{model.latency}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                   <span className={cn(
                      "text-[10px] font-black uppercase tracking-tighter",
                      model.status === 'Active' ? "text-emerald-500" : "text-slate-600"
                    )}>
                      {model.status}
                    </span>
                    <button className="p-1.5 rounded-md hover:bg-slate-800 text-slate-500 hover:text-white transition-all">
                      <ChevronRight className="w-4 h-4" />
                    </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Cloud Providers */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 px-2">
            <Cloud className="w-5 h-5 text-purple-500" />
            External Providers
          </h2>
          <div className="space-y-3">
            {externalProviders.map((model) => (
              <div key={model.name} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex justify-between items-center hover:border-purple-500/30 transition-all group">
                <div className="flex items-center gap-4">
                  <div className={cn(
                    "w-10 h-10 rounded-lg flex items-center justify-center bg-slate-950 border border-slate-800 text-slate-400 group-hover:text-purple-400 transition-colors",
                    model.status === 'Connected' ? "border-purple-500/20 text-purple-400" : ""
                  )}>
                    <Zap className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-wide uppercase">{model.name}</h3>
                    <div className="flex gap-3 mt-1">
                       <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">{model.provider}</span>
                       <span className="text-[10px] text-slate-700">•</span>
                       <span className="text-[10px] text-purple-500 font-bold uppercase tracking-widest">{model.latency}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                   <span className={cn(
                      "text-[10px] font-black uppercase tracking-tighter",
                      model.status === 'Connected' ? "text-emerald-500" : "text-slate-600"
                    )}>
                      {model.status}
                    </span>
                    <button className="p-1.5 rounded-md hover:bg-slate-800 text-slate-500 hover:text-white transition-all">
                      <ExternalLink className="w-4 h-4" />
                    </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Routing Configuration Panel */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-8 backdrop-blur-md relative overflow-hidden group">
         <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none group-hover:scale-110 transition-transform duration-700">
          <ArrowRightLeft size={160} className="text-blue-500" />
        </div>
        
        <div className="relative z-10 flex flex-col md:flex-row gap-12">
            <div className="flex-1">
               <h2 className="text-2xl font-black text-white uppercase tracking-tighter mb-2">Advanced Router</h2>
               <p className="text-slate-400 text-sm leading-relaxed max-w-sm">
                 Intelligent task routing optimizes for <strong>Cost</strong>, <strong>Latency</strong>, and <strong>Reliability</strong> automatically based on TaskForge insights.
               </p>
               
               <div className="mt-8 flex gap-4">
                  <button className="px-6 py-2 rounded-xl bg-slate-800 text-white font-bold text-xs uppercase hover:bg-slate-700 transition-all border border-slate-700">Edit Rules</button>
                  <button className="px-6 py-2 rounded-xl bg-blue-600/10 text-blue-400 font-bold text-xs uppercase hover:bg-blue-600/20 transition-all border border-blue-500/30">View Logs</button>
               </div>
            </div>
            
            <div className="flex-1 space-y-4">
               <div className="p-4 rounded-2xl bg-slate-950/50 border border-slate-800 hover:border-blue-500/40 transition-all cursor-pointer group">
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Task Type: Coding</span>
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  </div>
                  <div className="flex items-center gap-3">
                     <span className="text-sm font-bold text-white uppercase">codellama</span>
                     <ChevronRight className="w-3 h-3 text-slate-700" />
                     <span className="text-xs text-slate-500 italic">Self-correction: Enabled</span>
                  </div>
               </div>
               
               <div className="p-4 rounded-2xl bg-slate-950/50 border border-slate-800 hover:border-purple-500/40 transition-all cursor-pointer group">
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Task Type: Research</span>
                    <Lock className="w-3.5 h-3.5 text-purple-500" />
                  </div>
                  <div className="flex items-center gap-3">
                     <span className="text-sm font-bold text-white uppercase">qwen-7b</span>
                     <ChevronRight className="w-3 h-3 text-slate-700" />
                     <span className="text-xs text-slate-500 italic">Web Search: Tavily</span>
                  </div>
               </div>
            </div>
        </div>
      </div>
    </div>
  );
}
