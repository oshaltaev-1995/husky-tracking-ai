export interface DogCreatePayload {
  name: string;
  external_id?: number | null;
  birth_year?: number | null;
  sex?: string | null;
  kennel_row?: string | null;
  kennel_block?: number | null;
  home_slot?: number | null;
  primary_role?: string | null;
  can_lead: boolean;
  can_team: boolean;
  can_wheel: boolean;
  status?: string | null;
  notes?: string | null;
  is_active: boolean;
  lifecycle_status: string;
  availability_status: string;
  exclude_from_team_builder: boolean;
  exclude_reason?: string | null;
}