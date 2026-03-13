"use client";

import { useEffect, useState, useRef } from 'react';
import { Terminal, Copy, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/services/utils';
import { DashboardService } from '@/services/api';

interface LogEntry {
  id: string;
  timestamp: string;
  type: string;
  data: any;
}

export function TerminalFeed() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ws = DashboardService.connectEvents((message) => {
      if (message.type === 'log' || message.type === 'task_event' || message.type === 'agent_activity') {
        const newEntry = {
          id: Math.random().toString(36).substr(2, 9),
          timestamp: new Date().toLocaleTimeString(),
          type: message.type,
          data: message.data
        };
        setLogs(prev => [...prev.slice(-49), newEntry]); // Keep last 50
      }
    });

    return () => ws.close();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const clearLogs = () => setLogs([]);

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden flex flex-col h-full shadow-2xl">
      <div className="flex justify-between items-center px-4 py-2 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Thought Stream</span>
        </div>
        <div className="flex gap-2">
           <button className="p-1 hover:text-white text-slate-500 transition-colors" title="Copy Logs">
            <Copy className="w-3.5 h-3.5" />
          </button>
           <button onClick={clearLogs} className="p-1 hover:text-red-400 text-slate-500 transition-colors" title="Clear">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-[11px] space-y-2 scroll-smooth"
      >
        <AnimatePresence>
          {logs.length === 0 ? (
            <div className="h-full flex items-center justify-center text-slate-600 animate-pulse">
              Waiting for live signals...
            </div>
          ) : logs.map((log) => (
            <motion.div 
              key={log.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex gap-3 leading-relaxed"
            >
              <span className="text-slate-600 shrink-0 select-none">[{log.timestamp}]</span>
              <span className={cn(
                "shrink-0 font-bold",
                log.type === 'log' ? "text-blue-500" :
                log.type === 'task_event' ? "text-purple-500" :
                "text-emerald-500"
              )}>
                {log.type.toUpperCase()}
              </span>
              <span className="text-slate-300">
                {typeof log.data === 'string' ? log.data : JSON.stringify(log.data)}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
