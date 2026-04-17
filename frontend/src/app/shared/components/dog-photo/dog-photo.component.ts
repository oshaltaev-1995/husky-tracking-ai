import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import { getDogPhotoUrl } from '../../utils/dog-photo.util';

@Component({
  selector: 'app-dog-photo',
  standalone: true,
  imports: [CommonModule],
  template: `
    <img
      class="dog-photo"
      [src]="photoUrl"
      [alt]="altText"
      (error)="useFallback()"
    />
  `,
  styleUrls: ['./dog-photo.component.scss'],
})
export class DogPhotoComponent implements OnInit {
  @Input() dogName: string | null | undefined;
  @Input() altText = 'Dog photo';

  photoUrl = '/dog-photos/fallback.png';

  ngOnInit(): void {
    this.photoUrl = getDogPhotoUrl(this.dogName);
  }

  useFallback(): void {
    this.photoUrl = '/dog-photos/fallback.png';
  }
}