
import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/home/home').then(m => m.Home)
  },
  {
    path: 'projects',
    loadComponent: () => import('./pages/projects/projects').then(m => m.Projects)
  },
  {
    path: 'projects/:id',
    loadComponent: () =>
      import('./pages/project-details/project-details')
        .then(m => m.ProjectDetails)
  },
  {
    path: 'offices',
    loadComponent: () => import('./pages/offices/offices').then(m => m.Offices)
  },
  {
    path: 'retail',
    loadComponent: () => import('./pages/retail/retail').then(m => m.Retail)
  },
  {
    path: 'about',
    loadComponent: () => import('./pages/about/about').then(m => m.About)
  },
  {
    path: 'careers',
    loadComponent: () => import('./pages/careers/careers').then(m => m.Careers)
  },
  {
    path: 'contact',
    loadComponent: () => import('./pages/contact/contact').then(m => m.Contact)
  }
];
