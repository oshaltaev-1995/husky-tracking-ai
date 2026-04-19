import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import {
  TeamBuilderRequest,
  TeamBuilderResponse,
} from '../models/team-builder.model';

@Injectable({
  providedIn: 'root',
})
export class TeamBuilderService {
  private readonly http = inject(HttpClient);
  private readonly apiBaseUrl = environment.apiBaseUrl;

  buildTeams(payload: TeamBuilderRequest): Observable<TeamBuilderResponse> {
    return this.http.post<TeamBuilderResponse>(`${this.apiBaseUrl}/team-builder/build`, payload);
  }
}