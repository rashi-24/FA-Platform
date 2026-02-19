import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap, switchMap } from 'rxjs';
import { Router } from '@angular/router';
import { StorageService } from './storage.service';
import { User, LoginCredentials, RegisterData, LoginResponse } from '../models/user.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly TOKEN_KEY = 'access_token';
  private readonly TOKEN_EXPIRES_KEY = 'token_expires_at';
  private readonly API_BASE = environment.apiBaseUrl;

  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor(
    private http: HttpClient,
    private storage: StorageService,
    private router: Router
  ) {
    this.loadCurrentUser();
  }

  login(credentials: LoginCredentials): Observable<User> {
    console.log('[AuthService] Attempting login with:', credentials.email);
    return this.http.post<LoginResponse>(`${this.API_BASE}/auth/login`, credentials).pipe(
      tap(response => {
        console.log('[AuthService] Login response received:', response);
        this.setSession(response);
        console.log('[AuthService] Token stored in localStorage:', localStorage.getItem(this.TOKEN_KEY)?.substring(0, 20) + '...');
      }),
      switchMap(() => {
        console.log('[AuthService] Loading user info...');
        return this.loadUserInfo();
      })
    );
  }

  register(data: RegisterData): Observable<void> {
    return this.http.post<void>(`${this.API_BASE}/auth/register`, data);
  }

  logout(): void {
    this.storage.removeItem(this.TOKEN_KEY);
    this.storage.removeItem(this.TOKEN_EXPIRES_KEY);
    this.currentUserSubject.next(null);
    this.router.navigate(['/auth/login']);
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    const expiresAt = this.storage.getItem(this.TOKEN_EXPIRES_KEY);
    return !!token && !!expiresAt && Date.now() < parseInt(expiresAt);
  }

  getToken(): string | null {
    return this.storage.getItem(this.TOKEN_KEY);
  }

  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  private setSession(authResult: LoginResponse): void {
    console.log('[AuthService] Setting session with token:', authResult.access_token.substring(0, 20) + '...');
    this.storage.setItem(this.TOKEN_KEY, authResult.access_token);
    const expiresAt = Date.now() + (authResult.expires_in * 1000);
    this.storage.setItem(this.TOKEN_EXPIRES_KEY, expiresAt.toString());
    console.log('[AuthService] Session set, expires at:', new Date(expiresAt).toISOString());
  }

  private loadUserInfo(): Observable<User> {
    console.log('[AuthService] Fetching /api/auth/me');
    return this.http.get<User>(`${this.API_BASE}/auth/me`).pipe(
      tap(user => {
        console.log('[AuthService] User info loaded:', user);
        this.currentUserSubject.next(user);
      })
    );
  }

  private loadCurrentUser(): void {
    if (this.isAuthenticated()) {
      this.loadUserInfo().subscribe({
        error: (error) => {
          console.error('[AuthService] Failed to load user on init, but keeping token:', error);
          // Don't logout on page refresh - the token might still be valid
          // Only clear if it's a 401 Unauthorized
          if (error.status === 401) {
            console.log('[AuthService] Token is invalid (401), clearing session');
            this.storage.removeItem(this.TOKEN_KEY);
            this.storage.removeItem(this.TOKEN_EXPIRES_KEY);
            this.currentUserSubject.next(null);
          }
        }
      });
    }
  }
}
