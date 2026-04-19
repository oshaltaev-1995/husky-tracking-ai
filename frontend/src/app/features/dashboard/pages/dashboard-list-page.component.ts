import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { combineLatest } from 'rxjs';

import { DogPhotoComponent } from '../../../shared/components/dog-photo/dog-photo.component';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import {
  getAvailabilityBadgeClass,
  getLifecycleBadgeClass,
} from '../../../shared/utils/dog-badge.util';
import {
  getRiskBadgeClass,
  getUsageBadgeClass,
} from '../../../shared/utils/risk-badge.util';
import { humanizeEligibilityReason } from '../../dogs/utils/dog-eligibility.util';
import { humanizeRiskFlag } from '../../dogs/utils/dog-risk.util';
import { DashboardDogNoteItem } from '../models/dashboard.model';
import { DashboardService } from '../services/dashboard.service';
import { pickDashboardReason } from '../utils/dashboard-text.util';

type ListKind = 'watchlist' | 'blockers' | 'underused';

@Component({
  selector: 'app-dashboard-list-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    StatusBadgeComponent,
    DogPhotoComponent,
  ],
  templateUrl: './dashboard-list-page.component.html',
  styleUrl: './dashboard-list-page.component.scss',
})
export class DashboardListPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly dashboardService = inject(DashboardService);

  kind: ListKind = 'watchlist';
  selectedDate = '';
  items: DashboardDogNoteItem[] = [];

  isLoading = false;
  errorMessage = '';

  ngOnInit(): void {
    combineLatest([this.route.paramMap, this.route.queryParamMap]).subscribe(
      ([params, queryParams]) => {
        const kindParam = params.get('kind');
        this.kind = this.normalizeKind(kindParam);
        this.selectedDate = queryParams.get('as_of_date') ?? '';
        this.loadItems();
      }
    );
  }

  get pageTitle(): string {
    switch (this.kind) {
      case 'blockers':
        return 'Planning blockers';
      case 'underused':
        return 'Underused dogs';
      default:
        return 'Operational watchlist';
    }
  }

  get pageDescription(): string {
    switch (this.kind) {
      case 'blockers':
        return 'Dogs currently unavailable for planning based on the same logic used on the dashboard.';
      case 'underused':
        return 'Operationally eligible dogs with low recent usage for the selected date.';
      default:
        return 'Dogs needing closer operational attention for the selected date.';
    }
  }

  setToday(): void {
    this.selectedDate = this.toDateInputValue(new Date());
    this.applySelectedDate();
  }

  setYesterday(): void {
    const date = new Date();
    date.setDate(date.getDate() - 1);
    this.selectedDate = this.toDateInputValue(date);
    this.applySelectedDate();
  }

  applySelectedDate(): void {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        as_of_date: this.selectedDate || null,
      },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  riskBadgeClass(value: string | null | undefined): string {
    return getRiskBadgeClass(value);
  }

  usageBadgeClass(value: string | null | undefined): string {
    return getUsageBadgeClass(value);
  }

  availabilityBadgeClass(value: string | null | undefined): string {
    return getAvailabilityBadgeClass(value);
  }

  lifecycleBadgeClass(value: string | null | undefined): string {
    return getLifecycleBadgeClass(value);
  }

  itemReason(item: DashboardDogNoteItem): string {
    return this.humanizeReason(pickDashboardReason(item.reason, item.reasons));
  }

  detailReasons(item: DashboardDogNoteItem): string[] {
    const raw = Array.isArray(item.reasons) ? item.reasons : [];
    const unique = [...new Set(raw.filter(Boolean))];
    return unique.map((reason) => this.humanizeReason(reason));
  }

  private humanizeReason(reason: string | null | undefined): string {
    if (!reason) return '—';

    if (reason.includes('=')) {
      return humanizeEligibilityReason(reason);
    }

    if (reason === 'manual_exclusion') {
      return humanizeEligibilityReason(reason);
    }

    if (reason === 'too_young') {
      return humanizeEligibilityReason(reason);
    }

    return humanizeRiskFlag(reason);
  }

  private loadItems(): void {
    this.isLoading = true;
    this.errorMessage = '';

    const asOfDate = this.selectedDate || null;

    const request =
      this.kind === 'blockers'
        ? this.dashboardService.getPlanningBlockers(asOfDate)
        : this.kind === 'underused'
        ? this.dashboardService.getUnderusedDogs(asOfDate)
        : this.dashboardService.getOperationalWatchlist(asOfDate);

    request.subscribe({
      next: (items) => {
        this.items = items;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load dashboard list', error);
        this.errorMessage = 'Failed to load operational list from API.';
        this.isLoading = false;
      },
    });
  }

  private normalizeKind(value: string | null): ListKind {
    if (value === 'blockers') return 'blockers';
    if (value === 'underused') return 'underused';
    return 'watchlist';
  }

  private toDateInputValue(date: Date): string {
    const year = date.getFullYear();
    const month = `${date.getMonth() + 1}`.padStart(2, '0');
    const day = `${date.getDate()}`.padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
}