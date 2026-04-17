import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

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
import { DogEligibility } from '../models/dog-eligibility.model';
import { DogStatusUpdatePayload } from '../models/dog-status-update.model';
import { Dog } from '../models/dog.model';
import { DogRiskSummary } from '../models/dog-risk.model';
import { DogWorkload, RecentWorklog } from '../models/dog-workload.model';
import { DogsService } from '../services/dogs.service';
import { buildRiskSummary, humanizeRiskFlag } from '../utils/dog-risk.util';
import { humanizeEligibilityReason } from '../utils/dog-eligibility.util';
import {
  getDogAgeLabel,
  getDogCapabilities,
  getDogKennelPosition,
  getDogRoleLabel,
} from '../utils/dog-display.util';

@Component({
  selector: 'app-dog-detail-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, DogPhotoComponent, StatusBadgeComponent],
  templateUrl: './dog-detail-page.component.html',
  styleUrl: './dog-detail-page.component.scss',
})
export class DogDetailPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly dogsService = inject(DogsService);

  dog: Dog | null = null;
  eligibility: DogEligibility | null = null;
  workload: DogWorkload | null = null;
  risk: DogRiskSummary | null = null;

  isLoading = false;
  isSavingStatus = false;
  errorMessage = '';
  statusSuccessMessage = '';
  statusErrorMessage = '';

  statusForm: DogStatusUpdatePayload = {
    lifecycle_status: 'active',
    availability_status: 'available',
    exclude_from_team_builder: false,
    exclude_reason: null,
  };

  readonly lifecycleOptions = ['active', 'retired', 'deceased', 'archived'];
  readonly availabilityOptions = ['available', 'rest', 'restricted', 'injured', 'sick', 'treatment'];

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    const dogId = Number(idParam);

    if (!dogId || Number.isNaN(dogId)) {
      this.errorMessage = 'Invalid dog id.';
      return;
    }

    this.loadDogData(dogId);
  }

  loadDogData(id: number): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.statusSuccessMessage = '';
    this.statusErrorMessage = '';

    forkJoin({
      dog: this.dogsService.getDogById(id),
      eligibility: this.dogsService.getDogEligibility(id),
      workload: this.dogsService.getDogWorkload(id),
      risk: this.dogsService.getDogRisk(id),
    }).subscribe({
      next: ({ dog, eligibility, workload, risk }) => {
        this.dog = dog;
        this.eligibility = eligibility;
        this.workload = workload;
        this.risk = risk;

        this.statusForm = {
          lifecycle_status: dog.lifecycle_status || 'active',
          availability_status: dog.availability_status || 'available',
          exclude_from_team_builder: dog.exclude_from_team_builder,
          exclude_reason: dog.exclude_reason,
        };

        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load dog profile data', error);
        this.errorMessage = 'Failed to load dog profile data from API.';
        this.isLoading = false;
      },
    });
  }

  saveStatus(): void {
    if (!this.dog) return;

    this.isSavingStatus = true;
    this.statusSuccessMessage = '';
    this.statusErrorMessage = '';

    const payload: DogStatusUpdatePayload = {
      lifecycle_status: this.statusForm.lifecycle_status || 'active',
      availability_status: this.statusForm.availability_status || 'available',
      exclude_from_team_builder: Boolean(this.statusForm.exclude_from_team_builder),
      exclude_reason: this.emptyToNull(this.statusForm.exclude_reason),
    };

    this.dogsService.updateDogStatus(this.dog.id, payload).subscribe({
      next: (updatedDog) => {
        this.dog = updatedDog;
        this.statusForm = {
          lifecycle_status: updatedDog.lifecycle_status || 'active',
          availability_status: updatedDog.availability_status || 'available',
          exclude_from_team_builder: updatedDog.exclude_from_team_builder,
          exclude_reason: updatedDog.exclude_reason,
        };
        this.statusSuccessMessage = 'Operational status updated.';
        this.isSavingStatus = false;
      },
      error: (error) => {
        console.error('Failed to update dog status', error);
        this.statusErrorMessage = 'Failed to update operational status.';
        this.isSavingStatus = false;
      },
    });
  }

  kennelPosition(): string {
    return this.dog ? getDogKennelPosition(this.dog) : '—';
  }

  roleLabel(): string {
    return this.dog ? getDogRoleLabel(this.dog) : '—';
  }

  ageLabel(): string {
    return this.dog ? getDogAgeLabel(this.dog) : '—';
  }

  capabilities(): string[] {
    return this.dog ? getDogCapabilities(this.dog) : [];
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

  humanizeRiskFlag(flag: string): string {
    return humanizeRiskFlag(flag);
  }

  humanizeEligibilityReason(reason: string): string {
    return humanizeEligibilityReason(reason);
  }

  riskSummary(): string {
    if (!this.risk) return '—';

    return buildRiskSummary(
      this.risk.risk_level,
      this.risk.usage_level,
      this.risk.explanations
    );
  }

  recentWorklogs(): RecentWorklog[] {
    return this.workload?.recent_worklogs ?? [];
  }

  showYoungDogHint(): boolean {
    if (!this.dog) return false;

    const birthYear = this.dog.birth_year;
    if (!birthYear) return false;

    const currentYear = new Date().getFullYear();
    const roughAge = currentYear - birthYear;

    return (
      roughAge <= 1 &&
      this.dog.lifecycle_status === 'active' &&
      this.dog.availability_status === 'available' &&
      !this.dog.exclude_from_team_builder
    );
  }

  youngDogHintText(): string {
    return 'This appears to be a very young dog. If it is not yet ready for safari work, set Availability status to Restricted and exclude it from team builder.';
  }

  private emptyToNull(value: string | null | undefined): string | null {
    if (value === null || value === undefined) return null;
    const trimmed = value.trim();
    return trimmed ? trimmed : null;
  }
}