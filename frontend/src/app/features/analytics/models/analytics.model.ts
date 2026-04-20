export interface WeeklyAnalyticsItem {
  week_start: string;
  week_end: string;
  week_label: string;
  total_km: number;
  worked_dogs: number;
  avg_km_per_worked_dog: number;
  high_risk_dogs: number;
  moderate_risk_dogs: number;
  underused_dogs: number;
}

export interface WeeklyAnalyticsResponse {
  date_from: string;
  date_to: string;
  items: WeeklyAnalyticsItem[];
}

export interface AnalyticsSummaryLatestWeek {
  week_start: string;
  week_end: string;
  week_label: string;
  total_km: number;
  worked_dogs: number;
  avg_km_per_worked_dog: number;
  high_risk_dogs: number;
  moderate_risk_dogs: number;
  underused_dogs: number;
}

export interface AnalyticsSummaryResponse {
  date_from: string;
  date_to: string;
  weeks_count: number;
  total_km: number;
  total_worked_dog_days: number;
  unique_worked_dogs: number;
  avg_km_per_worked_dog: number;
  latest_week_snapshot?: AnalyticsSummaryLatestWeek | null;
}

export interface WeeklyCompareDelta {
  total_km: number;
  worked_dogs: number;
  avg_km_per_worked_dog: number;
  high_risk_dogs: number;
  moderate_risk_dogs: number;
  underused_dogs: number;
}

export interface WeeklyCompareResponse {
  week_a: WeeklyAnalyticsItem;
  week_b: WeeklyAnalyticsItem;
  delta: WeeklyCompareDelta;
}