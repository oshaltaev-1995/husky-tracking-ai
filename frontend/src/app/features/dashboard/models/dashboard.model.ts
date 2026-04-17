export interface DashboardOverview {
  as_of_date?: string | null;
  total_dogs: number;
  active_dogs: number;
  eligible_dogs: number;
  high_risk_dogs: number;
  moderate_risk_dogs: number;
  underused_dogs: number;
  worked_today_dogs: number;
  total_km_today: number;
}

export interface TodayDogStat {
  dog_id: number;
  dog_name: string;
  km?: number | null;
  worked?: boolean;
  main_role?: string | null;
  runs_today?: number | null;
  availability_status?: string | null;
  lifecycle_status?: string | null;
}

export interface TodayStatsResponse {
  as_of_date?: string | null;
  dogs: TodayDogStat[];
}

export interface DashboardDogNoteItem {
  dog_id: number;
  dog_name: string;
  reason?: string | null;
  reasons?: string[] | null;
  risk_level?: string | null;
  usage_level?: string | null;
  availability_status?: string | null;
  lifecycle_status?: string | null;
}

export interface HeatmapCell {
  dog_id: number;
  dog_name: string;
  kennel_row?: string | null;
  kennel_block?: number | null;
  home_slot?: number | null;
  worked_today?: boolean;
  km_today?: number | null;
  risk_level?: string | null;
  availability_status?: string | null;
  lifecycle_status?: string | null;
}

export interface DashboardHeatmapResponse {
  as_of_date?: string | null;
  items: HeatmapCell[];
}