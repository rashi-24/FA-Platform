import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Approval, ApprovalReview } from '../models/approval.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApprovalService {
  private readonly API_BASE = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getApprovals(): Observable<Approval[]> {
    return this.http.get<Approval[]>(`${this.API_BASE}/approvals`);
  }

  reviewApproval(approvalId: number, approved: boolean): Observable<void> {
    const review: ApprovalReview = { approval_id: approvalId, approved };
    return this.http.post<void>(`${this.API_BASE}/approvals/${approvalId}/review`, review);
  }
}
