
import {
  Component,
  inject,
  ChangeDetectorRef,
  OnDestroy
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ContactService } from '../../services/contact';
import { Subscription, timer } from 'rxjs';

@Component({
  selector: 'app-contact',
  imports: [FormsModule],
  templateUrl: './contact.html',
  styleUrl: './contact.scss'
})
export class Contact implements OnDestroy {
  private contactService = inject(ContactService);
  private cdr = inject(ChangeDetectorRef);
  private router = inject(Router);

  private redirectSubscription?: Subscription;

  form = {
    name: '',
    email: '',
    phone: '',
    subject: '',
    message: ''
  };

  loading = false;
  success = '';
  error = '';
  redirecting = false;

  submitForm(): void {
    if (this.loading || this.redirecting) return;

    this.loading = true;
    this.success = '';
    this.error = '';

    this.contactService.submitContact(this.form).subscribe({
      next: () => {
        this.loading = false;
        this.redirecting = true;

        this.success =
          'Enquiry submitted successfully! Redirecting to Home in 3 seconds...';

        this.form = {
          name: '',
          email: '',
          phone: '',
          subject: '',
          message: ''
        };

        this.cdr.detectChanges();

        this.redirectSubscription = timer(3000).subscribe(() => {
          void this.router.navigate(['/']);
        });
      },

      error: () => {
        this.error =
          'Unable to submit enquiry. Please check your details.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  ngOnDestroy(): void {
    this.redirectSubscription?.unsubscribe();
  }
}
