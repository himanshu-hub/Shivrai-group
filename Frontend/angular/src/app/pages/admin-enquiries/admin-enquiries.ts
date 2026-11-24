
import {
  Component,
  inject,
  OnInit,
  ChangeDetectorRef,
  PLATFORM_ID
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { isPlatformBrowser, DatePipe } from '@angular/common';

import {
  AdminEnquiryService,
  Enquiry
} from '../../services/admin-enquiry';

@Component({
  selector: 'app-admin-enquiries',
  imports: [DatePipe, FormsModule],
  templateUrl: './admin-enquiries.html',
  styleUrl: './admin-enquiries.scss'
})
export class AdminEnquiries implements OnInit {
  private enquiryService = inject(AdminEnquiryService);
  private cdr = inject(ChangeDetectorRef);
  private platformId = inject(PLATFORM_ID);

  enquiries: Enquiry[] = [];

  loading = true;
  error = '';
  statusMessage = '';

  searchQuery = '';
  filterStatus = '';

  currentPage = 1;
  totalPages = 0;
  totalEnquiries = 0;

  updatingId: string | null = null;
  deletingId: string | null = null;

  ngOnInit() {
    if (isPlatformBrowser(this.platformId)) {
      this.loadEnquiries();
    }
  }

  // FETCH ENQUIRIES WITH SEARCH, FILTER AND PAGINATION

  loadEnquiries(page = 1) {
    this.loading = true;
    this.error = '';
    this.cdr.detectChanges();

    this.enquiryService.getEnquiries(
      page,
      10,
      this.searchQuery,
      this.filterStatus
    ).subscribe({
      next: (response) => {
        this.enquiries = response.enquiries;
        this.currentPage = response.current_page;
        this.totalPages = response.total_pages;
        this.totalEnquiries = response.total_enquiries;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.error = err.status === 401
          ? 'Session expired. Please log in again.'
          : 'Unable to load enquiries.';

        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  // SEARCH AND STATUS FILTERS

  applyFilters() {
    this.loadEnquiries(1);
  }

  clearFilters() {
    this.searchQuery = '';
    this.filterStatus = '';
    this.loadEnquiries(1);
  }

  // PAGINATION

  nextPage() {
    if (!this.loading && this.currentPage < this.totalPages) {
      this.loadEnquiries(this.currentPage + 1);
    }
  }

  previousPage() {
    if (!this.loading && this.currentPage > 1) {
      this.loadEnquiries(this.currentPage - 1);
    }
  }

  // UPDATE ENQUIRY STATUS

  updateEnquiryStatus(enquiry: Enquiry, status: string) {
    if (this.updatingId || this.deletingId || status === enquiry.status) {
      return;
    }

    this.updatingId = enquiry.id;
    this.statusMessage = '';
    this.error = '';

    this.enquiryService.updateStatus(enquiry.id, status).subscribe({
      next: (response) => {
        enquiry.status = response.status;
        this.statusMessage = `Status updated for ${enquiry.name}.`;
        this.updatingId = null;

        // Refresh if the updated enquiry no longer matches the filter
        if (this.filterStatus && this.filterStatus !== response.status) {
          this.loadEnquiries(this.currentPage);
        }

        this.cdr.detectChanges();
      },
      error: (err) => {
        this.error = err.status === 401
          ? 'Session expired. Please log in again.'
          : 'Unable to update enquiry status.';

        this.updatingId = null;
        this.loadEnquiries(this.currentPage);
        this.cdr.detectChanges();
      }
    });
  }

  // DELETE ENQUIRY

  deleteEnquiry(enquiry: Enquiry) {
    if (this.deletingId || this.updatingId) return;

    const confirmed = confirm(
      `Are you sure you want to delete the enquiry from "${enquiry.name}"?`
    );

    if (!confirmed) return;

    this.deletingId = enquiry.id;
    this.error = '';
    this.statusMessage = '';

    this.enquiryService.deleteEnquiry(enquiry.id).subscribe({
      next: () => {
        this.deletingId = null;
        this.statusMessage = 'Enquiry deleted successfully.';

        const page =
          this.enquiries.length === 1 && this.currentPage > 1
            ? this.currentPage - 1
            : this.currentPage;

        this.loadEnquiries(page);
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.error = err.status === 401
          ? 'Session expired. Please log in again.'
          : 'Unable to delete enquiry.';

        this.deletingId = null;
        this.cdr.detectChanges();
      }
    });
  }
}
