import { HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  console.log('[AuthInterceptor] Request:', req.method, req.url);

  // Skip auth for login/register endpoints
  if (req.url.includes('/auth/login') || req.url.includes('/auth/register')) {
    console.log('[AuthInterceptor] Skipping auth for login/register');
    return next(req);
  }

  // Get token directly from localStorage to avoid circular dependency issues
  const token = localStorage.getItem('access_token');
  console.log('[AuthInterceptor] Token from localStorage:', token ? token.substring(0, 20) + '...' : 'NO TOKEN');

  // Add Authorization header if token exists
  if (token) {
    req = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
    console.log('[AuthInterceptor] Authorization header added');
  } else {
    console.log('[AuthInterceptor] No token available, request sent without auth');
  }

  return next(req);
};
