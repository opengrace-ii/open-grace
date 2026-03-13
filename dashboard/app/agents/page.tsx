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
import { motion } from 'framer-motion';
import { cn } from '@/services/utils';
import { DashboardService } from '@/services/api';
import { AgentPulse } from '@/components/AgentPulse';

const AGENT_CONFIGS: Record<string, any> = {
  coder: { icon: Brain, role: 'Software Engineering', color: 'blue' },
  sysadmin: { icon: ShieldCheck, role: 'System Operations', color: 'emerald' },
  researcher: { icon: Globe, role: 'Information Retrieval', color: 'amber' },
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
            successRate: '98%' // Simulated as backend doesn't track this yet
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
      <div className="flex justify-between items-center bg-slate-900/50 p-6 rounded-2xl border border-slate-800 backdrop-blur-sm">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Agent Swarm</h1>
          <p className="text-slate-500 mt-1 text-xs uppercase font-black tracking-widest">Global Instance: TaskForge-01-Alpha</p>
        </div>
        <div className="flex gap-4">
           <div className="flex flex-col items-end pr-4 border-r border-slate-800">
              <span className="text-[10px] text-slate-500 uppercase font-bold">Total Power</span>
              <span className="text-sm font-mono text-blue-400">4 ACTIVE NODES</span>
           </div>
           <button className="flex items-center gap-2 px-4 py-2 bg-slate-950 border border-slate-800 hover:border-blue-500/50 rounded-xl text-slate-300 text-xs font-bold transition-all group">
             <Zap className="w-3.5 h-3.5 fill-current transition-transform group-hover:rotate-12" />
             Reload Swarm
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {swarm.length > 0 ? swarm.map((agent) => (
          <div 
            key={agent.id} 
            className="bg-slate-900 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-all group relative overflow-hidden flex flex-col h-full"
          >
            {/* Intensity Glow */}
            <div className={cn(
               "absolute -top-12 -right-12 w-32 h-32 blur-[40px] opacity-10 transition-opacity group-hover:opacity-20",
               agent.color === 'purple' ? "bg-purple-500" :
               agent.color === 'blue' ? "bg-blue-500" :
               agent.color === 'amber' ? "bg-amber-500" :
               agent.color === 'emerald' ? "bg-emerald-500" :
               "bg-slate-500"
            )}></div>

            <div className="flex justify-between items-start mb-8 relative z-10">
              <div className={cn(
                "p-3 rounded-xl border",
                agent.color === 'purple' ? "bg-purple-500/10 border-purple-500/20 text-purple-400" :
                agent.color === 'blue' ? "bg-blue-500/10 border-blue-500/20 text-blue-400" :
                agent.color === 'amber' ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
                agent.color === 'emerald' ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" :
                "bg-slate-500/10 border-slate-500/20 text-slate-400"
              )}>
                <agent.icon className="w-5 h-5" />
              </div>
              <div className="flex items-center gap-3">
                 <div className="flex flex-col items-end">
                    <span className="text-[9px] font-black text-slate-600 uppercase tracking-tighter">Status</span>
                    <span className="text-[10px] font-bold text-slate-300 uppercase">{agent.status}</span>
                 </div>
                 <AgentPulse status={agent.status.toLowerCase() as any} />
                 <button className="p-1 text-slate-600 hover:text-white transition-colors ml-1">
                   <MoreVertical className="w-4 h-4" />
                 </button>
              </div>
            </div>

            <div className="mb-8 relative z-10">
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-[9px] font-mono text-slate-600">GRACE-NODE-{agent.id.slice(0,4).toUpperCase()}</span>
                {agent.status === 'busy' && <Zap className="w-2.5 h-2.5 text-blue-500 animate-bounce" />}
              </div>
              <h3 className="text-xl font-bold text-white tracking-tight">{agent.name}</h3>
              <p className="text-[10px] text-slate-500 uppercase font-black tracking-widest mt-1 opacity-70">{agent.role}</p>
            </div>

            <div className="flex-1 space-y-4 relative z-10">
               <div className="space-y-2">
                 <div className="flex justify-between items-center text-[10px]">
                    <span className="font-bold text-slate-600 uppercase">Load Latency</span>
                    <span className="text-slate-400 font-mono">14ms</span>
                 </div>
                 <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div 
                       initial={{ width: 0 }}
                       animate={{ width: agent.status === 'busy' ? '85%' : '10%' }}
                       className={cn("h-full", agent.status === 'busy' ? "bg-blue-500" : "bg-emerald-500")}
                    />
                 </div>
               </div>

               <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/50">
                     <span className="text-[9px] text-slate-600 uppercase font-bold block mb-1">Success Rate</span>
                     <span className="text-xs font-bold text-emerald-500">{agent.successRate}</span>
                  </div>
                  <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800/50">
                     <span className="text-[9px] text-slate-600 uppercase font-bold block mb-1">Throughput</span>
                     <span className="text-xs font-bold text-slate-300">{agent.task_count} Pkts</span>
                  </div>
               </div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-800 flex gap-2">
               <button className="flex-1 py-2 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-600 text-[10px] font-black uppercase text-slate-500 hover:text-white transition-all">
                  Settings
               </button>
               <button className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 hover:border-blue-500/50 text-slate-600 hover:text-blue-400 transition-all">
                  <Settings className="w-3.5 h-3.5" />
               </button>
            </div>
          </div>
        )) : !loading ? (
          <div className="col-span-full py-20 text-center bg-slate-950/50 border border-dashed border-slate-800 rounded-3xl">
            <Users className="w-12 h-12 text-slate-800 mx-auto mb-4" />
            <p className="text-slate-600 font-mono tracking-tighter">SWARM NODES DESYNCED FROM CENTRAL ORCHESTRATOR.</p>
          </div>
        ) : (
          <div className="col-span-full py-20 text-center">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto opacity-50" />
            <p className="text-[10px] text-slate-600 uppercase font-black tracking-widest mt-4">Polling Cluster Status...</p>
          </div>
        )}
      </div>
    </div>
  );
}
