import { Component, inject, ChangeDetectorRef, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { of, switchMap, finalize, throwError } from 'rxjs';
import { ProjectService, Project } from '../../services/project';
import { AdminProjectService } from '../../services/admin-project';
import { AdminMediaService, MediaImage } from '../../services/admin-media';

interface ProjectForm {
  name: string;
  status: string;
  category: string;
  location: string;
  description: string;
  image: string;
}

@Component({
  selector: 'app-admin-projects',
  imports: [FormsModule],
  templateUrl: './admin-projects.html',
  styleUrl: './admin-projects.scss'
})
export class AdminProjects implements OnInit {
  private projectService = inject(ProjectService);
  private adminService = inject(AdminProjectService);
  private mediaService = inject(AdminMediaService);
  private cdr = inject(ChangeDetectorRef);

  projects: Project[] = [];
  loading = false;
  saving = false;
  error = '';
  message = '';

  editingId: string | null = null;
  showEditModal = false;
  form: ProjectForm = this.emptyForm();

  searchQuery = '';
  filterStatus = '';
  filterCategory = '';

  // A selected media ID is applied through /images/.../cover/select after
  // the project is saved. This preserves the Media Library association.
  selectedCover: MediaImage | null = null;
  showMediaPicker = false;
  mediaImages: MediaImage[] = [];
  mediaSearch = '';
  mediaPage = 1;
  mediaTotalPages = 1;
  mediaLoading = false;
  mediaError = '';

  ngOnInit(): void {
    this.loadProjects();
  }

  emptyForm(): ProjectForm {
    return {
      name: '',
      status: 'Ongoing',
      category: 'Residential',
      location: '',
      description: '',
      image: ''
    };
  }

  loadProjects(): void {
    this.loading = true;
    this.projectService.getProjects(
      undefined, undefined, undefined, 1, 100
    ).subscribe({
      next: response => {
        this.projects = response.projects;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'Failed to load projects.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  openMediaPicker(): void {
    this.mediaError = '';
    this.mediaSearch = '';
    this.mediaPage = 1;
    this.showMediaPicker = true;
    this.loadMediaPicker();
  }

  closeMediaPicker(): void {
    this.showMediaPicker = false;
  }

  loadMediaPicker(): void {
    if (this.mediaLoading) return;
    this.mediaLoading = true;
    this.mediaError = '';

    this.mediaService.getImages({
      page: this.mediaPage,
      limit: 24,
      search: this.mediaSearch,
      usage: 'all',
      sort_by: 'newest'
    }).pipe(finalize(() => {
      this.mediaLoading = false;
      this.cdr.detectChanges();
    })).subscribe({
      next: result => {
        this.mediaImages = result.images;
        this.mediaTotalPages = Math.max(1, result.total_pages);
        this.cdr.detectChanges();
      },
      error: () => {
        this.mediaError = 'Unable to load Media Library images.';
      }
    });
  }

  searchMedia(): void {
    this.mediaPage = 1;
    this.loadMediaPicker();
  }

  changeMediaPage(direction: -1 | 1): void {
    const next = this.mediaPage + direction;
    if (next < 1 || next > this.mediaTotalPages || this.mediaLoading) return;
    this.mediaPage = next;
    this.loadMediaPicker();
  }

  chooseCover(image: MediaImage): void {
    this.selectedCover = image;
    this.showMediaPicker = false;
    this.mediaError = '';
  }

  clearSelectedCover(): void {
    this.selectedCover = null;
  }

  get coverPreviewUrl(): string {
    return this.selectedCover?.image_url ||
      (this.form.image?.startsWith('http') ? this.form.image : '');
  }

  saveProject(): void {
    if (this.saving) return;

    this.saving = true;
    this.error = '';
    this.message = '';

    const currentEditingId = this.editingId;
    const isEditing = currentEditingId !== null;
    const selectedMediaId = this.selectedCover?.id;
    let projectSaved = false;

    const request = currentEditingId
      ? this.adminService.updateProject(currentEditingId, this.form)
      : this.adminService.createProject(this.form);

    request.pipe(
      switchMap(response => {
        projectSaved = true;
        if (!selectedMediaId) return of(null);

        // New-project API responses must contain the new MongoDB project ID.
        const data = response as { id?: string; project_id?: string; project?: { id?: string } } | null;
        const projectId = currentEditingId || data?.id || data?.project_id || data?.project?.id;
        if (!projectId) {
          return throwError(() => new Error('Project saved, but the API did not return its ID.'));
        }
        return this.mediaService.selectCover(projectId, selectedMediaId);
      }),
      finalize(() => {
        this.saving = false;
        this.cdr.detectChanges();
      })
    ).subscribe({
      next: () => {
        this.cancelEdit();
        this.message = isEditing
          ? 'Project updated successfully.'
          : 'Project created successfully.';
        this.loadProjects();
      },
      error: err => {
        if (projectSaved) {
          this.error = 'Project details were saved, but the cover could not be assigned. Open the project again and retry the cover selection.';
          this.loadProjects();
        } else {
          this.error = err?.status === 401
            ? 'Session expired or unauthorized. Please log in again.'
            : 'Failed to save project.';
        }
        this.cdr.detectChanges();
      }
    });
  }

  editProject(project: Project): void {
    this.error = '';
    this.message = '';
    this.editingId = project.id;
    this.selectedCover = null;
    this.form = {
      name: project.name,
      status: project.status,
      category: project.category || 'Residential',
      location: project.location,
      description: project.description,
      image: project.image || ''
    };
    this.showEditModal = true;
    this.cdr.detectChanges();
  }

  deleteProject(project: Project): void {
    if (!confirm(`Delete "${project.name}"? Its Media Library images will be preserved.`)) return;
    this.error = '';
    this.message = '';
    this.adminService.deleteProject(project.id).subscribe({
      next: () => {
        this.message = 'Project deleted successfully.';
        this.loadProjects();
      },
      error: err => {
        this.error = err.status === 401
          ? 'Session expired or unauthorized. Please log in again.'
          : 'Failed to delete project.';
        this.cdr.detectChanges();
      }
    });
  }

  cancelEdit(): void {
    this.editingId = null;
    this.showEditModal = false;
    this.showMediaPicker = false;
    this.selectedCover = null;
    this.form = this.emptyForm();
    this.cdr.detectChanges();
  }

  get filteredProjects(): Project[] {
    const search = this.searchQuery.trim().toLowerCase();
    return this.projects.filter(project => {
      const matchesSearch = !search ||
        project.name.toLowerCase().includes(search) ||
        project.location.toLowerCase().includes(search);
      const matchesStatus = !this.filterStatus ||
        project.status.toLowerCase() === this.filterStatus.toLowerCase();
      const matchesCategory = !this.filterCategory ||
        (project.category || '').toLowerCase() === this.filterCategory.toLowerCase();
      return matchesSearch && matchesStatus && matchesCategory;
    });
  }

  clearFilters(): void {
    this.searchQuery = '';
    this.filterStatus = '';
    this.filterCategory = '';
  }
}
