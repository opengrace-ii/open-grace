"use client";

import { 
  Database, 
  Search, 
  Sparkles, 
  TrendingUp, 
  ExternalLink,
  History,
  Lightbulb,
  FileSearch,
  Zap,
  CheckCircle2,
  Brain,
  ChevronRight,
  ShieldCheck,
  LayoutGrid
} from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '@/services/utils';
import { MemoryVisualizer } from '@/components/MemoryVisualizer';

const experiences = [
  {
    goal: 'Build Python CLI tool for log analysis',
    score: 8,
    strength: 'Good modular design and error handling',
    suggestions: ['Add input validation for file paths', 'Implement concurrent processing for large files'],
    timestamp: '2 hours ago',
    type: 'Coding'
  },
  {
    goal: 'Design responsive React landing page',
    score: 9,
    strength: 'Excellent use of Tailwind and Framer Motion',
    suggestions: ['Consider mobile-first approach for hero section'],
    timestamp: '5 hours ago',
    type: 'UI/UX'
  }
];

const distributionData = [
  { label: 'React', value: 450, color: 'blue' },
  { label: 'Python', value: 890, color: 'purple' },
  { label: 'SEO', value: 210, color: 'pink' },
  { label: 'DevOps', value: 640, color: 'emerald' },
];

export default function MemoryExplorer() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-left-4 duration-500">
      <div className="flex justify-between items-center bg-slate-900 border border-slate-800 p-8 rounded-3xl backdrop-blur-md shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
           <Database size={200} className="text-blue-500" />
        </div>
        
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
             <div className="flex items-center gap-1.5 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full">
                <ShieldCheck className="w-3 h-3 text-blue-400" />
                <span className="text-[10px] font-black text-blue-400 uppercase tracking-widest">Local-First Vault</span>
             </div>
             <span className="text-[10px] font-mono text-slate-600 tracking-tighter uppercase">Sync Locked: Cluster-01</span>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Knowledge Infrastructure</h1>
          <p className="text-slate-500 mt-2 italic text-sm">Deep inspection of LLM experience vectors and strategy recall logic.</p>
        </div>
        
        <div className="flex gap-3 relative z-10">
           <button className="flex items-center gap-2 px-5 py-2.5 bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-xl text-slate-400 hover:text-white font-bold text-xs transition-all uppercase tracking-widest">
            <History className="w-4 h-4" />
            Wipe Cache
          </button>
          <button className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 rounded-xl text-white font-bold text-xs transition-all shadow-lg shadow-blue-900/40 uppercase tracking-widest">
            <Sparkles className="w-4 h-4" />
            Defragment
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Memory Stats */}
        <div className="md:col-span-4 space-y-8">
           <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm shadow-xl flex flex-col justify-between h-[180px]">
              <div className="flex items-center justify-between">
                 <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-pink-500/10 text-pink-400">
                      <TrendingUp className="w-4 h-4" />
                    </div>
                    <span className="text-xs font-black text-slate-500 uppercase tracking-widest">System Recall</span>
                 </div>
                 <span className="text-emerald-500 text-[10px] font-bold">+12% Gain</span>
              </div>
              <div>
                 <p className="text-4xl font-black text-white tracking-tighter">1,248<span className="text-sm text-slate-600 ml-2 font-mono">KEYS</span></p>
                 <div className="flex items-center gap-4 mt-6">
                    <div className="flex-1 space-y-1.5">
                       <div className="flex justify-between text-[10px] uppercase font-bold text-slate-600">
                          <span>Quality Alpha</span>
                          <span className="text-slate-400">8.4</span>
                       </div>
                       <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                          <motion.div initial={{ width: 0 }} animate={{ width: '84%' }} className="h-full bg-pink-500 shadow-[0_0_8px_rgba(236,72,153,0.5)]" />
                       </div>
                    </div>
                 </div>
              </div>
           </div>

           <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 space-y-6">
              <h3 className="text-[10px] font-black text-slate-600 uppercase tracking-[0.2em] border-b border-slate-800 pb-4 flex justify-between items-center">
                 Knowledge Proximity
                 <LayoutGrid className="w-3 h-3" />
              </h3>
              <div className="grid grid-cols-2 gap-4">
                 <div className="flex flex-col gap-1">
                    <span className="text-xs font-bold text-slate-300">Cluster A</span>
                    <span className="text-[9px] text-slate-600 italic uppercase">Engineering</span>
                 </div>
                 <div className="flex flex-col gap-1 border-l border-slate-800 pl-4">
                    <span className="text-xs font-bold text-slate-300">Cluster B</span>
                    <span className="text-[9px] text-slate-600 italic uppercase">Creative</span>
                 </div>
              </div>
              <button className="w-full py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-[10px] font-bold text-slate-500 hover:text-white transition-all uppercase tracking-widest">
                 View Adjacency Matrix
              </button>
           </div>
        </div>

        <div className="md:col-span-8 bg-slate-900/40 border border-slate-800 rounded-2xl p-8 backdrop-blur-sm shadow-xl">
          <div className="flex items-center justify-between mb-10">
             <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  <Brain className="w-5 h-5" />
                </div>
                <div>
                   <h2 className="text-lg font-bold text-white tracking-tight">Index Distribution</h2>
                   <p className="text-xs text-slate-600 font-mono tracking-tighter">TOTAL VECTOR DENSITY: 12.8 GB / UNCOMPRESSED</p>
                </div>
             </div>
             <button className="p-2 text-slate-500 hover:text-white transition-colors bg-slate-950 rounded-lg border border-slate-800">
                <ChevronRight className="w-4 h-4" />
             </button>
          </div>
          <MemoryVisualizer data={distributionData} />
        </div>
      </div>

      <div className="space-y-6">
        <div className="flex items-center justify-between px-2">
          <h2 className="text-xl font-bold text-white flex items-center gap-3">
            <div className="w-1.5 h-6 bg-blue-600 rounded-full" />
            Experience Audit Trail
          </h2>
          <div className="flex gap-4">
            <div className="relative group">
               <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-600 group-focus-within:text-blue-500 transition-colors" />
               <input type="text" placeholder="Search vectors..." className="bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500/50 w-48 transition-all" />
            </div>
            <button className="text-[10px] text-slate-500 hover:text-white font-black uppercase tracking-widest transition-all">Export JSON-L</button>
          </div>
        </div>

        <div className="grid gap-6">
          {experiences.map((exp, i) => (
            <div key={i} className="bg-slate-900/30 border border-slate-800/80 rounded-2xl p-6 group hover:border-slate-600 transition-all relative overflow-hidden">
              <div className="flex justify-between items-start mb-8 relative z-10">
                <div className="max-w-2xl">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="px-2.5 py-0.5 rounded-lg bg-blue-500/10 text-blue-400 text-[10px] font-black uppercase tracking-[0.1em] border border-blue-500/20">{exp.type}</span>
                    <span className="text-[10px] font-mono text-slate-600">{exp.timestamp}</span>
                    <div className="h-px w-12 bg-slate-800" />
                    <span className="text-[10px] text-slate-500 font-mono italic">CRC32: AX-99-01</span>
                  </div>
                  <h3 className="text-xl font-bold text-white group-hover:text-blue-400 transition-colors leading-tight">{exp.goal}</h3>
                </div>
                <div className="flex flex-col items-center gap-2">
                   <div className="w-12 h-12 rounded-2xl flex items-center justify-center bg-slate-950 border border-slate-800 text-xl font-black text-white shadow-2xl group-hover:border-purple-500/30 group-hover:shadow-purple-500/10 transition-all">
                    {exp.score}
                  </div>
                  <span className="text-[8px] text-slate-600 font-black uppercase tracking-[0.2em]">Rating</span>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-8 relative z-10 px-2">
                <div className="bg-slate-950/40 p-5 rounded-2xl border border-slate-800/40 hover:bg-slate-950/60 transition-colors">
                  <h4 className="text-[10px] text-slate-600 uppercase font-black tracking-[0.2em] mb-4 flex items-center gap-2">
                    <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                    Key Successors
                  </h4>
                  <p className="text-xs text-slate-300 leading-relaxed font-medium italic">
                    {exp.strength}
                  </p>
                </div>
                <div className="bg-slate-950/40 p-5 rounded-2xl border border-slate-800/40 hover:bg-slate-950/60 transition-colors">
                  <h4 className="text-[10px] text-slate-600 uppercase font-black tracking-[0.2em] mb-4 flex items-center gap-2">
                    <Lightbulb className="w-3 h-3 text-amber-500" />
                    Evolutionary Data
                  </h4>
                  <ul className="space-y-2.5">
                    {exp.suggestions.map((s, j) => (
                      <li key={j} className="text-xs text-slate-400 flex items-start gap-2 h-full">
                        <div className="w-1.5 h-1.5 rounded-full bg-slate-800 mt-1.5 shrink-0 group-hover:bg-blue-600 transition-colors"></div>
                        <span className="line-clamp-2">{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="mt-8 pt-6 border-t border-slate-800/50 flex justify-between items-center relative z-10 px-2">
                <div className="flex gap-4">
                   <span className="flex items-center gap-1.5 text-[10px] font-bold text-slate-600 uppercase"><Zap className="w-3 h-3" /> 84.1 Peak</span>
                   <span className="flex items-center gap-1.5 text-[10px] font-bold text-slate-600 uppercase"><Brain className="w-3 h-3" /> Dense Index</span>
                </div>
                <button className="flex items-center gap-2 text-[10px] font-black text-slate-500 hover:text-white uppercase tracking-[0.1em] transition-all group/btn">
                  Open Sub-graph
                  <ExternalLink className="w-3 h-3 group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-transform" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
