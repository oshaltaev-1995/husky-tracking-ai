import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import {
  AnalyticsSummaryResponse,
  WeeklyAnalyticsItem,
  WeeklyCompareResponse,
} from '../models/analytics.model';
import { AnalyticsService } from '../services/analytics.service';

interface Point {
  x: number;
  y: number;
}

interface AxisTick {
  value: number;
  y: number;
  label: string;
}

type CompareTone = 'good' | 'bad' | 'neutral';

@Component({
  selector: 'app-analytics-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './analytics-page.component.html',
  styleUrl: './analytics-page.component.scss',
})
export class AnalyticsPageComponent implements OnInit {
  private readonly analyticsService = inject(AnalyticsService);

  readonly weeklyItems = signal<WeeklyAnalyticsItem[]>([]);
  readonly summary = signal<AnalyticsSummaryResponse | null>(null);
  readonly comparison = signal<WeeklyCompareResponse | null>(null);

  readonly isLoading = signal(false);
  readonly isComparing = signal(false);
  readonly isExporting = signal(false);
  readonly isExportingWorkbook = signal(false);
  readonly isExportingPdf = signal(false);
  readonly isExportingRawLogs = signal(false);
  readonly errorMessage = signal('');

  dateFrom = '';
  dateTo = '';
  selectedWeekA = '';
  selectedWeekB = '';

  readonly maxKm = computed(() =>
    Math.max(...this.weeklyItems().map((item) => item.total_km), 0)
  );

  readonly maxWorkedDogs = computed(() =>
    Math.max(...this.weeklyItems().map((item) => item.worked_dogs), 0)
  );

  readonly maxAvgKm = computed(() =>
    Math.max(...this.weeklyItems().map((item) => item.avg_km_per_worked_dog), 0)
  );

  readonly maxRiskCount = computed(() =>
    Math.max(
      ...this.weeklyItems().flatMap((item) => [
        item.high_risk_dogs,
        item.moderate_risk_dogs,
        item.underused_dogs,
      ]),
      0
    )
  );

  ngOnInit(): void {
    this.applyPreset(8);
  }

  loadAnalytics(): void {
    if (!this.dateFrom || !this.dateTo) {
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set('');

    forkJoin({
      weekly: this.analyticsService.getWeekly(this.dateFrom, this.dateTo),
      summary: this.analyticsService.getSummary(this.dateFrom, this.dateTo),
    }).subscribe({
      next: ({ weekly, summary }) => {
        const items = weekly.items ?? [];
        this.weeklyItems.set(items);
        this.summary.set(summary);

        if (items.length > 0) {
          if (!this.selectedWeekA || !items.some((item) => item.week_start === this.selectedWeekA)) {
            this.selectedWeekA = items[0].week_start;
          }

          if (!this.selectedWeekB || !items.some((item) => item.week_start === this.selectedWeekB)) {
            this.selectedWeekB = items[items.length - 1].week_start;
          }
        } else {
          this.selectedWeekA = '';
          this.selectedWeekB = '';
          this.comparison.set(null);
        }

        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('Failed to load analytics', error);
        this.errorMessage.set('Failed to load analytics data from API.');
        this.isLoading.set(false);
      },
    });
  }

  applyPreset(weeks: number): void {
    const today = new Date();
    const end = this.toDateInputValue(today);

    const startDate = new Date();
    startDate.setDate(startDate.getDate() - (weeks * 7 - 1));

    this.dateFrom = this.toDateInputValue(startDate);
    this.dateTo = end;

    this.loadAnalytics();
  }

  applyFilters(): void {
    this.loadAnalytics();
  }

  compareSelectedWeeks(): void {
    if (!this.selectedWeekA || !this.selectedWeekB) {
      return;
    }

    this.isComparing.set(true);

    this.analyticsService.compareWeeks(this.selectedWeekA, this.selectedWeekB).subscribe({
      next: (response) => {
        this.comparison.set(response);
        this.isComparing.set(false);
      },
      error: (error) => {
        console.error('Failed to compare weeks', error);
        this.errorMessage.set('Failed to compare selected weeks.');
        this.isComparing.set(false);
      },
    });
  }

  exportWeeklyCsv(): void {
    const items = this.weeklyItems();
    if (!items.length) {
      return;
    }

    this.isExporting.set(true);

    try {
      const header = [
        'week_start',
        'week_end',
        'week_label',
        'total_km',
        'worked_dogs',
        'avg_km_per_worked_dog',
        'high_risk_dogs',
        'moderate_risk_dogs',
        'underused_dogs',
      ];

      const rows = items.map((item) => [
        item.week_start,
        item.week_end,
        item.week_label,
        item.total_km,
        item.worked_dogs,
        item.avg_km_per_worked_dog,
        item.high_risk_dogs,
        item.moderate_risk_dogs,
        item.underused_dogs,
      ]);

      const csv = [header, ...rows]
        .map((row) =>
          row.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(',')
        )
        .join('\n');

      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics-weekly-${this.dateFrom}-to-${this.dateTo}.csv`;
      a.click();

      window.URL.revokeObjectURL(url);
    } finally {
      this.isExporting.set(false);
    }
  }

  exportExcelWorkbook(): void {
    if (!this.dateFrom || !this.dateTo) {
      return;
    }

    this.isExportingWorkbook.set(true);

    this.analyticsService
      .exportWorkbook(
        this.dateFrom,
        this.dateTo,
        this.selectedWeekA || undefined,
        this.selectedWeekB || undefined
      )
      .subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `husky-analytics-${this.dateFrom}-to-${this.dateTo}.xlsx`;
          a.click();
          window.URL.revokeObjectURL(url);
          this.isExportingWorkbook.set(false);
        },
        error: (error) => {
          console.error('Failed to export workbook', error);
          this.errorMessage.set('Failed to export Excel workbook.');
          this.isExportingWorkbook.set(false);
        },
      });
  }

  exportSummaryPdf(): void {
    if (!this.dateFrom || !this.dateTo) {
      return;
    }

    this.isExportingPdf.set(true);

    this.analyticsService
      .exportSummaryPdf(
        this.dateFrom,
        this.dateTo,
        this.selectedWeekA || undefined,
        this.selectedWeekB || undefined
      )
      .subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `husky-analytics-summary-${this.dateFrom}-to-${this.dateTo}.pdf`;
          a.click();
          window.URL.revokeObjectURL(url);
          this.isExportingPdf.set(false);
        },
        error: (error) => {
          console.error('Failed to export PDF summary', error);
          this.errorMessage.set('Failed to export PDF summary.');
          this.isExportingPdf.set(false);
        },
      });
  }

  exportRawLogsCsv(): void {
    if (!this.dateFrom || !this.dateTo) {
      return;
    }

    this.isExportingRawLogs.set(true);

    this.analyticsService.exportRawRunLogsCsv(this.dateFrom, this.dateTo).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `husky-run-logs-${this.dateFrom}-to-${this.dateTo}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.isExportingRawLogs.set(false);
      },
      error: (error) => {
        console.error('Failed to export raw logs CSV', error);
        this.errorMessage.set('Failed to export raw run logs CSV.');
        this.isExportingRawLogs.set(false);
      },
    });
  }

  kmBarHeight(value: number): string {
    const max = this.maxKm();
    if (max <= 0) return '6px';
    return `${Math.max((value / max) * 180, 6)}px`;
  }

  workedDogsBarHeight(value: number): string {
    const max = this.maxWorkedDogs();
    if (max <= 0) return '6px';
    return `${Math.max((value / max) * 180, 6)}px`;
  }

  linePoints(values: number[], maxValue: number): string {
    if (!values.length) return '';

    const width = 1000;
    const height = 220;
    const paddingX = 24;
    const paddingY = 18;

    if (values.length === 1) {
      const y = this.scaleY(values[0], maxValue, height, paddingY);
      return `${width / 2},${y}`;
    }

    return values
      .map((value, index) => {
        const x =
          paddingX +
          (index * (width - paddingX * 2)) / Math.max(values.length - 1, 1);
        const y = this.scaleY(value, maxValue, height, paddingY);
        return `${x},${y}`;
      })
      .join(' ');
  }

  lineDots(values: number[], maxValue: number): Point[] {
    if (!values.length) return [];

    const width = 1000;
    const height = 220;
    const paddingX = 24;
    const paddingY = 18;

    if (values.length === 1) {
      return [{ x: width / 2, y: this.scaleY(values[0], maxValue, height, paddingY) }];
    }

    return values.map((value, index) => ({
      x:
        paddingX +
        (index * (width - paddingX * 2)) / Math.max(values.length - 1, 1),
      y: this.scaleY(value, maxValue, height, paddingY),
    }));
  }

  avgKmLinePoints(): string {
    return this.linePoints(
      this.weeklyItems().map((item) => item.avg_km_per_worked_dog),
      this.maxAvgKm()
    );
  }

  avgKmDots(): Point[] {
    return this.lineDots(
      this.weeklyItems().map((item) => item.avg_km_per_worked_dog),
      this.maxAvgKm()
    );
  }

  highRiskLinePoints(): string {
    return this.linePoints(
      this.weeklyItems().map((item) => item.high_risk_dogs),
      this.maxRiskCount()
    );
  }

  highRiskDots(): Point[] {
    return this.lineDots(
      this.weeklyItems().map((item) => item.high_risk_dogs),
      this.maxRiskCount()
    );
  }

  moderateRiskLinePoints(): string {
    return this.linePoints(
      this.weeklyItems().map((item) => item.moderate_risk_dogs),
      this.maxRiskCount()
    );
  }

  moderateRiskDots(): Point[] {
    return this.lineDots(
      this.weeklyItems().map((item) => item.moderate_risk_dogs),
      this.maxRiskCount()
    );
  }

  underusedLinePoints(): string {
    return this.linePoints(
      this.weeklyItems().map((item) => item.underused_dogs),
      this.maxRiskCount()
    );
  }

  underusedDots(): Point[] {
    return this.lineDots(
      this.weeklyItems().map((item) => item.underused_dogs),
      this.maxRiskCount()
    );
  }

  yAxisTicks(maxValue: number, decimals = 0): AxisTick[] {
    const height = 220;
    const paddingY = 18;
    const safeMax = maxValue > 0 ? maxValue : 1;

    return [0, 0.25, 0.5, 0.75, 1].map((ratio) => {
      const value = safeMax * (1 - ratio);
      const y = paddingY + (height - paddingY * 2) * ratio;

      return {
        value,
        y,
        label: decimals > 0 ? value.toFixed(decimals) : `${Math.round(value)}`,
      };
    });
  }

  shortWeekLabel(item: WeeklyAnalyticsItem): string {
    const start = new Date(item.week_start);
    const month = `${start.getMonth() + 1}`.padStart(2, '0');
    const day = `${start.getDate()}`.padStart(2, '0');
    return `${day}.${month}`;
  }

  formatCompact(value: number, decimals = 0): string {
    if (decimals > 0) {
      return value.toFixed(decimals);
    }
    return `${Math.round(value)}`;
  }

  pointLabelY(pointY: number, seriesIndex = 0): number {
    return Math.max(pointY - 10 - seriesIndex * 14, 12);
  }

  getBusiestWeek(): WeeklyAnalyticsItem | null {
    return this.pickMax((item) => item.total_km);
  }

  getHighestRiskWeek(): WeeklyAnalyticsItem | null {
    return this.pickMax((item) => item.high_risk_dogs);
  }

  getLowestUnderusedWeek(): WeeklyAnalyticsItem | null {
    return this.pickMin((item) => item.underused_dogs);
  }

  getBestAvgKmWeek(): WeeklyAnalyticsItem | null {
    return this.pickMax((item) => item.avg_km_per_worked_dog);
  }

  compareTone(metric: string, value: number): CompareTone {
    if (value === 0) {
      return 'neutral';
    }

    if (metric === 'total_km' || metric === 'worked_dogs' || metric === 'avg_km_per_worked_dog') {
      return value > 0 ? 'good' : 'bad';
    }

    if (metric === 'high_risk_dogs' || metric === 'moderate_risk_dogs' || metric === 'underused_dogs') {
      return value < 0 ? 'good' : 'bad';
    }

    return 'neutral';
  }

  compareDeltaClass(metric: string, value: number): string {
    const tone = this.compareTone(metric, value);
    if (tone === 'good') return 'delta-good';
    if (tone === 'bad') return 'delta-bad';
    return 'delta-neutral';
  }

  compareDeltaHint(metric: string, value: number): string {
    const tone = this.compareTone(metric, value);
    if (tone === 'neutral') return 'No change';

    if (metric === 'total_km') {
      return tone === 'good' ? 'More weekly distance' : 'Less weekly distance';
    }

    if (metric === 'worked_dogs') {
      return tone === 'good' ? 'More dogs worked' : 'Fewer dogs worked';
    }

    if (metric === 'avg_km_per_worked_dog') {
      return tone === 'good' ? 'Higher average load' : 'Lower average load';
    }

    if (metric === 'high_risk_dogs') {
      return tone === 'good' ? 'Risk reduced' : 'Risk increased';
    }

    if (metric === 'moderate_risk_dogs') {
      return tone === 'good' ? 'Moderate risk reduced' : 'Moderate risk increased';
    }

    if (metric === 'underused_dogs') {
      return tone === 'good' ? 'Underuse reduced' : 'Underuse increased';
    }

    return 'Change detected';
  }

  deltaPrefix(value: number): string {
    if (value > 0) return '+';
    return '';
  }

  private pickMax(selector: (item: WeeklyAnalyticsItem) => number): WeeklyAnalyticsItem | null {
    const items = this.weeklyItems();
    if (!items.length) return null;

    return items.reduce((best, current) => (selector(current) > selector(best) ? current : best));
  }

  private pickMin(selector: (item: WeeklyAnalyticsItem) => number): WeeklyAnalyticsItem | null {
    const items = this.weeklyItems();
    if (!items.length) return null;

    return items.reduce((best, current) => (selector(current) < selector(best) ? current : best));
  }

  private scaleY(value: number, maxValue: number, height: number, paddingY: number): number {
    if (maxValue <= 0) {
      return height - paddingY;
    }

    const normalized = value / maxValue;
    const drawableHeight = height - paddingY * 2;
    return height - paddingY - normalized * drawableHeight;
  }

  private toDateInputValue(date: Date): string {
    const year = date.getFullYear();
    const month = `${date.getMonth() + 1}`.padStart(2, '0');
    const day = `${date.getDate()}`.padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
}