import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { DogCreatePayload } from '../models/dog-create.model';
import { DogsService } from '../services/dogs.service';

@Component({
  selector: 'app-dog-create-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './dog-create-page.component.html',
  styleUrl: './dog-create-page.component.scss',
})
export class DogCreatePageComponent {
  private readonly dogsService = inject(DogsService);
  private readonly router = inject(Router);

  isSaving = false;
  errorMessage = '';

  form: DogCreatePayload = {
    name: '',
    external_id: null,
    birth_year: null,
    sex: null,
    kennel_row: null,
    kennel_block: null,
    home_slot: null,
    primary_role: 'team',
    can_lead: false,
    can_team: true,
    can_wheel: false,
    status: 'active',
    notes: null,
    is_active: true,
    lifecycle_status: 'active',
    availability_status: 'available',
    exclude_from_team_builder: false,
    exclude_reason: null,
  };

  readonly kennelRowOptions = ['A', 'B-1', 'B-2', 'C-1', 'C-2', 'D-1', 'D-2', 'E', 'YKSIOT'];
  readonly sexOptions = ['M', 'F'];
  readonly roleOptions = ['lead', 'team', 'wheel', 'none'];
  readonly lifecycleOptions = ['active', 'retired', 'deceased', 'archived'];
  readonly availabilityOptions = ['available', 'rest', 'restricted', 'injured', 'sick', 'treatment'];

  saveDog(): void {
    this.errorMessage = '';

    if (!this.form.name.trim()) {
      this.errorMessage = 'Name is required.';
      return;
    }

    this.isSaving = true;

    const payload: DogCreatePayload = {
      ...this.form,
      name: this.form.name.trim(),
      sex: this.emptyToNull(this.form.sex),
      kennel_row: this.emptyToNull(this.form.kennel_row),
      primary_role: this.emptyToNull(this.form.primary_role),
      status: this.emptyToNull(this.form.status),
      notes: this.emptyToNull(this.form.notes),
      exclude_reason: this.emptyToNull(this.form.exclude_reason),
      external_id: null,
      birth_year: this.numberOrNull(this.form.birth_year),
      kennel_block: this.numberOrNull(this.form.kennel_block),
      home_slot: this.numberOrNull(this.form.home_slot),
    };

    this.dogsService.createDog(payload).subscribe({
      next: (dog) => {
        this.isSaving = false;
        this.router.navigate(['/dogs', dog.id]);
      },
      error: (error) => {
        console.error('Failed to create dog', error);
        this.errorMessage = 'Failed to create dog.';
        this.isSaving = false;
      },
    });
  }

  private emptyToNull(value: string | null | undefined): string | null {
    if (value === null || value === undefined) return null;
    const trimmed = value.trim();
    return trimmed ? trimmed : null;
  }

  private numberOrNull(value: number | null | undefined): number | null {
    if (value === null || value === undefined || value === ('' as unknown as number)) {
      return null;
    }

    const num = Number(value);
    return Number.isFinite(num) ? num : null;
  }
}