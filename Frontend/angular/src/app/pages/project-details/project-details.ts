
import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ProjectService, Project } from '../../services/project';

@Component({
  selector: 'app-project-details',
  imports: [RouterLink],
  templateUrl: './project-details.html',
  styleUrl: './project-details.scss',
})
export class ProjectDetails implements OnInit {
  private route = inject(ActivatedRoute);
  private projectService = inject(ProjectService);
  private cdr = inject(ChangeDetectorRef);

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
      },
      error: () => {
        this.error = 'Project not found or unavailable.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }
}
