const RISK_FLAG_LABELS: Record<string, string> = {
  hard_last_day: 'Hard workload on the last working day',
  hard_streak: 'Several hard days in a row',
  two_hard_days_in_a_row: 'Two hard days in a row',

  high_7d_load: 'High 7-day workload',
  elevated_7d_load: 'Elevated 7-day workload',
  high_14d_load: 'High 14-day workload',

  above_own_average_load: 'Recent load is well above this dog’s usual average',
  moderately_above_own_average: 'Recent load is above this dog’s usual average',

  very_heavy_last_day_for_this_dog: 'Last day was much heavier than usual for this dog',
  heavy_last_day_for_this_dog: 'Last day was heavier than usual for this dog',

  dense_working_week: 'Dense working week',
  recent_heavy_block_despite_rest_day: 'Recent heavy workload despite a rest day',

  aging_dog_high_single_day_load: 'High single-day load for an aging dog',
  aging_dog_elevated_single_day_load: 'Elevated single-day load for an aging dog',
  aging_dog_high_recent_load: 'High recent load for an aging dog',
  aging_dog_moderate_recent_load: 'Moderate recent load for an aging dog',
  aging_dog_dense_schedule: 'Dense recent schedule for an aging dog',

  senior_dog_high_single_day_load: 'High single-day load for a senior dog',
  senior_dog_elevated_single_day_load: 'Elevated single-day load for a senior dog',
  senior_dog_high_recent_load: 'High recent load for a senior dog',
  senior_dog_moderate_recent_load: 'Moderate recent load for a senior dog',
  senior_dog_dense_schedule: 'Dense recent schedule for a senior dog',

  long_idle_period: 'Long idle period',
  very_low_recent_usage: 'Very low recent usage',
  young_dog_low_usage_context: 'Low usage may be normal for a very young dog',

  high_risk_tomorrow: 'High risk expected tomorrow',
  moderate_risk_tomorrow: 'Moderate risk expected tomorrow',
  underused_recently: 'Underused recently',
};

export function humanizeRiskFlag(flag: string): string {
  return RISK_FLAG_LABELS[flag] ?? flag.replaceAll('_', ' ');
}

export function buildRiskSummary(
  riskLevel: string | null | undefined,
  usageLevel: string | null | undefined,
  explanations: string[] | null | undefined
): string {
  const firstExplanation = explanations?.[0]?.trim();

  if (firstExplanation) {
    return firstExplanation;
  }

  if (riskLevel === 'high') {
    return 'This dog has a high current workload risk and should be reviewed carefully before planning.';
  }

  if (riskLevel === 'moderate') {
    return 'This dog has a moderate workload risk and may need cautious planning.';
  }

  if (usageLevel === 'underused') {
    return 'This dog appears underused recently and may be considered for work if otherwise suitable.';
  }

  return 'No major workload warning signals were detected.';
}