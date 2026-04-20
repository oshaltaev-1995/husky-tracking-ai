import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import {
  AnalyticsSummaryResponse,
  WeeklyAnalyticsResponse,
  WeeklyCompareResponse,
} from '../models/analytics.model';

@Injectable({
  providedIn: 'root',
})
export class AnalyticsService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = environment.apiBaseUrl;

  getWeekly(dateFrom: string, dateTo: string): Observable<WeeklyAnalyticsResponse> {
    const params = new HttpParams().set('date_from', dateFrom).set('date_to', dateTo);

    return this.http.get<WeeklyAnalyticsResponse>(`${this.apiBaseUrl}/analytics/weekly`, {
      params,
    });
  }

  getSummary(dateFrom: string, dateTo: string): Observable<AnalyticsSummaryResponse> {
    const params = new HttpParams().set('date_from', dateFrom).set('date_to', dateTo);

    return this.http.get<AnalyticsSummaryResponse>(`${this.apiBaseUrl}/analytics/summary`, {
      params,
    });
  }

  compareWeeks(weekAStart: string, weekBStart: string): Observable<WeeklyCompareResponse> {
    const params = new HttpParams()
      .set('week_a_start', weekAStart)
      .set('week_b_start', weekBStart);

    return this.http.get<WeeklyCompareResponse>(`${this.apiBaseUrl}/analytics/weekly-compare`, {
      params,
    });
  }

  exportWorkbook(
    dateFrom: string,
    dateTo: string,
    weekAStart?: string,
    weekBStart?: string
  ): Observable<Blob> {
    let params = new HttpParams().set('date_from', dateFrom).set('date_to', dateTo);

    if (weekAStart && weekBStart) {
      params = params.set('week_a_start', weekAStart).set('week_b_start', weekBStart);
    }

    return this.http.get(`${this.apiBaseUrl}/exports/analytics-workbook.xlsx`, {
      params,
      responseType: 'blob',
    });
  }

  exportRawRunLogsCsv(dateFrom: string, dateTo: string): Observable<Blob> {
    const params = new HttpParams().set('date_from', dateFrom).set('date_to', dateTo);

    return this.http.get(`${this.apiBaseUrl}/exports/raw-run-logs.csv`, {
      params,
      responseType: 'blob',
    });
  }
}