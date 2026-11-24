
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { tap } from 'rxjs';

interface LoginResponse {
  access_token: string;
  token_type: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private apiUrl = 'http://127.0.0.1:8000/auth/login';

  login(username: string, password: string) {
    const body = new HttpParams()
      .set('username', username)
      .set('password', password);

    return this.http.post<LoginResponse>(
      this.apiUrl,
      body.toString(),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    ).pipe(
      tap(response => {
        sessionStorage.setItem(
          'admin_token',
          response.access_token
        );
      })
    );
  }

  getToken(): string | null {
    return sessionStorage.getItem('admin_token');
  }

  logout() {
    sessionStorage.removeItem('admin_token');
  }
}
