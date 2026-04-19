export interface TeamBuilderRequest {
  program_type: string;
  sled_type: string;
  team_count: number;
  min_dogs_per_team: number;
  max_dogs_per_team: number;
  avoid_high_risk: boolean;
  prefer_underused: boolean;
}

export interface TeamDogAssignment {
  dog_id: number;
  dog_name: string;
  primary_role: string | null;
  assigned_role: string;
  risk_level: string;
  usage_level: string;
}

export interface HarnessDog {
  dog_id: number;
  dog_name: string;
  primary_role: string | null;
  assigned_role: string;
  risk_level: string;
  usage_level: string;
}

export interface HarnessRow {
  row_role: string;
  row_type: string;
  relation: string | null;
  dogs: HarnessDog[];
  warnings: string[];
}

export interface HarnessLayout {
  lead_rows: HarnessRow[];
  team_rows: HarnessRow[];
  wheel_rows: HarnessRow[];
}

export interface SuggestedTeam {
  team_number: number;
  dogs: TeamDogAssignment[];
  layout: HarnessLayout;
  warnings: string[];
}

export interface ExcludedDog {
  dog_id: number;
  dog_name: string;
  reasons: string[];
}

export interface TeamBuilderResponse {
  request: TeamBuilderRequest;
  teams: SuggestedTeam[];
  unassigned_dogs: TeamDogAssignment[];
  excluded_dogs: ExcludedDog[];
  global_warnings: string[];
}