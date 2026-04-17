import { Dog } from '../models/dog.model';

export function getDogKennelPosition(dog: Dog): string {
  const parts: string[] = [];

  if (dog.kennel_row) {
    parts.push(String(dog.kennel_row));
  }

  if (dog.kennel_block !== null && dog.kennel_block !== undefined) {
    parts.push(`block ${dog.kennel_block}`);
  }

  if (dog.home_slot !== null && dog.home_slot !== undefined) {
    parts.push(`slot ${dog.home_slot}`);
  }

  return parts.length ? parts.join(' / ') : '—';
}

export function getDogRoleLabel(dog: Dog): string {
  return dog.primary_role || 'unknown';
}

export function getDogCapabilities(dog: Dog): string[] {
  const caps: string[] = [];

  if (dog.can_lead) caps.push('lead');
  if (dog.can_team) caps.push('team');
  if (dog.can_wheel) caps.push('wheel');

  return caps;
}

export function getDogAgeLabel(dog: Dog): string {
  if (!dog.birth_year) return '—';

  const currentYear = new Date().getFullYear();
  return `${currentYear - dog.birth_year} y`;
}