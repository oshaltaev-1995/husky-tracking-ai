export function humanizeDashboardReason(value: string | null | undefined): string {
  const normalized = (value || '').trim().toLowerCase();

  switch (normalized) {
    case 'high_risk_tomorrow':
      return 'High risk expected tomorrow';
    case 'moderate_risk_tomorrow':
      return 'Moderate risk expected tomorrow';
    case 'unavailable':
      return 'Currently unavailable';
    case 'injured':
      return 'Injured';
    case 'sick':
      return 'Sick';
    case 'treatment':
      return 'Under treatment';
    case 'rest':
      return 'On rest';
    case 'restricted':
      return 'Restricted workload';
    case 'retired':
      return 'Retired from active work';
    case 'excluded_from_team_builder':
      return 'Excluded from team builder';
    case 'underused':
      return 'Underused recently';
    case 'manual_exclusion':
      return 'Manual exclusion';
    case 'lifecycle_status=retired':
      return 'Retired from active work';
    case 'availability_status=restricted':
      return 'Restricted workload';
    case 'availability_status=rest':
      return 'On rest';
    case 'availability_status=injured':
      return 'Injured';
    case 'availability_status=sick':
      return 'Sick';
    case 'availability_status=treatment':
      return 'Under treatment';
    case 'manual_exclusion=true':
      return 'Manual exclusion';
    default:
      return humanizeSnakeCase(value);
  }
}

export function humanizeSnakeCase(value: string | null | undefined): string {
  if (!value) return 'No additional details';

  return value
    .replace(/_/g, ' ')
    .replace(/=/g, ': ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/^\w/, (c) => c.toUpperCase());
}

export function pickDashboardReason(
  reason?: string | null,
  reasons?: string[] | null
): string {
  if (reason) {
    return humanizeDashboardReason(reason);
  }

  if (reasons && reasons.length > 0) {
    return humanizeDashboardReason(reasons[0]);
  }

  return 'No additional details';
}