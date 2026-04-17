export function normalizeStatus(value: string | null | undefined): string {
  return (value || '').trim().toLowerCase();
}

export function getAvailabilityBadgeClass(value: string | null | undefined): string {
  const status = normalizeStatus(value);

  switch (status) {
    case 'available':
      return 'badge-success';
    case 'rest':
      return 'badge-warning';
    case 'restricted':
      return 'badge-warning';
    case 'injured':
    case 'sick':
    case 'treatment':
      return 'badge-danger';
    default:
      return 'badge-neutral';
  }
}

export function getLifecycleBadgeClass(value: string | null | undefined): string {
  const status = normalizeStatus(value);

  switch (status) {
    case 'active':
      return 'badge-success';
    case 'retired':
      return 'badge-warning';
    case 'deceased':
    case 'archived':
      return 'badge-neutral';
    default:
      return 'badge-neutral';
  }
}

export function getRoleBadgeClass(value: string | null | undefined): string {
  const role = normalizeStatus(value);

  switch (role) {
    case 'lead':
      return 'badge-role-lead';
    case 'team':
    case 'center':
      return 'badge-role-team';
    case 'wheel':
      return 'badge-role-wheel';
    default:
      return 'badge-neutral';
  }
}