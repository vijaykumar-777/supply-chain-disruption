export type View = "dashboard" | "monitor" | "global-map" | "live-disasters" | "live-feed" | "analytics" | "ai-assistant" | "hospital-network";

export interface Event {
  id: number;
  type: string;
  title: string;
  time: string;
  description: string;
  icon: any;
  color: string;
  bgColor: string;
  borderColor: string;
}

export interface Metric {
  label: string;
  value: string;
  trend?: string;
  icon: any;
  colorClass: string;
  pulse?: boolean;
}
