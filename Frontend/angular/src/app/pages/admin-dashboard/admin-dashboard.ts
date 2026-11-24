
import {
  Component,
  inject,
  OnInit,
  ChangeDetectorRef,
  PLATFORM_ID
} from '@angular/core';

import { isPlatformBrowser, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

import {
  ProjectService,
  Project
} from '../../services/project';

import {
  AdminEnquiryService,
  Enquiry
} from '../../services/admin-enquiry';

@Component({
  selector: 'app-admin-dashboard',
  imports: [RouterLink, DatePipe],
  templateUrl: './admin-dashboard.html',
  styleUrl: './admin-dashboard.scss'
})
export class AdminDashboard implements OnInit {

  private projectService = inject(ProjectService);
  private enquiryService = inject(AdminEnquiryService);
  private cdr = inject(ChangeDetectorRef);
  private platformId = inject(PLATFORM_ID);

  // DASHBOARD STATE

  loading = true;
  error = '';

  // PROJECT STATISTICS

  totalProjects: number | null = null;
  ongoingProjects: number | null = null;
  upcomingProjects: number | null = null;
  completedProjects: number | null = null;

  // PROJECT VISITOR ANALYTICS

  mostViewedProjects: Project[] = [];

  // ENQUIRY STATISTICS

  totalEnquiries: number | null = null;
  pendingEnquiries: number | null = null;

  recentEnquiries: Enquiry[] = [];

  ngOnInit() {
    if (isPlatformBrowser(this.platformId)) {
      this.loadDashboard();
    }
  }

  // EXTRACT TOTAL PROJECT COUNT

  private getProjectCount(response: unknown): number | null {
    if (!response || typeof response !== 'object') {
      return null;
    }

    const data = response as Record<string, unknown>;
    const count = data['total_projects'] ?? data['total'];

    return typeof count === 'number' ? count : null;
  }

  // LOAD ALL DASHBOARD DATA

  loadDashboard() {
    this.loading = true;
    this.error = '';

    const safeProjects = (status?: string) =>
      this.projectService
        .getProjects(status, undefined, undefined, 1, 1)
        .pipe(
          catchError(() => of(null))
        );

    forkJoin({

      // PROJECT COUNTS

      all: safeProjects(),

      ongoing: safeProjects('Ongoing'),

      upcoming: safeProjects('Upcoming'),

      completed: safeProjects('Completed'),

      // MOST VIEWED PROJECTS

      mostViewed: this.projectService
        .getMostViewedProjects(5)
        .pipe(
          catchError(() => of(null))
        ),

      // CUSTOMER ENQUIRIES

      enquiries: this.enquiryService
        .getEnquiries(1, 5)
        .pipe(
          catchError(() => of(null))
        ),

      pending: this.enquiryService
        .getEnquiries(1, 1, '', 'Pending')
        .pipe(
          catchError(() => of(null))
        )

    }).subscribe({

      next: (results) => {

        // PROJECT STATISTICS

        this.totalProjects =
          this.getProjectCount(results.all);

        this.ongoingProjects =
          this.getProjectCount(results.ongoing);

        this.upcomingProjects =
          this.getProjectCount(results.upcoming);

        this.completedProjects =
          this.getProjectCount(results.completed);

        // MOST VIEWED PROJECTS

        this.mostViewedProjects =
          results.mostViewed?.projects ?? [];

        // ENQUIRY STATISTICS

        this.totalEnquiries =
          results.enquiries?.total_enquiries ?? null;

        this.pendingEnquiries =
          results.pending?.total_enquiries ?? null;

        this.recentEnquiries =
          results.enquiries?.enquiries ?? [];

        // CHECK FOR MISSING DATA

        const missingData = [
          this.totalProjects,
          this.ongoingProjects,
          this.upcomingProjects,
          this.completedProjects,
          this.totalEnquiries,
          this.pendingEnquiries
        ].some(value => value === null);

        if (missingData || results.mostViewed === null) {
          this.error =
            'Some dashboard statistics could not be loaded.';
        }

        this.loading = false;
        this.cdr.detectChanges();
      },

      error: () => {
        this.error = 'Unable to load dashboard.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }
}
