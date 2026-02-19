import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full'
  },
  {
    path: 'auth/login',
    loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent),
    title: 'Login - ARTHAVA'
  },
  {
    path: 'auth/register',
    loadComponent: () => import('./features/auth/register/register.component').then(m => m.RegisterComponent),
    title: 'Register - ARTHAVA'
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent),
    canActivate: [authGuard],
    title: 'Dashboard - ARTHAVA'
  },
  {
    path: 'clients',
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./features/clients/client-list/client-list.component').then(m => m.ClientListComponent),
        title: 'Clients - ARTHAVA'
      },
      {
        path: ':id',
        loadComponent: () => import('./features/clients/client-detail/client-detail.component').then(m => m.ClientDetailComponent),
        title: 'Client Detail - ARTHAVA'
      }
    ]
  },
  {
    path: 'policies',
    loadComponent: () => import('./features/policies/policy-list.component').then(m => m.PolicyListComponent),
    canActivate: [authGuard],
    title: 'Policies - ARTHAVA'
  },
  {
    path: 'sips',
    loadComponent: () => import('./features/sips/sip-list.component').then(m => m.SIPListComponent),
    canActivate: [authGuard],
    title: 'SIPs - ARTHAVA'
  },
  {
    path: 'reminders',
    loadComponent: () => import('./features/reminders/reminder-list.component').then(m => m.ReminderListComponent),
    canActivate: [authGuard],
    title: 'Reminders - ARTHAVA'
  },
  {
    path: 'approvals',
    loadComponent: () => import('./features/approvals/approval-list.component').then(m => m.ApprovalListComponent),
    canActivate: [authGuard],
    title: 'Approvals - ARTHAVA'
  },
  {
    path: 'calendar',
    loadComponent: () => import('./features/calendar/calendar.component').then(m => m.CalendarComponent),
    canActivate: [authGuard],
    title: 'Calendar - ARTHAVA'
  },
  {
    path: '**',
    redirectTo: 'dashboard'
  }
];
