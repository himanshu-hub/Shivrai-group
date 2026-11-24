
import {
  Component,
  inject,
  OnInit,
  ChangeDetectorRef,
  PLATFORM_ID
} from '@angular/core';

import { isPlatformBrowser } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ProjectService, Project } from '../../services/project';

@Component({
  selector: 'app-project-details',
  imports: [RouterLink],
  templateUrl: './project-details.html',
  styleUrl: './project-details.scss'
})
export class ProjectDetails implements OnInit {

  private route = inject(ActivatedRoute);
  private projectService = inject(ProjectService);
  private cdr = inject(ChangeDetectorRef);
  private platformId = inject(PLATFORM_ID);

  project: Project | null = null;
  loading = true;
  error = '';

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');

    if (!id) {
      this.error = 'Invalid project ID';
      this.loading = false;
      return;
    }

    this.projectService.getProjectById(id).subscribe({
      next: (response) => {
        this.project = response;
        this.loading = false;
        this.cdr.detectChanges();

        // Record a view only after the project loads.
        // Browser-only execution prevents SSR from counting views.
        if (isPlatformBrowser(this.platformId)) {
          this.trackView(id);
        }
      },

      error: (err) => {
        console.error('Unable to load project:', err.status);

        this.error = 'Project not found or unavailable.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  private trackView(projectId: string) {
    this.projectService.trackProjectView(projectId).subscribe({
      next: () => {
        console.log('Project view recorded:', projectId);
      },

      error: (err) => {
        // Analytics errors must not affect project loading.
        console.warn(
          'Project view tracking failed:',
          err.status
        );
      }
    });
  }
}
