import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from '../../shared/components/navbar/navbar.component';
import { ApprovalService } from '../../core/services/approval.service';
import { Approval } from '../../core/models/approval.model';

@Component({
  selector: 'app-approval-list',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent],
  template: `
    <app-navbar></app-navbar>
    <div class="container">
      <h1 class="page-title">Pending Approvals</h1>
      <p class="subtitle">Review AI-proposed actions</p>
      <div class="card" *ngIf="!loading">
        <table class="data-table" *ngIf="approvals.length > 0">
          <thead>
            <tr>
              <th>Job Type</th>
              <th>Entity</th>
              <th>Action</th>
              <th>Confidence</th>
              <th>Reasoning</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let approval of approvals">
              <td>{{ approval.job_type }}</td>
              <td>{{ approval.entity_type }}</td>
              <td>{{ approval.action }}</td>
              <td>{{ approval.confidence }}%</td>
              <td class="text-small">{{ approval.reasoning }}</td>
              <td>
                <div class="action-buttons">
                  <button class="btn-small btn-primary" (click)="reviewApproval(approval.id, true)">
                    Approve
                  </button>
                  <button class="btn-small btn-secondary" (click)="reviewApproval(approval.id, false)">
                    Reject
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div *ngIf="approvals.length === 0" class="empty-state">
          No pending approvals
        </div>
      </div>
      <div *ngIf="loading" class="loading">Loading approvals...</div>
    </div>
  `,
  styles: [`
    .page-title {
      font-size: 48px;
      font-weight: 700;
      background: linear-gradient(135deg, var(--arthava-gold) 0%, var(--arthava-gold-light) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin-bottom: 16px;
      letter-spacing: -0.5px;
    }

    .subtitle {
      font-size: 22px;
      color: var(--text-muted);
      margin-bottom: 40px;
      font-weight: 400;
    }

    .data-table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      font-size: 17px;
    }

    .data-table thead {
      background: linear-gradient(135deg, rgba(200, 168, 112, 0.15) 0%, rgba(200, 168, 112, 0.08) 100%);
    }

    .data-table thead th {
      padding: 24px 20px;
      text-align: left;
      color: var(--arthava-gold);
      font-weight: 600;
      font-size: 18px;
      border-bottom: 2px solid var(--arthava-gold);
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .data-table thead th:first-child {
      border-top-left-radius: 16px;
    }

    .data-table thead th:last-child {
      border-top-right-radius: 16px;
    }

    .data-table tbody tr {
      transition: all 0.3s ease;
      border-bottom: 1px solid var(--border-color);
    }

    .data-table tbody tr:hover {
      background: rgba(200, 168, 112, 0.08);
      transform: scale(1.01);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    .data-table tbody tr:last-child {
      border-bottom: none;
    }

    .data-table tbody td {
      padding: 24px 20px;
      color: var(--text-light);
      font-size: 17px;
    }

    .text-small {
      font-size: 15px;
      color: var(--text-muted);
      max-width: 400px;
    }

    .action-buttons {
      display: flex;
      gap: 12px;
    }

    .btn-small {
      padding: 10px 20px;
      border: none;
      border-radius: 10px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .btn-primary {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }

    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
    }

    .btn-secondary {
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
    }

    .btn-secondary:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
    }

    .empty-state {
      text-align: center;
      padding: 80px 40px;
      color: var(--text-muted);
      font-size: 22px;
      background: linear-gradient(135deg, rgba(200, 168, 112, 0.05) 0%, rgba(200, 168, 112, 0.02) 100%);
      border-radius: 16px;
      border: 2px dashed var(--border-color);
    }

    .loading {
      text-align: center;
      padding: 80px 40px;
      font-size: 22px;
      color: var(--arthava-gold);
      animation: pulse 1.5s ease-in-out infinite;
    }

    @keyframes pulse {
      0%, 100% {
        opacity: 1;
      }
      50% {
        opacity: 0.5;
      }
    }
  `]
})
export class ApprovalListComponent implements OnInit {
  approvals: Approval[] = [];
  loading = true;

  constructor(
    private approvalService: ApprovalService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadApprovals();
  }

  loadApprovals(): void {
    this.loading = true;
    this.approvalService.getApprovals().subscribe({
      next: (approvals) => {
        this.approvals = approvals.filter(a => a.status === 'pending');
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  reviewApproval(id: number, approved: boolean): void {
    this.approvalService.reviewApproval(id, approved).subscribe({
      next: () => {
        this.approvals = this.approvals.filter(a => a.id !== id);
        this.cdr.detectChanges();
      }
    });
  }
}
