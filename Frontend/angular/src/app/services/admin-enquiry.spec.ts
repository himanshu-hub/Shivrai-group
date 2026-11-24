import { TestBed } from '@angular/core/testing';
import { AdminEnquiry } from './admin-enquiry';

describe('AdminEnquiry', () => {
  let service: AdminEnquiry;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AdminEnquiry);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
