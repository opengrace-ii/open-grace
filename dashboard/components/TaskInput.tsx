"use client";

import { useState } from 'react';
import { Send, Sparkles, Shield, Zap } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '@/services/utils';
import { DashboardService } from '@/services/api';

export function TaskInput() {
  const [goal, setGoal] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim() || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await DashboardService.submitTask(goal, 'auto');
      setGoal('');
      // We could add a toast here
    } catch (error) {
      console.error('Failed to submit task:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="w-5 h-5 text-blue-400" />
        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-widest">Submit New Goal</h3>
      </div>

      <div className="relative">
        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="What should Grace do? (e.g., 'Analyze the performance of our API endpoints')"
          className="w-full h-32 bg-slate-950 border border-slate-700 rounded-xl p-4 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all resize-none placeholder:text-slate-600"
          disabled={isSubmitting}
        />
        
        <div className="absolute bottom-4 right-4 flex items-center gap-3">
          <div className="flex bg-slate-950 border border-slate-800 rounded-lg p-1">
            {(['low', 'medium', 'high'] as const).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setPriority(p)}
                className={cn(
                  "px-3 py-1 text-[10px] font-bold uppercase rounded transition-all",
                  priority === p 
                    ? "bg-slate-800 text-blue-400" 
                    : "text-slate-500 hover:text-slate-300"
                )}
              >
                {p}
              </button>
            ))}
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            disabled={isSubmitting || !goal.trim()}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-lg font-bold text-xs transition-all",
              isSubmitting || !goal.trim()
                ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20"
            )}
          >
            {isSubmitting ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            {isSubmitting ? 'Submitting...' : 'Execute'}
          </motion.button>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between text-[10px] text-slate-500 px-1">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1"><Shield className="w-3 h-3" /> Sandbox Enabled</span>
          <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-amber-500" /> High Priority Cluster</span>
        </div>
        <span className="italic">Autosave enabled</span>
      </div>
    </form>
  );
}
