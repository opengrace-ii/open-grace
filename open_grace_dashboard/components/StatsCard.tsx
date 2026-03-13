import { LucideIcon } from 'lucide-react';
import { cn } from '@/services/utils';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: string;
  trendPositive?: boolean;
  unit?: string;
  color?: 'blue' | 'purple' | 'green' | 'amber' | 'red';
}

export function StatsCard({ 
  title, 
  value, 
  icon: Icon, 
  trend, 
  trendPositive, 
  unit,
  color = 'blue'
}: StatsCardProps) {
  const colorClasses = {
    blue: 'text-blue-500 bg-blue-500/10',
    purple: 'text-purple-500 bg-purple-500/10',
    green: 'text-green-500 bg-green-500/10',
    amber: 'text-amber-500 bg-amber-500/10',
    red: 'text-red-500 bg-red-500/10',
  };

  return (
    <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl backdrop-blur-sm">
      <div className="flex justify-between items-start mb-4">
        <div className={cn("p-2 rounded-lg", colorClasses[color])}>
          <Icon className="w-5 h-5" />
        </div>
        {trend && (
          <span className={cn(
            "text-xs font-medium px-2 py-0.5 rounded-full",
            trendPositive ? "text-green-400 bg-green-400/10" : "text-amber-400 bg-amber-400/10"
          )}>
            {trend}
          </span>
        )}
      </div>
      <div>
        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">{title}</h3>
        <div className="flex items-baseline gap-1 mt-1">
          <span className="text-2xl font-bold text-white">{value}</span>
          {unit && <span className="text-sm text-slate-500 font-medium">{unit}</span>}
        </div>
      </div>
    </div>
  );
}
