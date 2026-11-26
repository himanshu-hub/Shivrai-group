
import {
  Component,
  inject,
  OnInit,
  ChangeDetectorRef,
  PLATFORM_ID,
  ElementRef,
  viewChild
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

  // Gallery slider reference
  readonly galleryTrack =
    viewChild<ElementRef<HTMLElement>>('galleryTrack');

  project: Project | null = null;
  loading = true;
  error = '';

  ngOnInit(): void {
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

        // Record views only in the browser
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

  // Gallery navigation
  scrollGallery(direction: number): void {
    if (!isPlatformBrowser(this.platformId)) return;

    const track = this.galleryTrack()?.nativeElement;

    if (!track) return;

    const slide = track.querySelector<HTMLElement>(
      '.gallery-slide'
    );

    if (!slide) return;

    const gap =
      parseFloat(getComputedStyle(track).columnGap) || 18;

    const distance = slide.offsetWidth + gap;

    track.scrollBy({
      left: direction * distance,
      behavior: 'smooth'
    });
  }

  private trackView(projectId: string): void {
    this.projectService.trackProjectView(projectId).subscribe({
      next: () => {
        console.log('Project view recorded:', projectId);
      },

      error: (err) => {
        // Analytics failures must not affect the page
        console.warn(
          'Project view tracking failed:',
          err.status
        );
      }
    });
  }
}
