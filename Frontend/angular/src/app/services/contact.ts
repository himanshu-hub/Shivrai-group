
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export interface Contact {
  name: string;
  email: string;
  phone: string;
  subject?: string;
  message: string;
}

export interface ContactResponse {
  message: string;
  id: string;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class ContactService {
  private http = inject(HttpClient);

  private apiUrl = 'http://127.0.0.1:8000/contact/';

  submitContact(data: Contact) {
    return this.http.post<ContactResponse>(this.apiUrl, data);
  }
}
