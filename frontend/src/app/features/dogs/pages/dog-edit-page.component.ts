import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { DogCreatePayload } from '../models/dog-create.model';
import { Dog } from '../models/dog.model';
import { DogsService } from '../services/dogs.service';

@Component({
  selector: 'app-dog-edit-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './dog-edit-page.component.html',
  styleUrl: './dog-edit-page.component.scss',
})
export class DogEditPageComponent implements OnInit {
  private readonly dogsService = inject(DogsService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  dogId = 0;
  dog: Dog | null = null;

  isLoading = false;
  isSaving = false;
  errorMessage = '';

  form: Partial<DogCreatePayload> = {
    name: '',
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
  };

  readonly kennelRowOptions = ['A', 'B-1', 'B-2', 'C-1', 'C-2', 'D-1', 'D-2', 'E', 'YKSIOT'];
  readonly sexOptions = ['M', 'F'];
  readonly roleOptions = ['lead', 'team', 'wheel', 'none'];

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    this.dogId = Number(idParam);

    if (!this.dogId || Number.isNaN(this.dogId)) {
      this.errorMessage = 'Invalid dog id.';
      return;
    }

    this.loadDog();
  }

  loadDog(): void {
    this.isLoading = true;
    this.errorMessage = '';

    this.dogsService.getDogById(this.dogId).subscribe({
      next: (dog) => {
        this.dog = dog;
        this.form = {
          name: dog.name,
          birth_year: dog.birth_year,
          sex: dog.sex,
          kennel_row: dog.kennel_row,
          kennel_block: dog.kennel_block,
          home_slot: dog.home_slot,
          primary_role: dog.primary_role,
          can_lead: dog.can_lead,
          can_team: dog.can_team,
          can_wheel: dog.can_wheel,
          status: dog.status,
          notes: dog.notes,
          is_active: dog.is_active,
        };
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Failed to load dog for editing', error);
        this.errorMessage = 'Failed to load dog.';
        this.isLoading = false;
      },
    });
  }

  saveDog(): void {
    this.errorMessage = '';

    if (!this.form.name?.trim()) {
      this.errorMessage = 'Name is required.';
      return;
    }

    this.isSaving = true;

    const payload: Partial<DogCreatePayload> = {
      name: this.form.name.trim(),
      birth_year: this.numberOrNull(this.form.birth_year),
      sex: this.emptyToNull(this.form.sex),
      kennel_row: this.emptyToNull(this.form.kennel_row),
      kennel_block: this.numberOrNull(this.form.kennel_block),
      home_slot: this.numberOrNull(this.form.home_slot),
      primary_role: this.emptyToNull(this.form.primary_role),
      can_lead: Boolean(this.form.can_lead),
      can_team: Boolean(this.form.can_team),
      can_wheel: Boolean(this.form.can_wheel),
      status: this.emptyToNull(this.form.status),
      notes: this.emptyToNull(this.form.notes),
      is_active: this.form.is_active ?? true,
    };

    this.dogsService.updateDog(this.dogId, payload).subscribe({
      next: (dog) => {
        this.isSaving = false;
        this.router.navigate(['/dogs', dog.id]);
      },
      error: (error) => {
        console.error('Failed to update dog', error);
        this.errorMessage = 'Failed to update dog.';
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