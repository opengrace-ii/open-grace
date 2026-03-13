"use client";

import { motion } from 'framer-motion';
import { cn } from '@/services/utils';

interface MemoryVisualizerProps {
  data: { label: string; value: number; color: string }[];
  className?: string;
}

export function MemoryVisualizer({ data, className }: MemoryVisualizerProps) {
  const max = Math.max(...data.map(d => d.value));

  return (
    <div className={cn("flex items-end gap-3 h-48", className)}>
      {data.map((item, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-3 h-full justify-end group">
          <div className="relative w-full flex flex-col items-center justify-end h-full">
            <motion.div
              initial={{ height: 0 }}
              animate={{ height: `${(item.value / max) * 100}%` }}
              transition={{ duration: 1, delay: i * 0.1, ease: "easeOut" }}
              className={cn(
                "w-full rounded-t-xl border-t border-x relative group-hover:brightness-125 transition-all",
                item.color === 'blue' ? "bg-blue-500/20 border-blue-500/30" :
                item.color === 'purple' ? "bg-purple-500/20 border-purple-500/30" :
                item.color === 'pink' ? "bg-pink-500/20 border-pink-500/30" :
                "bg-emerald-500/20 border-emerald-500/30"
              )}
            >
               <div className={cn(
                 "absolute top-0 left-[20%] right-[20%] h-1 rounded-full blur-[2px] opacity-50",
                 item.color === 'blue' ? "bg-blue-400" :
                 item.color === 'purple' ? "bg-purple-400" :
                 item.color === 'pink' ? "bg-pink-400" :
                 "bg-emerald-400"
               )} />
            </motion.div>
            
            <div className="absolute -top-8 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
              <span className="text-[10px] font-mono font-bold text-white px-2 py-1 bg-slate-950 rounded border border-slate-800 shadow-2xl">
                {item.value} ENTRIES
              </span>
            </div>
          </div>
          
          <div className="flex flex-col items-center gap-1">
             <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest text-center truncate w-full">
               {item.label}
             </span>
             <div className={cn(
               "w-1 h-1 rounded-full",
               item.color === 'blue' ? "bg-blue-500" :
               item.color === 'purple' ? "bg-purple-500" :
               item.color === 'pink' ? "bg-pink-500" :
               "bg-emerald-500"
             )} />
          </div>
        </div>
      ))}
    </div>
  );
}
