"use client";

import { motion } from 'framer-motion';
import { cn } from '@/services/utils';

interface AgentPulseProps {
  status: 'idle' | 'busy' | 'error' | 'offline';
  className?: string;
}

export function AgentPulse({ status, className }: AgentPulseProps) {
  const colorMap = {
    idle: 'bg-emerald-500',
    busy: 'bg-blue-500',
    error: 'bg-red-500',
    offline: 'bg-slate-500'
  };

  const shadowMap = {
    idle: 'shadow-[0_0_8px_rgba(16,185,129,0.4)]',
    busy: 'shadow-[0_0_12px_rgba(59,130,246,0.6)]',
    error: 'shadow-[0_0_12px_rgba(239,68,68,0.6)]',
    offline: 'shadow-none'
  };

  return (
    <div className={cn("relative flex items-center justify-center w-3 h-3", className)}>
      {status === 'busy' && (
        <motion.div
          animate={{
            scale: [1, 2, 1],
            opacity: [0.6, 0, 0.6]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }}
          className={cn("absolute inset-0 rounded-full", colorMap[status])}
        />
      )}
      <div 
        className={cn(
          "w-2 h-2 rounded-full transition-colors duration-500 z-10",
          colorMap[status],
          shadowMap[status]
        )} 
      />
    </div>
  );
}
