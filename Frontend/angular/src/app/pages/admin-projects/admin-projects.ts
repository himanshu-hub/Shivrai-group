
import { Component, inject, ChangeDetectorRef, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ProjectService, Project } from '../../services/project';
import { AdminProjectService } from '../../services/admin-project';

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
  private cdr = inject(ChangeDetectorRef);

  projects: Project[] = [];
  loading = false;
  saving = false;
  error = '';
  message = '';

  editingId: string | null = null;
  showEditModal = false;

  form: ProjectForm = this.emptyForm();

  ngOnInit() {
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

  loadProjects() {
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

  saveProject() {
    if (this.saving) return;

    this.saving = true;
    this.error = '';
    this.message = '';

    const isEditing = this.editingId !== null;

    const request = this.editingId
      ? this.adminService.updateProject(this.editingId, this.form)
      : this.adminService.createProject(this.form);

    request.subscribe({
      next: () => {
        this.message = isEditing
          ? 'Project updated successfully.'
          : 'Project created successfully.';

        this.cancelEdit();
        this.saving = false;
        this.loadProjects();
      },
      error: (err) => {
        this.error = err.status === 401
          ? 'Session expired or unauthorized. Please log in again.'
          : 'Failed to save project.';

        this.saving = false;
        this.cdr.detectChanges();
      }
    });
  }

  editProject(project: Project) {
    this.error = '';
    this.message = '';

    this.editingId = project.id;

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

  deleteProject(project: Project) {
    if (!confirm(`Delete "${project.name}"?`)) return;

    this.error = '';
    this.message = '';

    this.adminService.deleteProject(project.id).subscribe({
      next: () => {
        this.message = 'Project deleted successfully.';
        this.loadProjects();
      },
      error: (err) => {
        this.error = err.status === 401
          ? 'Session expired or unauthorized. Please log in again.'
          : 'Failed to delete project.';

        this.cdr.detectChanges();
      }
    });
  }

  cancelEdit() {
    this.editingId = null;
    this.showEditModal = false;
    this.form = this.emptyForm();
    this.cdr.detectChanges();
  }

  searchQuery = '';
  filterStatus = '';
  filterCategory = '';

  get filteredProjects(): Project[] {
    const search = this.searchQuery.trim().toLowerCase();

    return this.projects.filter(project => {
      const matchesSearch =
        !search ||
        project.name.toLowerCase().includes(search) ||
        project.location.toLowerCase().includes(search);

      const matchesStatus =
        !this.filterStatus ||
        project.status.toLowerCase() === this.filterStatus.toLowerCase();

      const matchesCategory =
        !this.filterCategory ||
        (project.category || '').toLowerCase() ===
          this.filterCategory.toLowerCase();

      return matchesSearch && matchesStatus && matchesCategory;
    });
  }

  clearFilters() {
    this.searchQuery = '';
    this.filterStatus = '';
    this.filterCategory = '';
  }

}
