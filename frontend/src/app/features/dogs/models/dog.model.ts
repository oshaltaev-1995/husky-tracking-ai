export interface Dog {
  id: number;
  name: string;
  external_id?: number | null;
  birth_year?: number | null;
  sex?: string | null;

  primary_role?: string | null;
  can_lead: boolean;
  can_team: boolean;
  can_wheel: boolean;

  lifecycle_status?: string | null;
  availability_status?: string | null;

  exclude_from_team_builder: boolean;
  exclude_reason?: string | null;

  kennel_row?: string | null;
  kennel_block?: number | null;
  home_slot?: number | null;

  status?: string | null;
  notes?: string | null;

  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}