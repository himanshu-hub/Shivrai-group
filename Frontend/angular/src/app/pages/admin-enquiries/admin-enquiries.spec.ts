import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AdminEnquiries } from './admin-enquiries';

describe('AdminEnquiries', () => {
  let component: AdminEnquiries;
  let fixture: ComponentFixture<AdminEnquiries>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminEnquiries],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminEnquiries);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
