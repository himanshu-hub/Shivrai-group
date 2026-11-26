
import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
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
  private platformId = inject(PLATFORM_ID);

  private apiUrl = 'http://127.0.0.1:8000/auth/login';
  private tokenKey = 'admin_token';

  private get isBrowser(): boolean {
    return isPlatformBrowser(this.platformId);
  }

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
        if (this.isBrowser) {
          sessionStorage.setItem(
            this.tokenKey,
            response.access_token
          );
        }
      })
    );
  }

  getToken(): string | null {
    if (!this.isBrowser) {
      return null;
    }

    const token = sessionStorage.getItem(this.tokenKey);

    if (!token) {
      return null;
    }

    try {
      const payloadPart = token.split('.')[1];

      if (!payloadPart) {
        this.logout();
        return null;
      }

      const base64 = payloadPart
        .replace(/-/g, '+')
        .replace(/_/g, '/');

      const payload = JSON.parse(atob(base64));

      if (
        typeof payload.exp !== 'number' ||
        payload.exp * 1000 <= Date.now()
      ) {
        this.logout();
        return null;
      }

      return token;

    } catch {
      this.logout();
      return null;
    }
  }

  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  logout(): void {
    if (this.isBrowser) {
      sessionStorage.removeItem(this.tokenKey);
    }
  }
}
