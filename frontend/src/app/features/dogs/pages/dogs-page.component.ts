import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { DogPhotoComponent } from '../../../shared/components/dog-photo/dog-photo.component';
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
import { DogSummary } from '../models/dog-summary.model';
import { DogsService } from '../services/dogs.service';
import {
  getDogAgeLabel,
  getDogCapabilities,
  getDogKennelPosition,
  getDogRoleLabel,
} from '../utils/dog-display.util';

@Component({
  selector: 'app-dogs-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, DogPhotoComponent, StatusBadgeComponent],
  templateUrl: './dogs-page.component.html',
  styleUrl: './dogs-page.component.scss',
})
export class DogsPageComponent implements OnInit {
  private readonly dogsService = inject(DogsService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  dogSummaries: DogSummary[] = [];
  filteredDogSummaries: DogSummary[] = [];

  isLoading = false;
  errorMessage = '';

  searchTerm = '';
  selectedKennelRow = '';
  selectedAvailability = '';
  selectedLifecycle = '';
  selectedRole = '';
  selectedRiskLevel = '';
  selectedUsageLevel = '';
  eligibilityFilter = '';
  excludedOnly = false;
  showArchived = false;
  selectedAsOfDate = '';

  kennelRows: string[] = [];
  availabilityOptions: string[] = [];
  lifecycleOptions: string[] = [];
  roleOptions: string[] = [];
  riskOptions: string[] = [];
  usageOptions: string[] = [];

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      this.searchTerm = params.get('search') ?? '';
      this.selectedKennelRow = params.get('kennel') ?? '';
      this.selectedAvailability = params.get('availability') ?? '';
      this.selectedLifecycle = params.get('lifecycle') ?? '';
      this.selectedRole = params.get('role') ?? '';
      this.selectedRiskLevel = params.get('risk') ?? '';
      this.selectedUsageLevel = params.get('usage') ?? '';
      this.eligibilityFilter = params.get('eligibility') ?? '';
      this.excludedOnly = params.get('excluded') === 'true';
      this.showArchived = params.get('showArchived') === 'true';
      this.selectedAsOfDate = params.get('as_of_date') ?? '';

      this.loadDogsSummary();
    });
  }

  loadDogsSummary(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.dogsService.getDogsSummary(this.selectedAsOfDate || null).subscribe({
      next: (dogSummaries) => {
        this.dogSummaries = dogSummaries;
        this.buildFilterOptions(dogSummaries);
        this.applyFilter(false);
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load dogs summary', error);
        this.errorMessage = 'Failed to load dogs summary from API.';
        this.isLoading = false;
      },
    });
  }

  applyFilter(syncUrl = true): void {
    const term = this.searchTerm.trim().toLowerCase();

    this.filteredDogSummaries = this.dogSummaries
      .filter((summary) => {
        const dog = summary.dog;

        if (
          !this.showArchived &&
          (dog.lifecycle_status === 'archived' || dog.lifecycle_status === 'deceased')
        ) {
          return false;
        }

        if (term && !dog.name.toLowerCase().includes(term)) {
          return false;
        }

        if (this.selectedKennelRow && (dog.kennel_row || '') !== this.selectedKennelRow) {
          return false;
        }

        if (
          this.selectedAvailability &&
          (dog.availability_status || '') !== this.selectedAvailability
        ) {
          return false;
        }

        if (
          this.selectedLifecycle &&
          (dog.lifecycle_status || '') !== this.selectedLifecycle
        ) {
          return false;
        }

        if (this.selectedRole && (dog.primary_role || '') !== this.selectedRole) {
          return false;
        }

        if (this.selectedRiskLevel && (summary.risk_level || '') !== this.selectedRiskLevel) {
          return false;
        }

        if (this.selectedUsageLevel && (summary.usage_level || '') !== this.selectedUsageLevel) {
          return false;
        }

        if (this.eligibilityFilter === 'eligible' && !summary.eligible_for_team_builder) {
          return false;
        }

        if (this.eligibilityFilter === 'not_eligible' && summary.eligible_for_team_builder) {
          return false;
        }

        if (this.excludedOnly && !dog.exclude_from_team_builder) {
          return false;
        }

        return true;
      })
      .sort((a, b) => a.dog.name.localeCompare(b.dog.name));

    if (syncUrl) {
      this.syncQueryParams();
    }
  }

  resetFilters(): void {
    this.searchTerm = '';
    this.selectedKennelRow = '';
    this.selectedAvailability = '';
    this.selectedLifecycle = '';
    this.selectedRole = '';
    this.selectedRiskLevel = '';
    this.selectedUsageLevel = '';
    this.eligibilityFilter = '';
    this.excludedOnly = false;
    this.showArchived = false;
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

  riskBadgeClass(value: string | null | undefined): string {
    return getRiskBadgeClass(value);
  }

  usageBadgeClass(value: string | null | undefined): string {
    return getUsageBadgeClass(value);
  }

  private buildFilterOptions(summaries: DogSummary[]): void {
    this.kennelRows = this.uniqueSortedStrings(summaries.map((s) => s.dog.kennel_row));
    this.availabilityOptions = this.uniqueSortedStrings(
      summaries.map((s) => s.dog.availability_status)
    );
    this.lifecycleOptions = this.uniqueSortedStrings(
      summaries.map((s) => s.dog.lifecycle_status)
    );
    this.roleOptions = this.uniqueSortedStrings(
      summaries.map((s) => s.dog.primary_role)
    );
    this.riskOptions = this.uniqueSortedStrings(
      summaries.map((s) => s.risk_level)
    );
    this.usageOptions = this.uniqueSortedStrings(
      summaries.map((s) => s.usage_level)
    );
  }

  private uniqueSortedStrings(values: Array<string | null | undefined>): string[] {
    return [...new Set(values.filter((v): v is string => Boolean(v && v.trim())))]
      .sort((a, b) => a.localeCompare(b));
  }

  private syncQueryParams(): void {
    const queryParams: Record<string, string | null> = {
      search: this.searchTerm || null,
      kennel: this.selectedKennelRow || null,
      availability: this.selectedAvailability || null,
      lifecycle: this.selectedLifecycle || null,
      role: this.selectedRole || null,
      risk: this.selectedRiskLevel || null,
      usage: this.selectedUsageLevel || null,
      eligibility: this.eligibilityFilter || null,
      excluded: this.excludedOnly ? 'true' : null,
      showArchived: this.showArchived ? 'true' : null,
      as_of_date: this.selectedAsOfDate || null,
    };

    this.router.navigate([], {
      relativeTo: this.route,
      queryParams,
      replaceUrl: true,
    });
  }
}