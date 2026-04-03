import { cn } from "../../lib/utils";

export const SidebarItem = ({ 
  icon: Icon, 
  label, 
  active, 
  onClick 
}: { 
  icon: any, 
  label: string, 
  active?: boolean, 
  onClick: () => void 
}) => (
  <button 
    onClick={onClick}
    className={cn(
      "flex items-center gap-3 px-4 py-3 transition-all duration-300 ease-in-out w-full text-left",
      active 
        ? "bg-primary/10 text-primary border-r-4 border-primary" 
        : "text-on-surface-variant hover:bg-white/5"
    )}
  >
    <Icon className={cn("w-5 h-5", active && "fill-primary/20")} />
    <span className="text-sm font-medium">{label}</span>
  </button>
);
