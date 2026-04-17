export function humanizeEligibilityReason(value: string | null | undefined): string {
  const normalized = (value || '').trim().toLowerCase();

  switch (normalized) {
    case 'manual_exclusion':
      return 'Manual exclusion';
    case 'lifecycle_status=retired':
      return 'Retired from active work';
    case 'lifecycle_status=deceased':
      return 'Marked as deceased';
    case 'lifecycle_status=archived':
      return 'Archived';
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
    case 'too_young':
      return 'Too young for planning';
    case 'not_available':
      return 'Not available';
    default:
      return humanizeGenericReason(value);
  }
}

export function humanizeGenericReason(value: string | null | undefined): string {
  if (!value) return 'No reason provided';

  return value
    .replace(/_/g, ' ')
    .replace(/=/g, ': ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/^\w/, (c) => c.toUpperCase());
}