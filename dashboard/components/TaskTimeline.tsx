"use client";

import { CheckCircle2, Circle, Clock, Loader2 } from 'lucide-react';
import { cn } from '@/services/utils';

interface Stage {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

interface TaskTimelineProps {
  stages: Stage[];
  className?: string;
}

export function TaskTimeline({ stages, className }: TaskTimelineProps) {
  return (
    <div className={cn("flex items-center w-full py-4", className)}>
      {stages.map((stage, index) => (
        <div key={stage.id} className="flex-1 flex items-center group">
          <div className="relative flex flex-col items-center flex-1">
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center transition-all duration-500 border-2 z-10",
              stage.status === 'completed' ? "bg-blue-600 border-blue-600 text-white" :
              stage.status === 'running' ? "bg-slate-900 border-blue-500 text-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" :
              "bg-slate-950 border-slate-800 text-slate-600"
            )}>
              {stage.status === 'completed' && <CheckCircle2 className="w-5 h-5" />}
              {stage.status === 'running' && <Loader2 className="w-5 h-5 animate-spin" />}
              {stage.status === 'pending' && <Circle className="w-4 h-4 fill-current opacity-20" />}
              {stage.status === 'failed' && <span className="text-xs font-bold">!</span>}
            </div>
            
            <div className="absolute -bottom-6 flex flex-col items-center whitespace-nowrap">
              <span className={cn(
                "text-[10px] font-bold uppercase tracking-widest transition-colors",
                stage.status === 'running' ? "text-blue-400" :
                stage.status === 'completed' ? "text-slate-300" : "text-slate-600"
              )}>
                {stage.name}
              </span>
            </div>

            {/* Status indicator line */}
            {index < stages.length - 1 && (
              <div className="absolute left-[50%] right-[-50%] top-4 h-[2px] z-0">
                <div className="w-full h-full bg-slate-800" />
                <div 
                  className={cn(
                    "absolute top-0 left-0 h-full bg-blue-600 transition-all duration-700",
                    stage.status === 'completed' ? "w-full" : "w-0"
                  )} 
                />
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
