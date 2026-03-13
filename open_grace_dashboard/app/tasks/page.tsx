"use client";

import { useEffect, useState } from 'react';
import { 
  Play, 
  Search, 
  Filter, 
  MoreVertical, 
  CheckCircle2, 
  Clock, 
  Loader2,
  Terminal,
  ArrowRight,
  Users
} from 'lucide-react';
import { cn } from '@/services/utils';
import { DashboardService } from '@/services/api';

export default function TaskManager() {
  const [goal, setGoal] = useState('');
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

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

  const handleDispatch = async () => {
    if (!goal.trim()) return;
    setLoading(true);
    const result = await DashboardService.submitTask(goal);
    if (result) {
      setGoal('');
      // Refresh tasks
      const liveTasks = await DashboardService.getTasks();
      if (liveTasks) setTasks(liveTasks);
    }
    setLoading(false);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'running': return 'bg-blue-600';
      case 'completed': return 'bg-emerald-600';
      case 'pending': return 'bg-slate-600';
      case 'failed': return 'bg-red-600';
      default: return 'bg-slate-800';
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Task Manager</h1>
          <p className="text-slate-400 mt-2">Submit and monitor autonomous AI goals.</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search tasks..." 
              className="pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg text-sm text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all w-64"
            />
          </div>
          <button className="p-2 bg-slate-900/50 border border-slate-800 rounded-lg hover:bg-slate-800 transition-colors">
            <Filter className="w-5 h-5 text-slate-400" />
          </button>
        </div>
      </div>

      {/* Goal Submission */}
      <div className="bg-slate-900/50 border border-slate-800 p-8 rounded-2xl backdrop-blur-md relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none group-hover:scale-110 transition-transform duration-700">
          <Terminal size={120} className="text-blue-500" />
        </div>
        
        <div className="relative z-10 max-w-2xl">
          <h2 className="text-xl font-semibold text-white mb-2">New Objective</h2>
          <p className="text-sm text-slate-400 mb-6">Describe the task you want the agent swarm to accomplish.</p>
          
          <div className="flex flex-col gap-4">
            <div className="relative">
              <textarea 
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="Ex: Build a responsive dashboard using Next.js and Tailwind CSS..."
                className="w-full bg-slate-950/50 border border-slate-700 rounded-xl px-4 py-4 min-h-[120px] text-white focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all resize-none"
              />
              <div className="absolute bottom-4 right-4 flex gap-2">
                <span className="text-[10px] text-slate-500 font-mono tracking-tighter self-center uppercase">Priority: Normal</span>
              </div>
            </div>
            
            <button 
              onClick={handleDispatch}
              disabled={loading || !goal.trim()}
              className="flex items-center justify-center gap-2 py-3 px-6 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="fill-current w-4 h-4" />}
              Dispatch Agent Swarm
            </button>
          </div>
        </div>
      </div>

      {/* Active & Recent Tasks */}
      <div className="space-y-4">
        <div className="flex items-center justify-between px-2">
          <h2 className="text-lg font-semibold text-white">Execution Timeline</h2>
          <span className="text-xs text-slate-500 uppercase font-bold tracking-widest">Sort by: Recent</span>
        </div>

        <div className="grid gap-4">
          {tasks.length > 0 ? tasks.map((task) => (
            <div 
              key={task.id} 
              className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all cursor-pointer group"
            >
              <div className="flex justify-between items-start mb-6">
                <div className="flex items-center gap-4">
                  <div className={cn(
                    "w-12 h-12 rounded-xl flex items-center justify-center border",
                    task.status.toLowerCase() === 'running' ? "bg-blue-500/10 border-blue-500/20 text-blue-400" : 
                    task.status.toLowerCase() === 'completed' ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" :
                    "bg-slate-800 border-slate-700 text-slate-500"
                  )}>
                    {task.status.toLowerCase() === 'running' ? <Loader2 className="w-6 h-6 animate-spin" /> : 
                     task.status.toLowerCase() === 'completed' ? <CheckCircle2 className="w-6 h-6" /> :
                     <Clock className="w-6 h-6" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-500">#{task.id_numeric || task.id.slice(-4)}</span>
                      <h3 className="text-md font-semibold text-white group-hover:text-blue-400 transition-colors uppercase tracking-tight">{task.description}</h3>
                    </div>
                    <div className="flex items-center gap-4 mt-1">
                      <div className="flex items-center gap-1.5 text-xs text-slate-500">
                        <Clock className="w-3.5 h-3.5" />
                        {new Date(task.created_at).toLocaleTimeString()}
                      </div>
                      <div className="flex items-center gap-1.5 text-xs text-slate-500">
                        <Users className="w-3.5 h-3.5" />
                        {task.agent_type || 'Swarm'}
                      </div>
                    </div>
                  </div>
                </div>
                <button className="p-2 text-slate-500 hover:text-white transition-colors">
                  <MoreVertical className="w-5 h-5" />
                </button>
              </div>

              {/* Progress Bar (Simulated based on status) */}
              <div className="space-y-2 mb-6">
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-medium text-slate-400">Status</span>
                  <span className={cn(
                    "font-bold uppercase tracking-widest",
                    task.status.toLowerCase() === 'running' ? "text-blue-400" : 
                    task.status.toLowerCase() === 'completed' ? "text-emerald-400" : "text-slate-500"
                  )}>{task.status}</span>
                </div>
                <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className={cn(
                      "h-full transition-all duration-1000 ease-out",
                      getStatusColor(task.status)
                    )}
                    style={{ width: task.status.toLowerCase() === 'completed' ? '100%' : task.status.toLowerCase() === 'running' ? '60%' : '5%' }}
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t border-slate-800/50">
                <div className="flex gap-4">
                   <div className="flex flex-col">
                      <span className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Model</span>
                      <span className="text-xs text-white">{task.model || 'Auto'}</span>
                   </div>
                   <div className="flex flex-col">
                      <span className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Usage</span>
                      <span className="text-xs text-white">{task.tokens_used || 0} tokens</span>
                   </div>
                </div>
                <button className="px-4 py-1.5 rounded-lg border border-slate-700 text-xs font-semibold text-slate-300 hover:bg-slate-800 transition-all">
                  Inspect Details
                </button>
              </div>
            </div>
          )) : (
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-12 text-center">
              <p className="text-slate-500">No tasks found. Dispatch a new objective to begin.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
