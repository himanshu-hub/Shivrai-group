
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ContactService } from '../../services/contact';
import { ChangeDetectorRef } from '@angular/core';

@Component({
  selector: 'app-contact',
  imports: [FormsModule],
  templateUrl: './contact.html',
  styleUrl: './contact.scss',
})
export class Contact {
  private contactService = inject(ContactService);
  private cdr = inject(ChangeDetectorRef);

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

  submitForm() {
    if (this.loading) return;

    this.loading = true;
    this.success = '';
    this.error = '';
    

    this.contactService.submitContact(this.form).subscribe({
      next: () => {
        this.success = 'Enquiry submitted successfully!';
        this.loading = false;
        this.cdr.detectChanges();
        this.form = {
          name: '',
          email: '',
          phone: '',
          subject: '',
          message: ''
        };
      },
      error: () => {
        this.error = 'Unable to submit enquiry. Please check your details.';
        this.loading = false;
      }
    });
  }
}
