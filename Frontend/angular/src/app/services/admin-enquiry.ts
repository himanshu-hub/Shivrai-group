
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';

export interface Enquiry {
  id: string;
  name: string;
  email: string;
  phone: string;
  subject: string;
  message: string;
  status: string;
  created_at: string;
}

export interface EnquiryResponse {
  total_enquiries: number;
  current_page: number;
  total_pages: number;
  enquiries: Enquiry[];
}

@Injectable({
  providedIn: 'root'
})
export class AdminEnquiryService {
  private http = inject(HttpClient);
  private apiUrl = 'http://127.0.0.1:8000/contact/';

  private getHeaders(): HttpHeaders {
    const token = typeof sessionStorage !== 'undefined'
      ? sessionStorage.getItem('admin_token')
      : null;

    return new HttpHeaders({
      Authorization: `Bearer ${token || ''}`
    });
  }
    
  getEnquiries(
    page = 1,
    limit = 10,
    search = '',
    status = ''
  ) {
    const params: Record<string, string | number> = {
      page,
      limit
    };

    if (search.trim()) {
      params['search'] = search.trim();
    }

    if (status) {
      params['status'] = status;
    }

    return this.http.get<EnquiryResponse>(this.apiUrl, {
      headers: this.getHeaders(),
      params
    });
  }


  deleteEnquiry(id: string) {
    return this.http.delete(`${this.apiUrl}${id}`, {
      headers: this.getHeaders()
    });
  } 
    updateStatus(id: string, status: string) {
    return this.http.patch<{ message: string; status: string }>(
        `${this.apiUrl}${id}/status`,
        null,
        {
        headers: this.getHeaders(),
        params: { status }
        }
    );
    }
}
