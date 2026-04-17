import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { DogPhotoComponent } from '../../../shared/components/dog-photo/dog-photo.component';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import {
  getAvailabilityBadgeClass,
  getLifecycleBadgeClass,
  getRoleBadgeClass,
} from '../../../shared/utils/dog-badge.util';
import { DogSummary } from '../models/dog-summary.model';
import { DogsService } from '../services/dogs.service';
import {
  getDogAgeLabel,
  getDogCapabilities,
  getDogKennelPosition,
  getDogRoleLabel,
} from '../utils/dog-display.util';

@Component({
  selector: 'app-dog-archive-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, DogPhotoComponent, StatusBadgeComponent],
  templateUrl: './dog-archive-page.component.html',
  styleUrl: './dog-archive-page.component.scss',
})
export class DogArchivePageComponent implements OnInit {
  private readonly dogsService = inject(DogsService);

  dogSummaries: DogSummary[] = [];
  filteredDogSummaries: DogSummary[] = [];

  isLoading = false;
  errorMessage = '';

  searchTerm = '';
  lifecycleFilter = '';
  selectedKennelRow = '';

  lifecycleOptions: string[] = [];
  kennelRows: string[] = [];

  ngOnInit(): void {
    this.loadArchiveDogs();
  }

  loadArchiveDogs(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.dogsService.getDogsSummary().subscribe({
      next: (dogSummaries) => {
        this.dogSummaries = dogSummaries.filter((summary) =>
          summary.dog.lifecycle_status === 'archived' ||
          summary.dog.lifecycle_status === 'deceased'
        );

        this.lifecycleOptions = this.uniqueSortedStrings(
          this.dogSummaries.map((s) => s.dog.lifecycle_status)
        );
        this.kennelRows = this.uniqueSortedStrings(
          this.dogSummaries.map((s) => s.dog.kennel_row)
        );

        this.applyFilter();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load archive dogs', error);
        this.errorMessage = 'Failed to load archive dogs from API.';
        this.isLoading = false;
      },
    });
  }

  applyFilter(): void {
    const term = this.searchTerm.trim().toLowerCase();

    this.filteredDogSummaries = this.dogSummaries
      .filter((summary) => {
        const dog = summary.dog;

        if (term && !dog.name.toLowerCase().includes(term)) {
          return false;
        }

        if (this.lifecycleFilter && dog.lifecycle_status !== this.lifecycleFilter) {
          return false;
        }

        if (this.selectedKennelRow && (dog.kennel_row || '') !== this.selectedKennelRow) {
          return false;
        }

        return true;
      })
      .sort((a, b) => a.dog.name.localeCompare(b.dog.name));
  }

  resetFilters(): void {
    this.searchTerm = '';
    this.lifecycleFilter = '';
    this.selectedKennelRow = '';
    this.applyFilter();
  }

  kennelPosition(summary: DogSummary): string {
    return getDogKennelPosition(summary.dog);
  }

  roleLabel(summary: DogSummary): string {
    return getDogRoleLabel(summary.dog);
  }

  ageLabel(summary: DogSummary): string {
    return getDogAgeLabel(summary.dog);
  }

  capabilities(summary: DogSummary): string[] {
    return getDogCapabilities(summary.dog);
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

  private uniqueSortedStrings(values: Array<string | null | undefined>): string[] {
    return [...new Set(values.filter((v): v is string => Boolean(v && v.trim())))]
      .sort((a, b) => a.localeCompare(b));
  }
}