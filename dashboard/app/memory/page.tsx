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
  Brain
} from 'lucide-react';
import { cn } from '@/services/utils';

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

export default function MemoryExplorer() {
  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-left-4 duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Memory Explorer</h1>
          <p className="text-slate-400 mt-2">Visualize and optimize the AI OS knowledge base.</p>
        </div>
        <div className="flex gap-2">
           <button className="flex items-center gap-2 px-4 py-2 bg-slate-900/50 border border-slate-800 hover:bg-slate-800 rounded-lg text-slate-300 font-medium transition-all">
            <History className="w-4 h-4" />
            Clear Short-term
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-white font-medium transition-all shadow-lg shadow-purple-500/20">
            <Sparkles className="w-4 h-4" />
            Optimize Knowledge Path
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Memory Stats */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
          <div className="flex items-center gap-3 mb-6">
             <div className="p-2 rounded-lg bg-pink-500/10 text-pink-400">
               <TrendingUp className="w-5 h-5" />
             </div>
             <h2 className="text-lg font-semibold text-white">System Growth</h2>
          </div>
          <div className="space-y-6">
            <div className="flex justify-between items-end">
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Shared Experience</span>
                <p className="text-3xl font-bold text-white mt-1">1,248</p>
              </div>
              <span className="text-emerald-400 text-xs font-bold mb-1">+12 today</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Average Quality Score</span>
                <span className="text-white font-bold">8.4 / 10</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-purple-500 to-pink-500 w-[84%]"></div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm shadow-xl">
          <div className="flex items-center gap-3 mb-6">
             <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
               <Brain className="w-5 h-5" />
             </div>
             <h2 className="text-lg font-semibold text-white">Knowledge Distribution</h2>
          </div>
          <div className="flex gap-4 h-[94px] items-end">
            <div className="flex-1 flex flex-col items-center gap-2">
              <div className="w-full bg-blue-500/20 rounded-t-lg h-[60%] border-t border-x border-blue-500/30"></div>
              <span className="text-[9px] text-slate-500 font-bold uppercase">React</span>
            </div>
            <div className="flex-1 flex flex-col items-center gap-2">
              <div className="w-full bg-purple-500/20 rounded-t-lg h-[80%] border-t border-x border-purple-500/30"></div>
              <span className="text-[9px] text-slate-500 font-bold uppercase">Python</span>
            </div>
            <div className="flex-1 flex flex-col items-center gap-2">
              <div className="w-full bg-pink-500/20 rounded-t-lg h-[40%] border-t border-x border-pink-500/30"></div>
              <span className="text-[9px] text-slate-500 font-bold uppercase">SEO</span>
            </div>
            <div className="flex-1 flex flex-col items-center gap-2">
              <div className="w-full bg-emerald-500/20 rounded-t-lg h-[90%] border-t border-x border-emerald-500/30"></div>
              <span className="text-[9px] text-slate-500 font-bold uppercase">DevOps</span>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between px-2">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <FileSearch className="w-5 h-5 text-blue-500" />
            Stored Experiences
          </h2>
          <div className="flex gap-4">
            <button className="text-xs text-blue-400 hover:text-blue-300 font-bold uppercase tracking-wider transition-colors">Vector Search</button>
            <button className="text-xs text-slate-500 hover:text-slate-400 font-bold uppercase tracking-wider transition-colors">Filters</button>
          </div>
        </div>

        <div className="grid gap-4">
          {experiences.map((exp, i) => (
            <div key={i} className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 group hover:border-slate-700 transition-all">
              <div className="flex justify-between items-start mb-6">
                <div className="max-w-xl">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 text-[10px] font-bold uppercase tracking-widest">{exp.type}</span>
                    <span className="text-[10px] text-slate-600">•</span>
                    <span className="text-[10px] text-slate-500 font-medium">{exp.timestamp}</span>
                  </div>
                  <h3 className="text-lg font-bold text-white group-hover:text-purple-400 transition-colors">{exp.goal}</h3>
                </div>
                <div className="flex flex-col items-center gap-1">
                   <div className="w-10 h-10 rounded-full flex items-center justify-center bg-slate-950 border border-slate-800 text-lg font-black text-white shadow-xl shadow-purple-500/5 border-t-purple-500/50">
                    {exp.score}
                  </div>
                  <span className="text-[8px] text-slate-500 font-bold uppercase tracking-tighter">Quality</span>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-[10px] text-slate-500 uppercase font-black tracking-widest mb-3 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                    Strengths
                  </h4>
                  <p className="text-xs text-slate-300 bg-slate-950/30 p-3 rounded-xl border border-slate-800/50 italic">
                    {exp.strength}
                  </p>
                </div>
                <div>
                  <h4 className="text-[10px] text-slate-500 uppercase font-black tracking-widest mb-3 flex items-center gap-1.5">
                    <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
                    AI Recommendations
                  </h4>
                  <ul className="space-y-2">
                    {exp.suggestions.map((s, j) => (
                      <li key={j} className="text-xs text-slate-400 flex items-start gap-2 h-full">
                        <span className="w-1 h-1 rounded-full bg-slate-700 mt-2 shrink-0"></span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="mt-8 flex justify-end">
                <button className="flex items-center gap-2 text-[10px] font-bold text-slate-600 hover:text-white uppercase tracking-widest transition-all group/btn">
                  View Full Memory Graph
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
