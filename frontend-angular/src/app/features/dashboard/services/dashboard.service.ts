import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { DashboardStats, AIInsight } from '../../../core/models/dashboard.model';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private readonly API_BASE = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getDashboardStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.API_BASE}/dashboard`);
  }

  getDailyInsights(): Observable<AIInsight[]> {
    return this.http.get<AIInsight[]>(`${this.API_BASE}/agents/capital-companion/daily`);
  }
}
