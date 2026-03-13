"use client";

import { useEffect, useState } from 'react';
import { 
  Cpu, 
  Activity, 
  Users, 
  Layers, 
  Clock, 
  CheckCircle2,
  AlertTriangle,
  Terminal as TerminalIcon
} from 'lucide-react';
import { StatsCard } from '@/components/StatsCard';
import { TerminalFeed } from '@/components/TerminalFeed';
import { cn } from '@/services/utils';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { DashboardService } from '@/services/api';

const mockChartData = [
  { time: '10:00', cpu: 12, mem: 42 },
  { time: '10:05', cpu: 25, mem: 43 },
  { time: '10:10', cpu: 18, mem: 45 },
  { time: '10:15', cpu: 32, mem: 48 },
  { time: '10:20', cpu: 28, mem: 46 },
  { time: '10:25', cpu: 35, mem: 48 },
  { time: '10:30', cpu: 30, mem: 47 },
];

export default function SystemDashboard() {
  const [mounted, setMounted] = useState(false);
  const [stats, setStats] = useState({
    cpu: 0,
    memory: 0,
    activeAgents: 0,
    tasksCompleted: 0
  });
  const [agents, setAgents] = useState<any[]>([]);
  const [chartData, setChartData] = useState(mockChartData);

  useEffect(() => {
    setMounted(true);
    
    const fetchData = async () => {
      const status = await DashboardService.getSystemStatus();
      const agentsList = await DashboardService.getAgents();
      
      if (status) {
        setStats({
          cpu: Math.floor(Math.random() * 20) + 10, // Mocking CPU as backend doesn't provide real-time OS metrics yet
          memory: Math.floor(Math.random() * 10) + 40, // Mocking Mem
          activeAgents: status.agents.by_status.busy || 0,
          tasksCompleted: status.tasks.by_status.completed || 0
        });

        // Update chart data with new point
        setChartData(prev => {
          const newPoint = {
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            cpu: Math.floor(Math.random() * 20) + 10,
            mem: Math.floor(Math.random() * 10) + 40
          };
          return [...prev.slice(1), newPoint];
        });
      }
      
      if (agentsList) {
        setAgents(agentsList);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!mounted) return null;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">System Dashboard</h1>
        <p className="text-slate-400 mt-2">Real-time health monitoring and resource utilization.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard 
          title="CPU Usage" 
          value={stats.cpu} 
          unit="%" 
          icon={Cpu} 
          trend="+2%" 
          color="blue"
        />
        <StatsCard 
          title="Memory Usage" 
          value={stats.memory} 
          unit="%" 
          icon={Activity} 
          trend="Stable" 
          trendPositive={true}
          color="purple"
        />
        <StatsCard 
          title="Active Agents" 
          value={stats.activeAgents} 
          icon={Users} 
          color="green"
        />
        <StatsCard 
          title="Tasks Completed" 
          value={stats.tasksCompleted} 
          icon={CheckCircle2} 
          color="amber"
          trendPositive={true}
        />
      </div>

      {/* Main Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl backdrop-blur-sm">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-blue-500" />
              Resource Performance
            </h2>
            <div className="flex gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-500 rounded-sm"></div>
                <span className="text-xs text-slate-400">CPU</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-purple-500 rounded-sm"></div>
                <span className="text-xs text-slate-400">Memory</span>
              </div>
            </div>
          </div>
          
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorMem" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis 
                  dataKey="time" 
                  stroke="#64748b" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <YAxis 
                  stroke="#64748b" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                  tickFormatter={(val) => `${val}%`}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px' }}
                />
                <Area 
                  type="monotone" 
                  dataKey="cpu" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorCpu)" 
                />
                <Area 
                  type="monotone" 
                  dataKey="mem" 
                  stroke="#a855f7" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorMem)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Real-time Terminal Feed */}
        <div className="h-[300px]">
          <TerminalFeed />
        </div>
      </div>

        {/* System Activity Feed */}
        <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl backdrop-blur-sm">
          <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
            <Clock className="w-5 h-5 text-amber-500" />
            Active Swarm
          </h2>
          <div className="space-y-4">
            {agents.length > 0 ? agents.map((agent) => (
              <div key={agent.id} className={cn(
                "flex items-start gap-4 p-3 rounded-xl transition-all hover:bg-slate-800/50 group",
                agent.status === 'busy' ? "bg-blue-500/5 border border-blue-500/10" : ""
              )}>
                <div className={cn(
                  "mt-1 flex items-center justify-center p-2 rounded-lg transition-transform group-hover:scale-110",
                  agent.status === 'busy' ? "bg-blue-500/20 text-blue-400" : "bg-slate-800 text-slate-400"
                )}>
                  <Users className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">{agent.name}</h4>
                  <p className="text-xs text-slate-400 mt-0.5">{agent.agent_type.charAt(0).toUpperCase() + agent.agent_type.slice(1)} Agent</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded",
                      agent.status === 'busy' ? "bg-blue-500/20 text-blue-400" : 
                      agent.status === 'idle' ? "bg-green-500/10 text-green-400" :
                      "bg-slate-800 text-slate-400"
                    )}>
                      {agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
                    </span>
                    <span className="text-[10px] text-slate-500">{agent.task_count} tasks</span>
                  </div>
                </div>
              </div>
            )) : (
              <p className="text-xs text-slate-500 text-center py-4">No active agents found.</p>
            )}
          </div>
          
          <button className="w-full mt-6 py-2 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors">
            View Swarm Details
          </button>
        </div>
      </div>
    </div>
  );
}
