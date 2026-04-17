export interface DogStatusUpdatePayload {
  lifecycle_status?: string;
  availability_status?: string;
  exclude_from_team_builder?: boolean;
  exclude_reason?: string | null;
}