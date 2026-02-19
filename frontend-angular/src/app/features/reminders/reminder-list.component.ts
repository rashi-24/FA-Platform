import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from '../../shared/components/navbar/navbar.component';
import { ReminderService } from '../../core/services/reminder.service';
import { Reminder } from '../../core/models/reminder.model';

@Component({
  selector: 'app-reminder-list',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent],
  template: `
    <app-navbar></app-navbar>
    <div class="container">
      <div class="header-section">
        <h1 class="page-title">Reminders</h1>
        <button class="btn btn-primary" (click)="runReminderAgent()">
          🤖 Run Reminder Agent
        </button>
      </div>
      <div class="card" *ngIf="!loading">
        <table class="data-table" *ngIf="reminders.length > 0">
          <thead>
            <tr>
              <th>Type</th>
              <th>Message</th>
              <th>Due Date</th>
              <th>Urgency</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let reminder of reminders">
              <td>{{ reminder.reminder_type }}</td>
              <td>{{ reminder.message }}</td>
              <td>{{ formatDate(reminder.due_date) }}</td>
              <td>
                <span class="badge" [class]="getUrgencyClass(reminder.urgency)">
                  {{ reminder.urgency }}
                </span>
              </td>
              <td>
                <button class="btn-small btn-secondary" (click)="dismissReminder(reminder.id)" *ngIf="!reminder.is_dismissed">
                  Dismiss
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div *ngIf="reminders.length === 0" class="empty-state">
          🎉 No reminders - All caught up!
        </div>
      </div>
      <div *ngIf="loading" class="loading">Loading reminders...</div>
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
      margin-bottom: 0;
      letter-spacing: -0.5px;
    }

    .header-section {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 40px;
    }

    .btn {
      padding: 16px 32px;
      border: none;
      border-radius: 12px;
      font-size: 18px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .btn-primary {
      background: linear-gradient(135deg, var(--arthava-gold) 0%, var(--arthava-gold-dark) 100%);
      color: var(--arthava-navy);
      box-shadow: 0 4px 12px rgba(200, 168, 112, 0.3);
    }

    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(200, 168, 112, 0.4);
      background: linear-gradient(135deg, var(--arthava-gold-light) 0%, var(--arthava-gold) 100%);
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

    .btn-small {
      padding: 10px 20px;
      border: none;
      border-radius: 10px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .btn-secondary {
      background: linear-gradient(135deg, rgba(200, 168, 112, 0.2) 0%, rgba(200, 168, 112, 0.1) 100%);
      color: var(--arthava-gold);
      border: 1px solid var(--arthava-gold);
    }

    .btn-secondary:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(200, 168, 112, 0.3);
      background: linear-gradient(135deg, rgba(200, 168, 112, 0.3) 0%, rgba(200, 168, 112, 0.2) 100%);
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
export class ReminderListComponent implements OnInit {
  reminders: Reminder[] = [];
  loading = true;

  constructor(
    private reminderService: ReminderService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadReminders();
  }

  loadReminders(): void {
    this.loading = true;
    this.reminderService.getReminders(30).subscribe({
      next: (reminders) => {
        this.reminders = reminders;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  dismissReminder(id: number): void {
    this.reminderService.dismissReminder(id).subscribe({
      next: () => {
        this.reminders = this.reminders.filter(r => r.id !== id);
        this.cdr.detectChanges();
      }
    });
  }

  runReminderAgent(): void {
    this.reminderService.runReminderAgent().subscribe({
      next: () => {
        this.loadReminders();
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

  getUrgencyClass(urgency: string): string {
    const urgencyMap: Record<string, string> = {
      'high': 'danger',
      'medium': 'warning',
      'low': 'info'
    };
    return urgencyMap[urgency] || 'info';
  }
}
