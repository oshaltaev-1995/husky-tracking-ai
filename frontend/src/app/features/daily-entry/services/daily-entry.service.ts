import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { WorklogCreatePayload } from '../models/daily-entry.model';

export interface ExistingWorklogEntry {
  dog_id: number;
  work_date: string;
  worked: boolean;
  km: number;
  programs_10km?: number | null;
  programs_3km?: number | null;
  main_role?: string | null;
  notes?: string | null;
  week_label?: string | null;
  kennel_row?: string | null;
  home_slot?: number | null;
  status?: string | null;
}

@Injectable({
  providedIn: 'root',
})
export class DailyEntryService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = environment.apiBaseUrl;

  getLogsByDate(workDate: string): Observable<ExistingWorklogEntry[]> {
    const params = new HttpParams().set('work_date', workDate);
    return this.http.get<ExistingWorklogEntry[]>(`${this.apiBaseUrl}/worklogs/by-date`, { params });
  }

  logRun(payload: WorklogCreatePayload): Observable<unknown> {
    return this.http.post(`${this.apiBaseUrl}/worklogs/log-run`, payload);
  }
}