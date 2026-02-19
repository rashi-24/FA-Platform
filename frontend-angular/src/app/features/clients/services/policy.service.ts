import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Policy } from '../../../core/models/policy.model';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class PolicyService {
  private readonly API_BASE = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getPolicies(): Observable<Policy[]> {
    return this.http.get<Policy[]>(`${this.API_BASE}/policies`);
  }

  createPolicy(policy: Partial<Policy>): Observable<Policy> {
    return this.http.post<Policy>(`${this.API_BASE}/policies`, policy);
  }

  updatePolicy(id: number, policy: Partial<Policy>): Observable<Policy> {
    return this.http.put<Policy>(`${this.API_BASE}/policies/${id}`, policy);
  }

  deletePolicy(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API_BASE}/policies/${id}`);
  }
}
