import { 
  CloudRain, 
  Truck, 
  Info, 
  AlertTriangle, 
  Zap, 
  Brain, 
  LayoutDashboard, 
  Globe, 
  Activity, 
  BarChart3, 
  Bot, 
  Settings, 
  HelpCircle 
} from "lucide-react";
import React from "react";

export const DELAY_TREND_DATA = [
  { name: "Mon", value: 40, active: 20 },
  { name: "Tue", value: 60, active: 30 },
  { name: "Wed", value: 55, active: 25 },
  { name: "Thu", value: 85, active: 45 },
  { name: "Fri", value: 45, active: 22 },
  { name: "Sat", value: 70, active: 35 },
  { name: "Sun", value: 90, active: 50 },
];

export const LOGISTICS_VOLUME_DATA = [
  { name: "1", value: 10 },
  { name: "5", value: 15 },
  { name: "10", value: 12 },
  { name: "15", value: 25 },
  { name: "20", value: 18 },
  { name: "25", value: 35 },
  { name: "30", value: 30 },
];

export const RISK_BY_REGION_DATA = [
  { name: "Asia Pacific", value: 42, color: "#7dd3fc" },
  { name: "North America", value: 32, color: "#c8a0f0" },
  { name: "Other Regions", value: 26, color: "#1e293b" },
];

export const LIVE_EVENTS = [
  {
    id: 1,
    type: "critical",
    title: "Typhoon Songda - Philippines",
    time: "2m ago",
    description: "Maritime routes through Luzon Strait suspended. Expect 36h delay.",
    icon: <CloudRain className="w-4 h-4" />,
    color: "text-error",
    bgColor: "bg-error/10",
    borderColor: "border-error/20"
  },
  {
    id: 2,
    type: "warning",
    title: "Trucking Strike - Brazil",
    time: "14m ago",
    description: "Inland logistics near Santos Port operating at 15% capacity.",
    icon: <Truck className="w-4 h-4" />,
    color: "text-tertiary",
    bgColor: "bg-tertiary/10",
    borderColor: "border-tertiary/20"
  },
  {
    id: 3,
    type: "info",
    title: "Snow Storm - Frankfurt",
    time: "45m ago",
    description: "FRA Air cargo terminal experiencing minor de-icing delays.",
    icon: <Info className="w-4 h-4" />,
    color: "text-primary",
    bgColor: "bg-primary/10",
    borderColor: "border-primary/20"
  }
];
