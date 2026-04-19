import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';
import {
  getRiskBadgeClass,
  getUsageBadgeClass,
} from '../../../shared/utils/risk-badge.util';
import { humanizeEligibilityReason } from '../../dogs/utils/dog-eligibility.util';
import { humanizeRiskFlag } from '../../dogs/utils/dog-risk.util';
import {
  ExcludedDog,
  HarnessDog,
  HarnessLayout,
  HarnessRow,
  SuggestedTeam,
  TeamBuilderRequest,
  TeamBuilderResponse,
  TeamDogAssignment,
} from '../models/team-builder.model';
import { TeamBuilderService } from '../services/team-builder.service';

@Component({
  selector: 'app-team-builder-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, StatusBadgeComponent],
  templateUrl: './team-builder-page.component.html',
  styleUrl: './team-builder-page.component.scss',
})
export class TeamBuilderPageComponent {
  private readonly teamBuilderService = inject(TeamBuilderService);

  form: TeamBuilderRequest = {
    program_type: '10km',
    sled_type: 'T6',
    team_count: 2,
    min_dogs_per_team: 5,
    max_dogs_per_team: 6,
    avoid_high_risk: true,
    prefer_underused: true,
  };

  readonly programOptions = [
    { value: '3km', label: '3 km' },
    { value: '10km', label: '10 km' },
    { value: 'evening', label: 'Evening / special' },
  ];

  readonly sledOptions = [
    { value: 'T6', label: 'T6' },
    { value: 'T8', label: 'T8' },
    { value: 'big_sled', label: 'Big sled' },
  ];

  response: TeamBuilderResponse | null = null;

  isLoading = false;
  errorMessage = '';

  buildTeams(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.teamBuilderService.buildTeams(this.form).subscribe({
      next: (response) => {
        this.response = response;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to build teams', error);
        this.errorMessage = 'Failed to build team suggestions from API.';
        this.isLoading = false;
      },
    });
  }

  rowRoleLabel(role: string): string {
    if (role === 'lead') return 'Lead';
    if (role === 'team') return 'Center';
    if (role === 'wheel') return 'Wheel';
    return role;
  }

  rowRelationLabel(relation: string | null): string {
    switch (relation) {
      case 'forced_pair':
        return 'Forced pair';
      case 'home_pair':
        return 'Home pair';
      case 'preferred_pair':
        return 'Preferred pair';
      case 'allowed_pair':
        return 'Allowed pair';
      case 'single_lead':
        return 'Solo lead';
      case 'single_center':
        return 'Single center';
      case 'single_wheel':
        return 'Single wheel';
      case 'single_fallback':
        return 'Single fallback';
      case 'solo':
        return 'Solo';
      default:
        return '';
    }
  }

  rowRelationBadgeClass(relation: string | null): string {
    switch (relation) {
      case 'forced_pair':
        return 'badge-blue';
      case 'home_pair':
        return 'badge-green';
      case 'preferred_pair':
        return 'badge-purple';
      case 'allowed_pair':
        return 'badge-neutral';
      case 'single_lead':
      case 'single_center':
      case 'single_wheel':
      case 'single_fallback':
      case 'solo':
        return 'badge-neutral';
      default:
        return 'badge-neutral';
    }
  }

  flattenRows(layout: HarnessLayout): HarnessRow[] {
    return [...layout.lead_rows, ...layout.team_rows, ...layout.wheel_rows];
  }

  riskBadgeClass(value: string | null | undefined): string {
    return getRiskBadgeClass(value);
  }

  usageBadgeClass(value: string | null | undefined): string {
    return getUsageBadgeClass(value);
  }

  dogRoleLabel(dog: TeamDogAssignment): string {
    if (dog.assigned_role === 'lead') return 'Lead';
    if (dog.assigned_role === 'wheel') return 'Wheel';
    if (dog.assigned_role === 'team') return 'Team';
    if (dog.assigned_role === 'unassigned') return 'Unassigned';
    return dog.assigned_role;
  }

  humanizeWarning(value: string): string {
    return this.humanizeReason(value);
  }

  humanizeExcludedReason(value: string): string {
    return this.humanizeReason(value);
  }

  excludedReasonList(item: ExcludedDog): string[] {
    return item.reasons.map((reason) => this.humanizeReason(reason));
  }

  trackRow(index: number, row: HarnessRow): string {
    const ids = row.dogs.map((dog) => dog.dog_id).join('-');
    return `${row.row_role}-${row.row_type}-${ids}-${index}`;
  }

  trackHarnessDog(index: number, dog: HarnessDog): number {
    return dog.dog_id;
  }

  private humanizeReason(reason: string): string {
    if (!reason) return '—';

    if (reason.includes('=')) {
      return humanizeEligibilityReason(reason);
    }

    if (reason === 'manual_exclusion' || reason === 'too_young') {
      return humanizeEligibilityReason(reason);
    }

    if (reason === 'big_sled_only') {
      return 'This dog is reserved for big sled teams only.';
    }

    if (reason === 'risk_unavailable') {
      return 'Risk summary is unavailable for this dog.';
    }

    if (reason === 'high_risk_tomorrow') {
      return 'High risk for the selected plan.';
    }

    if (reason === 'Added as optional sixth dog.') {
      return reason;
    }

    return humanizeRiskFlag(reason);
  }
}