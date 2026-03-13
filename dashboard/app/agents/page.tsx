"use client";

import { useEffect, useState } from 'react';
import { 
  Users, 
  Search, 
  Activity, 
  Brain, 
  Zap, 
  ShieldCheck,
  SearchCode,
  Globe,
  Settings,
  MoreVertical,
  Terminal,
  Loader2
} from 'lucide-react';
import { cn } from '@/services/utils';
import { DashboardService } from '@/services/api';

const AGENT_CONFIGS: Record<string, any> = {
  coder: { icon: Brain, role: 'Software Engineering', color: 'amber' },
  sysadmin: { icon: ShieldCheck, role: 'System Operations', color: 'emerald' },
  researcher: { icon: Globe, role: 'Information Retrieval', color: 'blue' },
  planner: { icon: Brain, role: 'Orchestrator', color: 'purple' },
  default: { icon: Users, role: 'General Tasking', color: 'slate' }
};

export default function AgentMonitor() {
  const [swarm, setSwarm] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAgents = async () => {
      const liveAgents = await DashboardService.getAgents();
      if (liveAgents) {
        const mapped = liveAgents.map((a: any) => {
          const config = AGENT_CONFIGS[a.agent_type.toLowerCase()] || AGENT_CONFIGS.default;
          return {
            ...a,
            ...config,
            successRate: '98%' // Simulated as backend doesn't track this per agent yet
          };
        });
        setSwarm(mapped);
      }
      setLoading(false);
    };

    fetchAgents();
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Agent Monitor</h1>
          <p className="text-slate-400 mt-2">Observe and manage your autonomous agent swarm.</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium transition-all group">
          <Zap className="w-4 h-4 fill-current transition-transform group-hover:rotate-12" />
          Re-initialize Swarm
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {swarm.length > 0 ? swarm.map((agent) => (
          <div 
            key={agent.id} 
            className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all group relative overflow-hidden"
          >
            {/* Background Glow */}
            <div className={cn(
              "absolute -top-10 -right-10 w-24 h-24 blur-[60px] opacity-20 transition-opacity group-hover:opacity-40",
              agent.color === 'purple' ? "bg-purple-500" :
              agent.color === 'blue' ? "bg-blue-500" :
              agent.color === 'amber' ? "bg-amber-500" :
              agent.color === 'emerald' ? "bg-emerald-500" :
              "bg-slate-500"
            )}></div>

            <div className="flex justify-between items-start mb-6">
              <div className={cn(
                "p-3 rounded-xl",
                agent.color === 'purple' ? "bg-purple-500/10 text-purple-400" :
                agent.color === 'blue' ? "bg-blue-500/10 text-blue-400" :
                agent.color === 'amber' ? "bg-amber-500/10 text-amber-400" :
                agent.color === 'emerald' ? "bg-emerald-500/10 text-emerald-400" :
                "bg-slate-500/10 text-slate-400"
              )}>
                <agent.icon className="w-6 h-6" />
              </div>
              <div className="flex items-center gap-2">
                 <span className={cn(
                    "w-2 h-2 rounded-full",
                    agent.status.toLowerCase() === 'busy' ? "bg-blue-500 animate-pulse" : 
                    agent.status.toLowerCase() === 'idle' ? "bg-green-500" : 
                    "bg-slate-500"
                  )}></span>
                <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{agent.status}</span>
                <button className="ml-2 p-1 text-slate-500 hover:text-white transition-colors">
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="mb-6">
              <h3 className="text-xl font-bold text-white tracking-tight">{agent.name}</h3>
              <p className="text-[10px] text-slate-500 uppercase font-bold tracking-[0.2em] mt-0.5">{agent.role}</p>
            </div>

            <div className="bg-slate-950/50 rounded-xl p-3 border border-slate-800 mb-6">
              <div className="flex items-center gap-2 mb-1">
                <Terminal className="w-3 h-3 text-slate-500" />
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Capabilities</span>
              </div>
              <div className="flex flex-wrap gap-1 mt-1">
                {(agent.capabilities || []).slice(0, 3).map((cap: string, i: number) => (
                  <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50">{cap}</span>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-800/50">
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-bold">Volume</span>
                <p className="text-sm font-bold text-white mt-0.5">{agent.task_count} tasks</p>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-bold">Reliability</span>
                <p className="text-sm font-bold text-emerald-400 mt-0.5">{agent.successRate}</p>
              </div>
            </div>
            
            <div className="mt-6">
              <button className="w-full py-2 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-all">
                Configure Skills
              </button>
            </div>
          </div>
        )) : !loading ? (
          <div className="col-span-full py-20 text-center bg-slate-900/50 border border-dashed border-slate-800 rounded-3xl">
            <Users className="w-12 h-12 text-slate-700 mx-auto mb-4" />
            <p className="text-slate-500">Swarm offline. Re-initialize to start agents.</p>
          </div>
        ) : (
          <div className="col-span-full py-20 text-center">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto" />
          </div>
        )}
      </div>
    </div>
  );
}
