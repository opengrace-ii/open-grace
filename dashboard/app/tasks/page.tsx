"use client";

import { useEffect, useState } from 'react';
import { 
  Search, 
  Filter, 
  MoreVertical, 
  CheckCircle2, 
  Clock, 
  Loader2,
  Users,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { cn } from '@/services/utils';
import { DashboardService } from '@/services/api';
import { TaskInput } from '@/components/TaskInput';
import { TaskTimeline } from '@/components/TaskTimeline';

export default function TaskManager() {
  const [tasks, setTasks] = useState<any[]>([]);

  useEffect(() => {
    const fetchTasks = async () => {
      const liveTasks = await DashboardService.getTasks();
      if (liveTasks) {
        setTasks(liveTasks);
      }
    };

    fetchTasks();
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStagesForTask = (task: any) => {
    // Mapping task status to agent stages for visualization
    const stages: { id: string; name: string; status: 'pending' | 'running' | 'completed' | 'failed' }[] = [
      { id: 'planning', name: 'Planning', status: 'pending' },
      { id: 'research', name: 'Researching', status: 'pending' },
      { id: 'coding', name: 'Implementing', status: 'pending' },
      { id: 'evaluating', name: 'Evaluating', status: 'pending' },
    ];

    const status = task.status.toLowerCase();
    if (status === 'completed') {
       stages.forEach(s => s.status = 'completed');
    } else if (status === 'running') {
       // Mock progression for now until backend provides granular stage data
       stages[0].status = 'completed';
       stages[1].status = 'running';
    }
    return stages;
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Task Manager</h1>
          <p className="text-slate-400 mt-2 italic text-sm">Control plane for autonomous goal orchestration.</p>
        </div>
        <div className="flex gap-3">
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-blue-400 transition-colors" />
            <input 
              type="text" 
              placeholder="Filter tasks..." 
              className="pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/30 w-64 transition-all"
            />
          </div>
          <button className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 text-slate-400 hover:text-white transition-all">
            <Filter className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Left Column: Input & Active */}
        <div className="xl:col-span-1 space-y-8">
           <TaskInput />
           
           <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Active Runtime</h3>
                <span className="flex items-center gap-1.5 text-[10px] text-blue-400 animate-pulse font-mono">
                  <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                  Observing Swarm
                </span>
              </div>
              <div className="text-center py-8">
                 <p className="text-xs text-slate-600">No active agents currently executing high-priority tasks in background.</p>
              </div>
           </div>
        </div>

        {/* Right Column: Execution Feed */}
        <div className="xl:col-span-2 space-y-6">
          <div className="flex items-center justify-between px-2">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              Execution Timeline
              <span className="text-[10px] font-bold bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full uppercase tracking-tighter">
                {tasks.length} total
              </span>
            </h2>
          </div>

          <div className="grid gap-6">
            {tasks.length > 0 ? tasks.map((task) => (
              <div 
                key={task.id} 
                className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all group relative overflow-hidden"
              >
                <div className="flex justify-between items-start mb-10">
                  <div className="flex items-center gap-4">
                    <div className={cn(
                      "w-10 h-10 rounded-lg flex items-center justify-center border",
                      task.status.toLowerCase() === 'running' ? "bg-blue-500/10 border-blue-500/20 text-blue-400" : 
                      task.status.toLowerCase() === 'completed' ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" :
                      "bg-slate-800 border-slate-700 text-slate-500"
                    )}>
                      {task.status.toLowerCase() === 'running' ? <Loader2 className="w-5 h-5 animate-spin" /> : 
                       task.status.toLowerCase() === 'completed' ? <CheckCircle2 className="w-5 h-5" /> :
                       <Clock className="w-5 h-5" />}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono font-bold text-slate-600">ID: {task.id.slice(0, 8)}</span>
                        <h3 className="text-sm font-bold text-white group-hover:text-blue-400 transition-colors uppercase tracking-tight line-clamp-1">{task.description}</h3>
                      </div>
                      <div className="flex items-center gap-3 mt-1 underline-offset-4 decoration-slate-700">
                        <span className="text-[10px] uppercase font-bold text-slate-500 flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {task.agent_type || 'Swarm'}
                        </span>
                        <span className="text-[10px] text-slate-600">•</span>
                        <span className="text-[10px] font-medium text-slate-500">{new Date(task.created_at).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  </div>
                  <button className="p-2 text-slate-600 hover:text-white transition-colors bg-slate-950/50 rounded-lg border border-slate-800">
                    <MoreVertical className="w-4 h-4" />
                  </button>
                </div>

                <div className="mb-10 px-4">
                   <TaskTimeline stages={getStagesForTask(task)} />
                </div>

                {/* Meta Info */}
                <div className="flex items-center justify-between pt-6 border-t border-slate-800/50">
                  <div className="flex gap-6">
                     <div className="flex flex-col">
                        <span className="text-[10px] text-slate-600 uppercase font-black tracking-widest mb-1">Compute Mode</span>
                        <span className="text-xs text-slate-300 flex items-center gap-1.5">
                           <div className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                           {task.model || 'Standard Cluster'}
                        </span>
                     </div>
                     <div className="flex flex-col border-l border-slate-800/50 pl-6">
                        <span className="text-[10px] text-slate-600 uppercase font-black tracking-widest mb-1">Priority</span>
                        <span className={cn(
                          "text-[10px] font-bold px-2 py-0.5 rounded-full w-fit uppercase tracking-tighter",
                          task.priority === 'high' ? "bg-red-500/10 text-red-500" : "bg-slate-800 text-slate-400"
                        )}>{task.priority || 'Medium'}</span>
                     </div>
                  </div>
                  
                  <div className="flex gap-3">
                     <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-[10px] font-bold text-slate-400 hover:text-white hover:bg-slate-900 transition-all">
                        <ChevronRight className="w-3 h-3" />
                        Details
                     </button>
                     <button className="p-2 rounded-xl bg-slate-950 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-all">
                        <ExternalLink className="w-3.5 h-3.5" />
                     </button>
                  </div>
                </div>
              </div>
            )) : (
              <div className="bg-slate-900/40 border border-slate-800 border-dashed rounded-2xl p-20 text-center">
                <p className="text-slate-600 font-mono text-sm tracking-tighter">No localized trajectories found in current session context.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
