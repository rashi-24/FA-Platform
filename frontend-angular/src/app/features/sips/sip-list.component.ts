import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from '../../shared/components/navbar/navbar.component';
import { SIPService } from '../clients/services/sip.service';
import { SIP } from '../../core/models/sip.model';

@Component({
  selector: 'app-sip-list',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent],
  template: `
    <app-navbar></app-navbar>
    <div class="container">
      <h1 class="page-title">Systematic Investment Plans (SIPs)</h1>
      <div class="card" *ngIf="!loading">
        <table class="data-table" *ngIf="sips.length > 0">
          <thead>
            <tr>
              <th>Client</th>
              <th>Fund Name</th>
              <th>Folio Number</th>
              <th>Amount</th>
              <th>SIP Day</th>
              <th>Frequency</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let sip of sips">
              <td>{{ sip.client_name }}</td>
              <td>{{ sip.fund_name }}</td>
              <td>{{ sip.folio_number }}</td>
              <td>₹{{ sip.sip_amount | number }}</td>
              <td>{{ sip.sip_day }}</td>
              <td>{{ sip.sip_frequency }}</td>
              <td>
                <span class="badge" [class]="getStatusClass(sip.status)">
                  {{ sip.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div *ngIf="sips.length === 0" class="empty-state">
          No SIPs found
        </div>
      </div>
      <div *ngIf="loading" class="loading">Loading SIPs...</div>
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
export class SIPListComponent implements OnInit {
  sips: SIP[] = [];
  loading = true;

  constructor(
    private sipService: SIPService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadSIPs();
  }

  loadSIPs(): void {
    this.loading = true;
    this.sipService.getSIPs().subscribe({
      next: (sips) => {
        this.sips = sips;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  getStatusClass(status: string): string {
    const statusMap: Record<string, string> = {
      'active': 'success',
      'paused': 'warning',
      'stopped': 'danger'
    };
    return statusMap[status] || 'info';
  }
}
