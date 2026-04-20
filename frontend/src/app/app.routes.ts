import { Routes } from '@angular/router';
import { AppShellComponent } from './core/layout/app-shell.component';

export const routes: Routes = [
  {
    path: '',
    component: AppShellComponent,
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard',
      },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/pages/dashboard-page.component').then(
            (m) => m.DashboardPageComponent
          ),
      },
      {
        path: 'dashboard/lists/:kind',
        loadComponent: () =>
          import('./features/dashboard/pages/dashboard-list-page.component').then(
            (m) => m.DashboardListPageComponent
          ),
      },
      {
        path: 'analytics',
        loadComponent: () =>
          import('./features/analytics/pages/analytics-page.component').then(
            (m) => m.AnalyticsPageComponent
          ),
      },
      {
        path: 'dogs',
        loadComponent: () =>
          import('./features/dogs/pages/dogs-page.component').then(
            (m) => m.DogsPageComponent
          ),
      },
      {
        path: 'dogs/archive',
        loadComponent: () =>
          import('./features/dogs/pages/dog-archive-page.component').then(
            (m) => m.DogArchivePageComponent
          ),
      },
      {
        path: 'dogs/new',
        loadComponent: () =>
          import('./features/dogs/pages/dog-create-page.component').then(
            (m) => m.DogCreatePageComponent
          ),
      },
      {
        path: 'dogs/:id/edit',
        loadComponent: () =>
          import('./features/dogs/pages/dog-edit-page.component').then(
            (m) => m.DogEditPageComponent
          ),
      },
      {
        path: 'dogs/:id',
        loadComponent: () =>
          import('./features/dogs/pages/dog-detail-page.component').then(
            (m) => m.DogDetailPageComponent
          ),
      },
      {
        path: 'daily-entry',
        loadComponent: () =>
          import('./features/daily-entry/pages/daily-entry-page.component').then(
            (m) => m.DailyEntryPageComponent
          ),
      },
      {
        path: 'team-builder',
        loadComponent: () =>
          import('./features/team-builder/pages/team-builder-page.component').then(
            (m) => m.TeamBuilderPageComponent
          ),
      },
    ],
  },
];