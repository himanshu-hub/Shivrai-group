
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class AdminProjectService {
  private http = inject(HttpClient);
  private apiUrl = 'http://127.0.0.1:8000/projects/';

  private getHeaders(): HttpHeaders {
    const token = sessionStorage.getItem('admin_token');

    return new HttpHeaders({
      Authorization: `Bearer ${token || ''}`
    });
  }

  createProject(project: unknown) {
    return this.http.post(this.apiUrl, project, {
      headers: this.getHeaders()
    });
  }

  updateProject(id: string, project: unknown) {
    return this.http.put(`${this.apiUrl}${id}`, project, {
      headers: this.getHeaders()
    });
  }

  deleteProject(id: string) {
    return this.http.delete(`${this.apiUrl}${id}`, {
      headers: this.getHeaders()
    });
  }
}
