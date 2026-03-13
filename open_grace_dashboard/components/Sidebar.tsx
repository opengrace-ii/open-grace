"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Image from 'next/image';
import { 
  LayoutDashboard, 
  ListTodo, 
  Users, 
  Database, 
  Puzzle, 
  Cpu, 
  FileText, 
  Settings,
  LogOut,
  Activity
} from 'lucide-react';
import { cn } from '@/services/utils';
import { DashboardService } from '@/services/api';

const navItems = [
  { name: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  { name: 'Tasks', icon: ListTodo, href: '/tasks' },
  { name: 'Agents', icon: Users, href: '/agents' },
  { name: 'Memory', icon: Database, href: '/memory' },
  { name: 'Plugins', icon: Puzzle, href: '/plugins' },
  { name: 'Models', icon: Cpu, href: '/models' },
  { name: 'Logs', icon: FileText, href: '/logs' },
];

export function Sidebar() {
  const pathname = usePathname();
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      const data = await DashboardService.getSystemStatus();
      if (data) setStatus(data);
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const cpuUsage = status ? Math.floor(Math.random() * 10) + 5 : 0;
  const memUsage = status ? Math.floor(Math.random() * 5) + 40 : 0;

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col h-screen border-r border-slate-800">
      <div className="p-6 flex items-center gap-3">
        <div className="relative w-10 h-10 flex items-center justify-center">
          <Image 
            src="/OG_Matelic.png" 
            alt="Open Grace Logo" 
            fill
            className="object-contain brightness-110 drop-shadow-[0_0_8px_rgba(255,255,255,0.2)]"
          />
        </div>
        <span className="text-xl font-bold text-white tracking-tight">Open Grace</span>
      </div>

      <nav className="flex-1 px-4 space-y-1 mt-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors group",
                isActive 
                  ? "bg-blue-600/10 text-blue-400 font-medium" 
                  : "hover:bg-slate-800 hover:text-white"
              )}
            >
              <item.icon className={cn("w-5 h-5", isActive ? "text-blue-400" : "text-slate-400 group-hover:text-slate-200")} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800 space-y-4">
        <div className="bg-slate-800/50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400">System Status</span>
            <span className={cn(
              "w-2 h-2 rounded-full",
              status ? "bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]"
            )}></span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-[10px]">
              <span>CPU</span>
              <span>{cpuUsage}%</span>
            </div>
            <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500 transition-all duration-1000" 
                style={{ width: `${cpuUsage}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-[10px]">
              <span>Memory</span>
              <span>{memUsage}%</span>
            </div>
            <div className="h-1 bg-slate-700 rounded-full overflow-hidden">
              <div 
                className="h-full bg-purple-500 transition-all duration-1000" 
                style={{ width: `${memUsage}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <Link
            href="/settings"
            className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-slate-800 hover:text-white transition-colors"
          >
            <Settings className="w-5 h-5 text-slate-400" />
            Settings
          </Link>
          <button
            className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-red-500/10 hover:text-red-400 transition-colors w-full text-left"
          >
            <LogOut className="w-5 h-5 text-slate-400" />
            Sign Out
          </button>
        </div>
      </div>
    </aside>
  );
}
