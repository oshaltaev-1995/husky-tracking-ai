import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="layout">
      <aside class="sidebar">
        <div class="brand">
          <h1>Husky Tracking AI</h1>
          <p>Frontend MVP</p>
        </div>

        <nav class="nav">
          <a routerLink="/dashboard" routerLinkActive="active">Dashboard</a>
          <a routerLink="/dogs" routerLinkActive="active">Dogs</a>
          <a routerLink="/daily-entry" routerLinkActive="active">Daily Entry</a>
          <a routerLink="/team-builder" routerLinkActive="active">Team Builder</a>
        </nav>
      </aside>

      <main class="content">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
  styleUrls: ['./app-shell.component.scss'],
})
export class AppShellComponent {}