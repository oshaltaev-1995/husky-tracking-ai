export interface DailyEntryRow {
  dog_id: number;
  dog_name: string;
  kennel_row?: string | null;
  kennel_block?: number | null;
  home_slot?: number | null;
  primary_role?: string | null;
  availability_status?: string | null;
  lifecycle_status?: string | null;

  programs_3km: number;
  programs_10km: number;
  total_km: number;
  worked: boolean;
  notes: string;
}

export interface DailyEntryGroup {
  key: string;
  label: string;
  rows: DailyEntryRow[];
}

export interface WorklogCreatePayload {
  dog_id: number;
  work_date: string;
  worked: boolean;
  km: number;
  programs_10km: number;
  programs_3km: number;
  main_role?: string | null;
  notes?: string | null;
}