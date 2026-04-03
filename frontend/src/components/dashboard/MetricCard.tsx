import { cn } from "../../lib/utils";

export const MetricCard = ({ 
  label, 
  value, 
  trend, 
  icon: Icon, 
  colorClass, 
  pulse 
}: { 
  label: string, 
  value: string, 
  trend?: string, 
  icon: any, 
  colorClass: string,
  pulse?: boolean
}) => (
  <div className={cn("glass p-5 rounded-xl group transition-all hover:border-primary/40")}>
    <div className="flex justify-between items-start mb-4">
      <span className="text-on-surface-variant text-[10px] font-bold tracking-wider uppercase">{label}</span>
      <div className={cn("p-2 rounded-lg", colorClass, pulse && "neon-pulse-red")}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
    <div className="flex items-baseline gap-2">
      <span className="text-3xl font-bold tracking-tight">{value}</span>
      {trend && (
        <div className="flex items-center">
            {/* Trend display usually goes here */}
            <span className="text-xs font-medium">{trend}</span>
        </div>
      )}
    </div>
  </div>
);
