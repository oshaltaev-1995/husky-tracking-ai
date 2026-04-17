export function normalizeRiskValue(value: string | null | undefined): string {
  return (value || '').trim().toLowerCase();
}

export function getRiskBadgeClass(value: string | null | undefined): string {
  const risk = normalizeRiskValue(value);

  switch (risk) {
    case 'low':
      return 'badge-success';
    case 'moderate':
      return 'badge-warning';
    case 'high':
      return 'badge-danger';
    default:
      return 'badge-neutral';
  }
}

export function getUsageBadgeClass(value: string | null | undefined): string {
  const usage = normalizeRiskValue(value);

  switch (usage) {
    case 'underused':
      return 'badge-role-team';
    case 'normal':
      return 'badge-success';
    case 'heavy':
      return 'badge-warning';
    default:
      return 'badge-neutral';
  }
}