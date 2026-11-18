
import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ProjectService, Project } from '../../services/project';

@Component({
  selector: 'app-projects',
  imports: [FormsModule, RouterLink],
  templateUrl: './projects.html',
  styleUrl: './projects.scss',
})
export class Projects implements OnInit {
  private projectService = inject(ProjectService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);

  projects: Project[] = [];
  loading = true;
  error = '';

  selectedStatus = '';
  selectedCategory = '';
  search = '';
  searchInput = '';

  currentPage = 1;
  totalPages = 0;
  totalProjects = 0;
  limit = 5;

  ngOnInit() {
    this.route.queryParamMap.subscribe(params => {
      this.selectedStatus = params.get('status') || '';
      this.selectedCategory = params.get('category') || '';
      this.search = params.get('search') || '';
      this.searchInput = this.search;

      const page = Number(params.get('page') || 1);
      this.currentPage = Number.isInteger(page) && page > 0 ? page : 1;

      this.loadProjects();
    });
  }

  loadProjects() {
    this.loading = true;
    this.error = '';
    this.cdr.detectChanges();

    this.projectService.getProjects(
      this.selectedStatus || undefined,
      this.selectedCategory || undefined,
      this.search || undefined,
      this.currentPage,
      this.limit
    ).subscribe({
      next: response => {
        this.projects = response.projects;
        this.currentPage = response.current_page;
        this.totalPages = response.total_pages;
        this.totalProjects = response.total_projects;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Unable to load projects.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  submitSearch() {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        search: this.searchInput.trim() || null,
        page: 1
      },
      queryParamsHandling: 'merge'
    });
  }

  changePage(page: number) {
    if (page < 1 || page > this.totalPages || this.loading) return;

    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { page },
      queryParamsHandling: 'merge'
    });
  }
}
