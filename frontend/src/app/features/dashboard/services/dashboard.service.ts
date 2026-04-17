import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { map, Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import {
  DashboardDogNoteItem,
  DashboardHeatmapResponse,
  DashboardOverview,
  HeatmapCell,
  TodayDogStat,
  TodayStatsResponse,
} from '../models/dashboard.model';

@Injectable({
  providedIn: 'root',
})
export class DashboardService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = environment.apiBaseUrl;

  getOverview(asOfDate?: string | null): Observable<DashboardOverview> {
    let params = new HttpParams();
    if (asOfDate) {
      params = params.set('as_of_date', asOfDate);
    }

    return this.http.get<DashboardOverview>(`${this.apiBaseUrl}/dashboard/overview`, {
      params,
    });
  }

  getTodayStats(asOfDate?: string | null): Observable<TodayStatsResponse> {
    let params = new HttpParams();
    if (asOfDate) {
      params = params.set('as_of_date', asOfDate);
    }

    return this.http.get<any>(`${this.apiBaseUrl}/dashboard/today`, { params }).pipe(
      map((raw) => {
        const rawDogs = Array.isArray(raw?.items)
          ? raw.items
          : Array.isArray(raw?.dogs)
          ? raw.dogs
          : Array.isArray(raw)
          ? raw
          : [];

        const dogs: TodayDogStat[] = rawDogs.map((item: any) => ({
          dog_id: item.dog_id ?? item.id ?? 0,
          dog_name: item.dog_name ?? item.name ?? 'Unknown',
          worked: item.worked_today ?? item.worked ?? false,
          km: item.km_today ?? item.km ?? 0,
          main_role: item.primary_role ?? item.main_role ?? item.role ?? null,
          runs_today: item.runs_today ?? item.run_count ?? null,
          availability_status: item.availability_status ?? null,
          lifecycle_status: item.lifecycle_status ?? null,
        }));

        return {
          as_of_date: raw?.as_of_date ?? null,
          dogs,
        };
      })
    );
  }

  getHeatmap(asOfDate?: string | null): Observable<DashboardHeatmapResponse> {
    let params = new HttpParams();
    if (asOfDate) {
      params = params.set('as_of_date', asOfDate);
    }

    return this.http.get<any>(`${this.apiBaseUrl}/dashboard/heatmap`, { params }).pipe(
      map((raw) => {
        const rawItems = Array.isArray(raw?.items)
          ? raw.items
          : Array.isArray(raw)
          ? raw
          : [];

        const items: HeatmapCell[] = rawItems.map((item: any) => ({
          dog_id: item.dog_id ?? item.id ?? 0,
          dog_name: item.dog_name ?? item.name ?? 'Unknown',
          kennel_row: item.kennel_row ?? null,
          kennel_block: item.kennel_block ?? null,
          home_slot: item.home_slot ?? null,
          worked_today: item.worked_today ?? item.worked ?? false,
          km_today: item.km_today ?? item.km ?? 0,
          risk_level: item.risk_level ?? 'unknown',
          availability_status: item.availability_status ?? null,
          lifecycle_status: item.lifecycle_status ?? null,
        }));

        return {
          as_of_date: raw?.as_of_date ?? null,
          items,
        };
      })
    );
  }

  getOperationalWatchlist(asOfDate?: string | null): Observable<DashboardDogNoteItem[]> {
    let params = new HttpParams();
    if (asOfDate) {
      params = params.set('as_of_date', asOfDate);
    }

    return this.http
      .get<any>(`${this.apiBaseUrl}/dogs/operational-watchlist`, { params })
      .pipe(map((raw) => this.normalizeListResponse(raw)));
  }

  getPlanningBlockers(asOfDate?: string | null): Observable<DashboardDogNoteItem[]> {
    let params = new HttpParams();
    if (asOfDate) {
      params = params.set('as_of_date', asOfDate);
    }

    return this.http
      .get<any>(`${this.apiBaseUrl}/dogs/planning-blockers`, { params })
      .pipe(map((raw) => this.normalizeListResponse(raw)));
  }

  getUnderusedDogs(asOfDate?: string | null): Observable<DashboardDogNoteItem[]> {
    let params = new HttpParams();
    if (asOfDate) {
      params = params.set('as_of_date', asOfDate);
    }

    return this.http
      .get<any>(`${this.apiBaseUrl}/dogs/underused`, { params })
      .pipe(map((raw) => this.normalizeListResponse(raw)));
  }

  private normalizeListResponse(raw: any): DashboardDogNoteItem[] {
    if (Array.isArray(raw)) return raw;
    if (Array.isArray(raw?.dogs)) return raw.dogs;
    if (Array.isArray(raw?.items)) return raw.items;
    return [];
  }
}