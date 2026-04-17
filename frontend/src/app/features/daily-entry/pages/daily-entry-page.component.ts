import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin, from, map, mergeMap, of, toArray, catchError } from 'rxjs';

import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import {
  getAvailabilityBadgeClass,
  getLifecycleBadgeClass,
} from '../../../shared/utils/dog-badge.util';
import { Dog } from '../../dogs/models/dog.model';
import { DogsService } from '../../dogs/services/dogs.service';
import { DailyEntryGroup, DailyEntryRow, WorklogCreatePayload } from '../models/daily-entry.model';
import { DailyEntryService, ExistingWorklogEntry } from '../services/daily-entry.service';

@Component({
  selector: 'app-daily-entry-page',
  standalone: true,
  imports: [CommonModule, FormsModule, StatusBadgeComponent],
  templateUrl: './daily-entry-page.component.html',
  styleUrl: './daily-entry-page.component.scss',
})
export class DailyEntryPageComponent implements OnInit {
  private readonly dogsService = inject(DogsService);
  private readonly dailyEntryService = inject(DailyEntryService);

  readonly kennelOrder = ['A', 'B-1', 'B-2', 'C-1', 'C-2', 'D-1', 'D-2', 'E', 'YKSIOT'];

  selectedDate = this.toDateInputValue(new Date());
  groups: DailyEntryGroup[] = [];

  isLoading = false;
  isSaving = false;
  errorMessage = '';
  successMessage = '';

  ngOnInit(): void {
    this.loadDay();
  }

  loadDay(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    forkJoin({
      dogs: this.dogsService.getDogs(),
      logs: this.dailyEntryService.getLogsByDate(this.selectedDate),
    }).subscribe({
      next: ({ dogs, logs }) => {
        const baseGroups = this.buildGroups(dogs);
        this.groups = this.applyExistingLogs(baseGroups, logs);
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load daily entry data', error);
        this.errorMessage = 'Failed to load daily entry data.';
        this.isLoading = false;
      },
    });
  }

  onDateChange(): void {
    this.loadDay();
  }

  setToday(): void {
    this.selectedDate = this.toDateInputValue(new Date());
    this.loadDay();
  }

  setYesterday(): void {
    const date = new Date();
    date.setDate(date.getDate() - 1);
    this.selectedDate = this.toDateInputValue(date);
    this.loadDay();
  }

  increment3(row: DailyEntryRow): void {
    row.programs_3km += 1;
    this.recalculateRow(row);
  }

  decrement3(row: DailyEntryRow): void {
    if (row.programs_3km > 0) {
      row.programs_3km -= 1;
      this.recalculateRow(row);
    }
  }

  increment10(row: DailyEntryRow): void {
    row.programs_10km += 1;
    this.recalculateRow(row);
  }

  decrement10(row: DailyEntryRow): void {
    if (row.programs_10km > 0) {
      row.programs_10km -= 1;
      this.recalculateRow(row);
    }
  }

  onManualCountChange(row: DailyEntryRow): void {
    row.programs_3km = Math.max(0, Number(row.programs_3km) || 0);
    row.programs_10km = Math.max(0, Number(row.programs_10km) || 0);
    this.recalculateRow(row);
  }

  recalculateRow(row: DailyEntryRow): void {
    row.total_km = row.programs_3km * 3 + row.programs_10km * 10;
    row.worked = row.total_km > 0;
  }

  clearDay(): void {
    this.successMessage = '';
    this.errorMessage = '';

    for (const group of this.groups) {
      for (const row of group.rows) {
        row.programs_3km = 0;
        row.programs_10km = 0;
        row.total_km = 0;
        row.worked = false;
        row.notes = '';
      }
    }
  }

  saveDay(): void {
    if (!this.selectedDate) {
      this.errorMessage = 'Please select a date first.';
      return;
    }

    this.isSaving = true;
    this.errorMessage = '';
    this.successMessage = '';

    const payloads = this.buildPayloads();

    if (payloads.length === 0) {
      this.isSaving = false;
      this.successMessage = `No changed rows to save for ${this.selectedDate}.`;
      return;
    }

    from(payloads)
      .pipe(
        mergeMap(
          (payload) =>
            this.dailyEntryService.logRun(payload).pipe(
              map(() => ({
                ok: true,
                dog_name: this.findDogName(payload.dog_id),
              })),
              catchError((error) => {
                console.error('Failed to save worklog', payload, error);
                return of({
                  ok: false,
                  dog_name: this.findDogName(payload.dog_id),
                });
              })
            ),
          8
        ),
        toArray()
      )
      .subscribe({
        next: (results) => {
          const successCount = results.filter((r) => r.ok).length;
          const failed = results.filter((r) => !r.ok).map((r) => r.dog_name);

          this.isSaving = false;

          if (failed.length === 0) {
            this.successMessage = `Saved ${successCount} daily log rows for ${this.selectedDate}.`;
            this.loadDay();
            return;
          }

          this.errorMessage =
            `Saved ${successCount} rows, but failed for ${failed.length} dogs: ` +
            failed.slice(0, 8).join(', ') +
            (failed.length > 8 ? '...' : '');
        },
        error: (error) => {
          console.error('Failed to save daily entry batch', error);
          this.errorMessage = 'Failed to save daily entry.';
          this.isSaving = false;
        },
      });
  }

  blockTotalKm(group: DailyEntryGroup): number {
    return group.rows.reduce((sum, row) => sum + row.total_km, 0);
  }

  blockWorkedCount(group: DailyEntryGroup): number {
    return group.rows.filter((row) => row.worked).length;
  }

  showStatusHints(row: DailyEntryRow): boolean {
    return Boolean(
      (row.availability_status && row.availability_status !== 'available') ||
      (row.lifecycle_status && row.lifecycle_status !== 'active')
    );
  }

  availabilityBadgeClass(value: string | null | undefined): string {
    return getAvailabilityBadgeClass(value);
  }

  lifecycleBadgeClass(value: string | null | undefined): string {
    return getLifecycleBadgeClass(value);
  }

  private buildPayloads(): WorklogCreatePayload[] {
    return this.groups.flatMap((group) =>
      group.rows
        .filter((row) => this.rowHasMeaningfulData(row))
        .map((row) => ({
          dog_id: row.dog_id,
          work_date: this.selectedDate,
          worked: row.worked,
          km: row.total_km,
          programs_10km: row.programs_10km,
          programs_3km: row.programs_3km,
          main_role: row.primary_role && row.primary_role !== 'none' ? row.primary_role : null,
          notes: row.notes.trim() || null,
        }))
    );
  }

  private rowHasMeaningfulData(row: DailyEntryRow): boolean {
    return row.programs_3km > 0 || row.programs_10km > 0 || row.notes.trim().length > 0 || row.worked;
  }

  private findDogName(dogId: number): string {
    for (const group of this.groups) {
      const row = group.rows.find((item) => item.dog_id === dogId);
      if (row) return row.dog_name;
    }
    return `dog ${dogId}`;
  }

  private buildGroups(dogs: Dog[]): DailyEntryGroup[] {
    const rows = dogs
      .filter((dog) => dog.lifecycle_status !== 'deceased' && dog.lifecycle_status !== 'archived')
      .map((dog) => this.toDailyEntryRow(dog));

    const grouped = new Map<string, DailyEntryRow[]>();

    for (const row of rows) {
      const key = this.normalizeKennelRow(row.kennel_row);
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)!.push(row);
    }

    const groups: DailyEntryGroup[] = [];

    for (const key of this.kennelOrder) {
      const groupRows = grouped.get(key) ?? [];
      if (groupRows.length === 0) continue;

      groups.push({
        key,
        label: this.displayKennelRow(key),
        rows: groupRows.sort((a, b) => this.compareRows(a, b)),
      });
    }

    for (const [key, groupRows] of grouped.entries()) {
      if (this.kennelOrder.includes(key)) continue;

      groups.push({
        key,
        label: this.displayKennelRow(key),
        rows: groupRows.sort((a, b) => this.compareRows(a, b)),
      });
    }

    return groups;
  }

  private applyExistingLogs(
    groups: DailyEntryGroup[],
    logs: ExistingWorklogEntry[]
  ): DailyEntryGroup[] {
    const logMap = new Map<number, ExistingWorklogEntry>();

    for (const log of logs) {
      logMap.set(log.dog_id, log);
    }

    for (const group of groups) {
      for (const row of group.rows) {
        const existing = logMap.get(row.dog_id);
        if (!existing) continue;

        row.programs_3km = Math.max(0, Number(existing.programs_3km) || 0);
        row.programs_10km = Math.max(0, Number(existing.programs_10km) || 0);
        row.total_km = Number(existing.km) || 0;
        row.worked = Boolean(existing.worked);
        row.notes = existing.notes ?? '';

        if (row.total_km === 0) {
          this.recalculateRow(row);
        }
      }
    }

    return groups;
  }

  private toDailyEntryRow(dog: Dog): DailyEntryRow {
    return {
      dog_id: dog.id,
      dog_name: dog.name,
      kennel_row: dog.kennel_row ?? null,
      kennel_block: dog.kennel_block ?? null,
      home_slot: dog.home_slot ?? null,
      primary_role: dog.primary_role ?? null,
      availability_status: dog.availability_status ?? null,
      lifecycle_status: dog.lifecycle_status ?? null,
      programs_3km: 0,
      programs_10km: 0,
      total_km: 0,
      worked: false,
      notes: '',
    };
  }

  private compareRows(a: DailyEntryRow, b: DailyEntryRow): number {
    const blockA = a.kennel_block ?? 999;
    const blockB = b.kennel_block ?? 999;
    if (blockA !== blockB) return blockA - blockB;

    const slotA = a.home_slot ?? 999;
    const slotB = b.home_slot ?? 999;
    if (slotA !== slotB) return slotA - slotB;

    return a.dog_name.localeCompare(b.dog_name);
  }

  private normalizeKennelRow(value: string | null | undefined): string {
    return (value || 'UNKNOWN').trim().toUpperCase();
  }

  private displayKennelRow(value: string): string {
    if (value === 'YKSIOT') return 'Yksiöt';
    return value;
  }

  private toDateInputValue(date: Date): string {
    const year = date.getFullYear();
    const month = `${date.getMonth() + 1}`.padStart(2, '0');
    const day = `${date.getDate()}`.padStart(2, '0');
    return `${year}-${month}-${day}`;
  }
}