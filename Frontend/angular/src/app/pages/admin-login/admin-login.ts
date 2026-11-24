
import { Component, inject, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-admin-login',
  imports: [FormsModule],
  templateUrl: './admin-login.html',
  styleUrl: './admin-login.scss'
})
export class AdminLogin {
  private auth = inject(AuthService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);

  username = '';
  password = '';
  loading = false;
  error = '';

  login() {
    if (!this.username.trim() || !this.password) {
      this.error = 'Enter your username and password.';
      return;
    }

    this.loading = true;
    this.error = '';

    this.auth.login(this.username, this.password).subscribe({
      next: (response) => {
        sessionStorage.setItem('admin_token', response.access_token);

        this.loading = false;
        this.cdr.detectChanges();

        this.router.navigate(['/admin/dashboard']);
      },
      error: () => {
        this.error = 'Invalid credentials or login unavailable.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }
}
