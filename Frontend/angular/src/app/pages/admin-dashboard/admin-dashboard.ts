
import {
  Component,
  inject,
  OnInit,
  ChangeDetectorRef,
  PLATFORM_ID
} from '@angular/core';

import { isPlatformBrowser, DatePipe } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
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

import { AuthService } from '../../services/auth';


// =============================================
// DASHBOARD API RESPONSE TYPES
// =============================================

interface ProjectDashboardStats {
  total: number;
  ongoing: number;
  completed: number;
  upcoming: number;
  total_views: number;
}

interface EnquiryDashboardStats {
  total: number;
  pending: number;
  contacted: number;
  resolved: number;
}

interface MediaDashboardStats {
  total_images: number;
}

interface DashboardResponse {
  projects: ProjectDashboardStats;
  enquiries: EnquiryDashboardStats;
  media: MediaDashboardStats;
  recent_enquiries: {
    id: string;
    name: string;
    email: string;
    subject: string | null;
    status: string;
    created_at: string | null;
  }[];
}


// =============================================
// ADMIN DASHBOARD COMPONENT
// =============================================

@Component({
  selector: 'app-admin-dashboard',
  imports: [RouterLink, DatePipe],
  templateUrl: './admin-dashboard.html',
  styleUrl: './admin-dashboard.scss'
})
export class AdminDashboard implements OnInit {

  private http = inject(HttpClient);
  private auth = inject(AuthService);

  private projectService = inject(ProjectService);
  private enquiryService = inject(AdminEnquiryService);

  private cdr = inject(ChangeDetectorRef);
  private platformId = inject(PLATFORM_ID);

  private dashboardUrl =
    'http://127.0.0.1:8000/auth/dashboard';


  // =============================================
  // GENERAL STATE
  // =============================================

  loading = true;
  error = '';


  // =============================================
  // PROJECT STATISTICS
  // =============================================

  totalProjects: number | null = null;
  ongoingProjects: number | null = null;
  upcomingProjects: number | null = null;
  completedProjects: number | null = null;

  totalViews = 0;


  // =============================================
  // PROJECT ANALYTICS
  // =============================================

  mostViewedProjects: Project[] = [];


  // =============================================
  // ENQUIRY STATISTICS
  // =============================================

  totalEnquiries: number | null = null;
  pendingEnquiries: number | null = null;

  contactedEnquiries = 0;
  resolvedEnquiries = 0;

  recentEnquiries: Enquiry[] = [];


  // =============================================
  // MEDIA STATISTICS
  // =============================================

  totalImages = 0;


  // =============================================
  // COMPONENT INITIALIZATION
  // =============================================

  ngOnInit(): void {
    if (isPlatformBrowser(this.platformId)) {
      this.loadDashboard();
    }
  }


  // =============================================
  // LOAD DASHBOARD
  // =============================================

  loadDashboard(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    this.loading = true;
    this.error = '';

    const token = this.auth.getToken();

    if (!token) {
      this.loading = false;
      this.error = 'Admin session expired. Please log in again.';
      this.cdr.detectChanges();
      return;
    }

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`
    });

    forkJoin({

      // Main admin dashboard summary
      dashboard: this.http.get<DashboardResponse>(
        this.dashboardUrl,
        { headers }
      ).pipe(
        catchError(() => of(null))
      ),

      // Preserve existing most-viewed projects display
      mostViewed: this.projectService
        .getMostViewedProjects(5)
        .pipe(
          catchError(() => of(null))
        ),

      // Preserve existing full enquiry records
      // expected by the dashboard HTML
      enquiries: this.enquiryService
        .getEnquiries(1, 5)
        .pipe(
          catchError(() => of(null))
        )

    }).subscribe({

      next: (results) => {

        const dashboard = results.dashboard;

        // =============================================
        // PROJECT COUNTS
        // =============================================

        if (dashboard) {
          this.totalProjects = dashboard.projects.total;

          this.ongoingProjects =
            dashboard.projects.ongoing;

          this.upcomingProjects =
            dashboard.projects.upcoming;

          this.completedProjects =
            dashboard.projects.completed;

          this.totalViews =
            dashboard.projects.total_views;

          // =============================================
          // ENQUIRY COUNTS
          // =============================================

          this.totalEnquiries =
            dashboard.enquiries.total;

          this.pendingEnquiries =
            dashboard.enquiries.pending;

          this.contactedEnquiries =
            dashboard.enquiries.contacted;

          this.resolvedEnquiries =
            dashboard.enquiries.resolved;

          // =============================================
          // MEDIA LIBRARY
          // =============================================

          this.totalImages =
            dashboard.media.total_images;

        } else {
          this.totalProjects = null;
          this.ongoingProjects = null;
          this.upcomingProjects = null;
          this.completedProjects = null;

          this.totalEnquiries = null;
          this.pendingEnquiries = null;

          this.totalViews = 0;
          this.totalImages = 0;
          this.contactedEnquiries = 0;
          this.resolvedEnquiries = 0;
        }

        // =============================================
        // MOST VIEWED PROJECTS
        // =============================================

        this.mostViewedProjects =
          results.mostViewed?.projects ?? [];

        // =============================================
        // RECENT ENQUIRIES
        // =============================================

        this.recentEnquiries =
          results.enquiries?.enquiries ?? [];

        // =============================================
        // ERROR HANDLING
        // =============================================

        if (
          !dashboard ||
          !results.mostViewed ||
          !results.enquiries
        ) {
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
