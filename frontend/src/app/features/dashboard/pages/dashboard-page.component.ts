import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import {
  getAvailabilityBadgeClass,
  getLifecycleBadgeClass,
  getRoleBadgeClass,
} from '../../../shared/utils/dog-badge.util';
import {
  getRiskBadgeClass,
  getUsageBadgeClass,
} from '../../../shared/utils/risk-badge.util';
import {
  DashboardDogNoteItem,
  DashboardOverview,
  HeatmapCell,
} from '../models/dashboard.model';
import { DashboardService } from '../services/dashboard.service';
import { pickDashboardReason } from '../utils/dashboard-text.util';

interface HeatmapGroup {
  key: string;
  label: string;
  items: HeatmapCell[];
}

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, StatusBadgeComponent],
  templateUrl: './dashboard-page.component.html',
  styleUrl: './dashboard-page.component.scss',
})
export class DashboardPageComponent implements OnInit {
  private readonly dashboardService = inject(DashboardService);

  overview: DashboardOverview | null = null;
  watchlist: DashboardDogNoteItem[] = [];
  blockers: DashboardDogNoteItem[] = [];
  underused: DashboardDogNoteItem[] = [];
  heatmapGroups: HeatmapGroup[] = [];

  selectedDate = '';

  isLoading = false;
  errorMessage = '';

  private readonly kennelOrder = ['A', 'B-1', 'B-2', 'C-1', 'C-2', 'D-1', 'D-2', 'E', 'YKSIOT'];

  ngOnInit(): void {
    this.loadDashboard();
  }

  loadDashboard(asOfDate?: string | null): void {
    this.isLoading = true;
    this.errorMessage = '';

    const effectiveDate = asOfDate || null;

    forkJoin({
      overview: this.dashboardService.getOverview(effectiveDate),
      heatmap: this.dashboardService.getHeatmap(effectiveDate),
      watchlist: this.dashboardService.getOperationalWatchlist(effectiveDate),
      blockers: this.dashboardService.getPlanningBlockers(effectiveDate),
      underused: this.dashboardService.getUnderusedDogs(effectiveDate),
    }).subscribe({
      next: ({ overview, heatmap, watchlist, blockers, underused }) => {
        this.overview = overview;
        this.heatmapGroups = this.buildHeatmapGroups(heatmap.items);
        this.watchlist = watchlist.slice(0, 5);
        this.blockers = blockers.slice(0, 5);
        this.underused = underused.slice(0, 5);
        this.selectedDate = overview?.as_of_date || this.selectedDate;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load dashboard data', error);
        this.errorMessage = 'Failed to load dashboard data from API.';
        this.isLoading = false;
      },
    });
  }

  applySelectedDate(): void {
    if (!this.selectedDate) return;
    this.loadDashboard(this.selectedDate);
  }

  loadLatest(): void {
    this.selectedDate = '';
    this.loadDashboard();
  }

  setYesterday(): void {
    const date = new Date();
    date.setDate(date.getDate() - 1);
    this.selectedDate = this.toDateInputValue(date);
    this.loadDashboard(this.selectedDate);
  }

  availabilityBadgeClass(value: string | null | undefined): string {
    return getAvailabilityBadgeClass(value);
  }

  lifecycleBadgeClass(value: string | null | undefined): string {
    return getLifecycleBadgeClass(value);
  }

  roleBadgeClass(value: string | null | undefined): string {
    return getRoleBadgeClass(value);
  }

  riskBadgeClass(value: string | null | undefined): string {
    return getRiskBadgeClass(value);
  }

  usageBadgeClass(value: string | null | undefined): string {
    return getUsageBadgeClass(value);
  }

  itemReason(item: DashboardDogNoteItem): string {
    return pickDashboardReason(item.reason, item.reasons);
  }

  heatmapWorkedLabel(item: HeatmapCell): string {
    return item.worked_today ? 'Worked' : 'No run';
  }

  private buildHeatmapGroups(items: HeatmapCell[]): HeatmapGroup[] {
    const grouped = new Map<string, HeatmapCell[]>();

    for (const item of items) {
      if (item.lifecycle_status === 'archived' || item.lifecycle_status === 'deceased') {
        continue;
      }

      const key = (item.kennel_row || 'UNKNOWN').toUpperCase().trim();
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)!.push(item);
    }

    const result: HeatmapGroup[] = [];

    for (const key of this.kennelOrder) {
      const groupItems = grouped.get(key) ?? [];
      if (!groupItems.length) continue;

      result.push({
        key,
        label: key === 'YKSIOT' ? 'Yksiöt' : key,
        items: groupItems.sort((a, b) => {
          const slotA = a.home_slot ?? 999;
          const slotB = b.home_slot ?? 999;
          if (slotA !== slotB) return slotA - slotB;
          return a.dog_name.localeCompare(b.dog_name);
        }),
      });
    }

    for (const [key, groupItems] of grouped.entries()) {
      if (this.kennelOrder.includes(key)) continue;

      result.push({
        key,
        label: key,
        items: groupItems.sort((a, b) => {
          const slotA = a.home_slot ?? 999;
          const slotB = b.home_slot ?? 999;
          if (slotA !== slotB) return slotA - slotB;
          return a.dog_name.localeCompare(b.dog_name);
        }),
      });
    }

    return result;
  }

  private toDateInputValue(date: Date): string {
    const year = date.getFullYear();
    const month = `${date.getMonth() + 1}`.padStart(2, '0');
    const day = `${date.getDate()}`.padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
}