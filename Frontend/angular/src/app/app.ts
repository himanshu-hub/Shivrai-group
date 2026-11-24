
import {
  Component,
  inject,
  signal,
  PLATFORM_ID
} from '@angular/core';

import { isPlatformBrowser } from '@angular/common';

import {
  Router,
  RouterLink,
  RouterOutlet,
  RouterLinkActive
} from '@angular/router';

@Component({
  selector: 'app-root',
  imports: [RouterLink, RouterOutlet, RouterLinkActive],
  templateUrl: './app.html',
  styleUrl: './app.scss',
  host: {
    '[class.admin-dark]': "isAdminRoute() && theme() === 'dark'"
  }
})
export class App {
  private router = inject(Router);
  private platformId = inject(PLATFORM_ID);

  protected readonly title = signal('Shivrai Group');

  activeMenu = signal<string | null>(null);
  hoveredItem = signal<string | null>(null);

  theme = signal<'light' | 'dark'>('light');

  constructor() {
    if (isPlatformBrowser(this.platformId)) {
      const saved = localStorage.getItem('shivrai-admin-theme');

      if (saved === 'dark') {
        this.theme.set('dark');
      }
    }
  }

  isAdminRoute(): boolean {
    return this.router.url.startsWith('/admin/');
  }

  isAdminLoginRoute(): boolean {
    return this.router.url.startsWith('/admin/login');
  }

  toggleTheme() {
    const next = this.theme() === 'light' ? 'dark' : 'light';

    this.theme.set(next);

    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem('shivrai-admin-theme', next);
    }
  }

  openMenu(menu: string) {
    this.activeMenu.set(menu);
    this.hoveredItem.set(null);
  }

  closeMenu() {
    this.activeMenu.set(null);
    this.hoveredItem.set(null);
  }

  logout() {
    if (isPlatformBrowser(this.platformId)) {
      sessionStorage.removeItem('admin_token');
    }

    this.router.navigate(['/admin/login']);
  }
}
