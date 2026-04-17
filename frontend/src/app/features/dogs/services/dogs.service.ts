import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { DogEligibility } from '../models/dog-eligibility.model';
import { DogSummary } from '../models/dog-summary.model';
import { DogStatusUpdatePayload } from '../models/dog-status-update.model';
import { Dog } from '../models/dog.model';
import { DogRiskSummary } from '../models/dog-risk.model';
import { DogWorkload } from '../models/dog-workload.model';

@Injectable({
  providedIn: 'root',
})
export class DogsService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = `${environment.apiBaseUrl}/dogs`;

  getDogs(): Observable<Dog[]> {
    return this.http.get<Dog[]>(this.apiBaseUrl);
  }

  getDogsSummary(asOfDate?: string | null): Observable<DogSummary[]> {
    let params = new HttpParams();
    if (asOfDate) {
      params = params.set('as_of_date', asOfDate);
    }

    return this.http.get<DogSummary[]>(`${this.apiBaseUrl}/summary`, { params });
  }

  getDogById(id: number): Observable<Dog> {
    return this.http.get<Dog>(`${this.apiBaseUrl}/${id}`);
  }

  getDogEligibility(id: number, asOfDate?: string | null): Observable<DogEligibility> {
    let params = new HttpParams();
    if (asOfDate) {
      params = params.set('as_of_date', asOfDate);
    }

    return this.http.get<DogEligibility>(`${this.apiBaseUrl}/${id}/eligibility`, { params });
  }

  getDogWorkload(id: number, asOfDate?: string | null): Observable<DogWorkload> {
    let params = new HttpParams();
    if (asOfDate) {
      params = params.set('as_of_date', asOfDate);
    }

    return this.http.get<DogWorkload>(`${this.apiBaseUrl}/${id}/workload`, { params });
  }

  getDogRisk(id: number, asOfDate?: string | null): Observable<DogRiskSummary> {
    let params = new HttpParams();
    if (asOfDate) {
      params = params.set('as_of_date', asOfDate);
    }

    return this.http.get<DogRiskSummary>(`${this.apiBaseUrl}/${id}/risk`, { params });
  }

  createDog(payload: Partial<Dog>): Observable<Dog> {
    return this.http.post<Dog>(this.apiBaseUrl, payload);
  }

  updateDog(id: number, payload: Partial<Dog>): Observable<Dog> {
    return this.http.patch<Dog>(`${this.apiBaseUrl}/${id}`, payload);
  }

  updateDogStatus(id: number, payload: DogStatusUpdatePayload): Observable<Dog> {
    return this.http.patch<Dog>(`${this.apiBaseUrl}/${id}/status`, payload);
  }
}