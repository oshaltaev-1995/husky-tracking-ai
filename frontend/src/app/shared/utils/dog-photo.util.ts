export function normalizeDogPhotoName(name: string | null | undefined): string {
  if (!name) return 'unknown';

  return name
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-');
}

export function getDogPhotoUrl(name: string | null | undefined): string {
  const normalized = normalizeDogPhotoName(name);
  return `/dog-photos/${normalized}.png`;
}