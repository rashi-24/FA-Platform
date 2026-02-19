import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from '../../shared/components/navbar/navbar.component';
import { PolicyService } from '../clients/services/policy.service';
import { Policy } from '../../core/models/policy.model';

@Component({
  selector: 'app-policy-list',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent],
  template: `
    <app-navbar></app-navbar>
    <div class="container">
      <h1 class="page-title">Policies</h1>
      <div class="card" *ngIf="!loading">
        <table class="data-table" *ngIf="policies.length > 0">
          <thead>
            <tr>
              <th>Client</th>
              <th>Policy Number</th>
              <th>Provider</th>
              <th>Type</th>
              <th>Premium</th>
              <th>Renewal Date</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let policy of policies">
              <td>{{ policy.client_name }}</td>
              <td>{{ policy.policy_number }}</td>
              <td>{{ policy.provider }}</td>
              <td>{{ policy.policy_type }}</td>
              <td>₹{{ policy.premium_amount | number }}</td>
              <td>{{ formatDate(policy.renewal_date) }}</td>
              <td>
                <span class="badge" [class]="getStatusClass(policy.status)">
                  {{ policy.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div *ngIf="policies.length === 0" class="empty-state">
          No policies found
        </div>
      </div>
      <div *ngIf="loading" class="loading">Loading policies...</div>
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
      margin-bottom: 40px;
      letter-spacing: -0.5px;
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

    .badge {
      padding: 8px 18px;
      border-radius: 20px;
      font-size: 15px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      display: inline-block;
    }

    .badge.success {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }

    .badge.danger {
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
    }

    .badge.warning {
      background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
    }

    .badge.info {
      background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
      color: white;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
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
export class PolicyListComponent implements OnInit {
  policies: Policy[] = [];
  loading = true;

  constructor(
    private policyService: PolicyService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadPolicies();
  }

  loadPolicies(): void {
    this.loading = true;
    this.policyService.getPolicies().subscribe({
      next: (policies) => {
        this.policies = policies;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  }

  getStatusClass(status: string): string {
    const statusMap: Record<string, string> = {
      'active': 'success',
      'lapsed': 'danger',
      'pending': 'warning'
    };
    return statusMap[status] || 'info';
  }
}
