
import { Component, signal } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  imports: [RouterLink, RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})

export class App {
  protected readonly title = signal('Shivrai Group');

  activeMenu = signal<string | null>(null);
  hoveredItem = signal<string | null>(null);

  openMenu(menu: string) {
    this.activeMenu.set(menu);
    this.hoveredItem.set(null);
  }

  closeMenu() {
    this.activeMenu.set(null);
    this.hoveredItem.set(null);
  }
}

