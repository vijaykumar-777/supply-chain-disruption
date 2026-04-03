export type View = "dashboard" | "global-map" | "live-feed" | "analytics" | "ai-assistant";

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
