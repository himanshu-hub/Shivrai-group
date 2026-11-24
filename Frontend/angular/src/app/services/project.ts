
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface Project {
  id: string;
  name: string;
  status: string;
  category?: string;
  location: string;
  description: string;

  // Main project cover image
  image?: string | null;

  // Additional project gallery images
  gallery?: string[];

  // Visitor analytics
  total_views?: number;
}

export interface ProjectResponse {
  total_projects: number;
  current_page: number;
  total_pages: number;
  projects: Project[];
}

@Injectable({
  providedIn: 'root'
})
export class ProjectService {

  private http = inject(HttpClient);

  private apiUrl = 'http://127.0.0.1:8000/projects/';

  // GET ALL PROJECTS WITH FILTERS AND PAGINATION

  getProjects(
    status?: string,
    category?: string,
    search?: string,
    page: number = 1,
    limit: number = 10
  ) {
    const params: Record<string, string | number> = {
      page,
      limit
    };

    if (status) {
      params['status'] = status;
    }

    if (category) {
      params['category'] = category;
    }

    if (search?.trim()) {
      params['search'] = search.trim();
    }

    return this.http.get<ProjectResponse>(
      this.apiUrl,
      { params }
    );
  }

  // GET SINGLE PROJECT DETAILS AND GALLERY

  getProjectById(id: string) {
    return this.http.get<Project>(
      `${this.apiUrl}${id}`
    );
  }

  // GET MOST VIEWED PROJECTS

  getMostViewedProjects(limit = 5) {
    return this.http.get<ProjectResponse>(
      this.apiUrl,
      {
        params: {
          page: 1,
          limit,
          sort_by: 'most_viewed'
        }
      }
    );
  }

  // RECORD PROJECT PAGE VIEW

  trackProjectView(id: string) {
    return this.http.post<void>(
      `${this.apiUrl}${id}/view`,
      null
    );
  }
}
