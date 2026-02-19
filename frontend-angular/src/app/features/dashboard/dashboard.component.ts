import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from '../../shared/components/navbar/navbar.component';
import { StatCardComponent } from '../../shared/components/stat-card/stat-card.component';
import { DashboardService } from './services/dashboard.service';
import { PolicyService } from '../clients/services/policy.service';
import { SIPService } from '../clients/services/sip.service';
import { ReminderService } from '../../core/services/reminder.service';
import { ApprovalService } from '../../core/services/approval.service';
import { MeetingService } from '../calendar/services/meeting.service';
import { DashboardStats, AIInsight } from '../../core/models/dashboard.model';
import { Policy } from '../../core/models/policy.model';
import { SIP } from '../../core/models/sip.model';
import { Reminder } from '../../core/models/reminder.model';
import { Approval } from '../../core/models/approval.model';
import { Meeting } from '../../core/models/meeting.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent, StatCardComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  stats: DashboardStats | null = null;
  insights: AIInsight[] = [];
  urgentReminders: Reminder[] = [];
  upcomingMeetings: Meeting[] = [];
  policies: Policy[] = [];
  sips: SIP[] = [];
  reminders: Reminder[] = [];
  approvals: Approval[] = [];

  activeTab: string = 'policies';
  loading = {
    stats: true,
    insights: true,
    reminders: true,
    meetings: true,
    policies: true,
    sips: true,
    approvals: true
  };

  constructor(
    private dashboardService: DashboardService,
    private policyService: PolicyService,
    private sipService: SIPService,
    private reminderService: ReminderService,
    private approvalService: ApprovalService,
    private meetingService: MeetingService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadDashboardData();
  }

  private loadDashboardData(): void {
    console.log('[Dashboard] Loading dashboard data...');

    this.dashboardService.getDashboardStats().subscribe({
      next: (stats) => {
        console.log('[Dashboard] Stats received:', stats);
        this.stats = stats;
        this.loading.stats = false;
        console.log('[Dashboard] Stats loading flag set to false, triggering change detection');
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('[Dashboard] Error loading stats:', error);
        this.loading.stats = false;
        this.cdr.detectChanges();
      }
    });

    this.dashboardService.getDailyInsights().subscribe({
      next: (insights) => {
        console.log('[Dashboard] Insights received:', insights);
        this.insights = insights;
        this.loading.insights = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('[Dashboard] Error loading insights:', error);
        this.loading.insights = false;
        this.cdr.detectChanges();
      }
    });

    this.reminderService.getReminders(7, 5).subscribe({
      next: (reminders) => {
        console.log('[Dashboard] Reminders received:', reminders);
        this.urgentReminders = reminders.filter(r => !r.is_dismissed);
        this.loading.reminders = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('[Dashboard] Error loading reminders:', error);
        this.loading.reminders = false;
        this.cdr.detectChanges();
      }
    });

    this.meetingService.getMeetings().subscribe({
      next: (meetings) => {
        console.log('[Dashboard] Meetings received:', meetings);
        const now = new Date();
        const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
        this.upcomingMeetings = meetings
          .filter(m => new Date(m.meeting_date) <= nextWeek)
          .slice(0, 5);
        this.loading.meetings = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('[Dashboard] Error loading meetings:', error);
        this.loading.meetings = false;
        this.cdr.detectChanges();
      }
    });

    this.loadPolicies();

    this.approvalService.getApprovals().subscribe({
      next: (approvals) => {
        console.log('[Dashboard] Approvals received:', approvals);
        this.approvals = approvals.filter(a => a.status === 'pending');
        this.loading.approvals = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('[Dashboard] Error loading approvals:', error);
        this.loading.approvals = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadPolicies(): void {
    this.loading.policies = true;
    this.policyService.getPolicies().subscribe({
      next: (policies) => {
        console.log('[Dashboard] Policies received:', policies);
        this.policies = policies;
        this.loading.policies = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('[Dashboard] Error loading policies:', error);
        this.loading.policies = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadSIPs(): void {
    this.loading.sips = true;
    this.sipService.getSIPs().subscribe({
      next: (sips) => {
        this.sips = sips;
        this.loading.sips = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading.sips = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadReminders(): void {
    this.loading.reminders = true;
    this.reminderService.getReminders(30).subscribe({
      next: (reminders) => {
        this.reminders = reminders;
        this.loading.reminders = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading.reminders = false;
        this.cdr.detectChanges();
      }
    });
  }

  showTab(tab: string): void {
    this.activeTab = tab;

    if (tab === 'sips' && this.sips.length === 0) {
      this.loadSIPs();
    } else if (tab === 'reminders' && this.reminders.length === 0) {
      this.loadReminders();
    }
  }

  dismissReminder(id: number): void {
    this.reminderService.dismissReminder(id).subscribe({
      next: () => {
        this.urgentReminders = this.urgentReminders.filter(r => r.id !== id);
        this.reminders = this.reminders.filter(r => r.id !== id);
      }
    });
  }

  reviewApproval(id: number, approved: boolean): void {
    this.approvalService.reviewApproval(id, approved).subscribe({
      next: () => {
        this.approvals = this.approvals.filter(a => a.id !== id);
        if (this.stats) {
          this.stats.pending_approvals--;
        }
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

  formatCurrency(value: number): string {
    if (value >= 10000000) {
      return `₹${(value / 10000000).toFixed(2)}Cr`;
    } else if (value >= 100000) {
      return `₹${(value / 100000).toFixed(2)}L`;
    } else if (value >= 1000) {
      return `₹${(value / 1000).toFixed(2)}K`;
    }
    return `₹${value.toFixed(2)}`;
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
      'paused': 'warning',
      'stopped': 'danger',
      'pending': 'warning',
      'approved': 'success',
      'rejected': 'danger'
    };
    return statusMap[status] || 'info';
  }

  getUrgencyClass(urgency: string): string {
    const urgencyMap: Record<string, string> = {
      'high': 'danger',
      'medium': 'warning',
      'low': 'info'
    };
    return urgencyMap[urgency] || 'info';
  }

  getPriorityClass(priority: string): string {
    const priorityMap: Record<string, string> = {
      'high': 'priority-high',
      'medium': 'priority-medium',
      'low': 'priority-low'
    };
    return priorityMap[priority] || 'priority-low';
  }
}
