export interface RecentWorklog {
  work_date: string;
  km: number;
  worked: boolean;
  week_label?: string | null;
  programs_10km?: number | null;
  programs_3km?: number | null;
  main_role?: string | null;
  status?: string | null;
  notes?: string | null;
}

export interface DogWorkload {
  dog_id: number;
  dog_name: string;

  total_worklogs: number;
  worked_days: number;
  total_km: number;
  average_km_per_worked_day: number;

  last_work_date: string | null;
  last_day_km: number | null;
  days_since_last_run: number | null;

  worked_days_7d: number;
  worked_days_14d: number;

  km_3d: number;
  km_7d: number;
  km_14d: number;

  recent_avg_km_per_worked_day_7d: number;
  load_vs_own_average_ratio: number;
  last_day_vs_own_average_ratio: number;

  hard_day_km_threshold: number;
  hard_days_count: number;
  current_hard_streak: number;

  recent_worklogs: RecentWorklog[];
}