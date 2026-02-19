import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const notification = inject(NotificationService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'An error occurred';

      if (error.status === 401) {
        // Unauthorized - clear session and redirect to login
        authService.logout();
        notification.error('Session expired. Please login again.');
      } else if (error.status === 403) {
        errorMessage = 'Access denied';
        notification.error(errorMessage);
      } else if (error.status >= 500) {
        errorMessage = 'Server error. Please try again later.';
        notification.error(errorMessage);
      } else if (error.error?.detail) {
        errorMessage = error.error.detail;
        notification.error(errorMessage);
      } else {
        notification.error(errorMessage);
      }

      return throwError(() => error);
    })
  );
};
