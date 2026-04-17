export interface DogRiskMetrics {
  last_day_km?: number;
  km_3d?: number;
  km_7d?: number;
  km_14d?: number;
  worked_days_7d?: number;
  worked_days_14d?: number;
  days_since_last_run?: number | null;
  average_km_per_worked_day?: number;
  recent_avg_km_per_worked_day_7d?: number;
  load_vs_own_average_ratio?: number;
  last_day_vs_own_average_ratio?: number;
  current_hard_streak?: number;
  hard_days_count?: number;
  age_years_estimate?: number | null;
  age_group?: string | null;
  is_prime_age?: boolean;
  is_aging?: boolean;
  is_senior?: boolean;
}

export interface DogRiskSummary {
  dog_id: number;
  dog_name: string;
  risk_level: string;
  usage_level?: string;
  flags: string[];
  explanations: string[];
  metrics?: DogRiskMetrics;
}