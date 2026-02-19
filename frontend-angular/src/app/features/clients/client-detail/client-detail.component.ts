import { Component, OnInit, AfterViewInit, ViewChild, ElementRef, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute } from '@angular/router';
import { NavbarComponent } from '../../../shared/components/navbar/navbar.component';
import { ClientService } from '../services/client.service';
import { ClientDetail, AIPortfolioAnalysis } from '../../../core/models/client.model';
import { Chart, ChartConfiguration } from 'chart.js/auto';

@Component({
  selector: 'app-client-detail',
  standalone: true,
  imports: [CommonModule, RouterModule, NavbarComponent],
  templateUrl: './client-detail.component.html',
  styleUrls: ['./client-detail.component.scss']
})
export class ClientDetailComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('policyChart') policyChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('sipChart') sipChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('premiumChart') premiumChartRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('sipAmountChart') sipAmountChartRef!: ElementRef<HTMLCanvasElement>;

  client: ClientDetail | null = null;
  aiAnalysis: AIPortfolioAnalysis | null = null;
  loading = true;
  aiLoading = true;

  private charts: Chart[] = [];

  constructor(
    private route: ActivatedRoute,
    private clientService: ClientService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const clientId = Number(this.route.snapshot.paramMap.get('id'));
    this.loadClient(clientId);
    this.loadAIAnalysis(clientId);
  }

  ngAfterViewInit(): void {
    if (this.client && !this.loading) {
      this.renderCharts();
    }
  }

  ngOnDestroy(): void {
    this.charts.forEach(chart => chart.destroy());
  }

  loadClient(id: number): void {
    this.clientService.getClient(id).subscribe({
      next: (client) => {
        this.client = client;
        this.loading = false;
        this.cdr.detectChanges();
        setTimeout(() => this.renderCharts(), 0);
      },
      error: () => {
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  loadAIAnalysis(id: number): void {
    this.clientService.getAIPortfolioAnalysis(id).subscribe({
      next: (analysis) => {
        this.aiAnalysis = analysis;
        this.aiLoading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.aiLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  renderCharts(): void {
    if (!this.client) return;

    this.renderPolicyDistribution();
    this.renderSIPDistribution();
    this.renderPremiumBreakdown();
    this.renderSIPAmountBreakdown();
  }

  renderPolicyDistribution(): void {
    if (!this.client || !this.policyChartRef) return;

    const providerMap: { [key: string]: number } = {};
    this.client.policies.forEach(p => {
      providerMap[p.provider] = (providerMap[p.provider] || 0) + 1;
    });

    const labels = Object.keys(providerMap);
    const data = Object.values(providerMap);

    const config: ChartConfiguration = {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#43e97b']
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          title: { display: true, text: 'Policy Distribution by Provider' }
        }
      }
    };

    const chart = new Chart(this.policyChartRef.nativeElement, config);
    this.charts.push(chart);
  }

  renderSIPDistribution(): void {
    if (!this.client || !this.sipChartRef) return;

    const fundMap: { [key: string]: number } = {};
    this.client.sips.forEach(s => {
      fundMap[s.fund_name] = (fundMap[s.fund_name] || 0) + 1;
    });

    const labels = Object.keys(fundMap);
    const data = Object.values(fundMap);

    const config: ChartConfiguration = {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#43e97b']
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
          title: { display: true, text: 'SIP Distribution by Fund' }
        }
      }
    };

    const chart = new Chart(this.sipChartRef.nativeElement, config);
    this.charts.push(chart);
  }

  renderPremiumBreakdown(): void {
    if (!this.client || !this.premiumChartRef) return;

    const typeMap: { [key: string]: number } = {};
    this.client.policies.forEach(p => {
      const annual = this.calculateAnnualPremium(p.premium_amount, p.payment_frequency);
      typeMap[p.policy_type] = (typeMap[p.policy_type] || 0) + annual;
    });

    const labels = Object.keys(typeMap);
    const data = Object.values(typeMap);

    const config: ChartConfiguration = {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Annual Premium (₹)',
          data,
          backgroundColor: '#667eea'
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          title: { display: true, text: 'Annual Premium Breakdown by Type' }
        },
        scales: {
          y: { beginAtZero: true }
        }
      }
    };

    const chart = new Chart(this.premiumChartRef.nativeElement, config);
    this.charts.push(chart);
  }

  renderSIPAmountBreakdown(): void {
    if (!this.client || !this.sipAmountChartRef) return;

    const fundMap: { [key: string]: number } = {};
    this.client.sips.forEach(s => {
      const monthly = this.calculateMonthlySIP(s.sip_amount, s.sip_frequency);
      fundMap[s.fund_name] = (fundMap[s.fund_name] || 0) + monthly;
    });

    const labels = Object.keys(fundMap);
    const data = Object.values(fundMap);

    const config: ChartConfiguration = {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Monthly SIP (₹)',
          data,
          backgroundColor: '#764ba2'
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          title: { display: true, text: 'Monthly SIP Amount Breakdown' }
        },
        scales: {
          y: { beginAtZero: true }
        }
      }
    };

    const chart = new Chart(this.sipAmountChartRef.nativeElement, config);
    this.charts.push(chart);
  }

  calculateSummaryStats() {
    if (!this.client) return { policies: 0, sips: 0, premium: 0, sipAmount: 0 };

    const activePolicies = this.client.policies.filter(p => p.status === 'active').length;
    const activeSIPs = this.client.sips.filter(s => s.status === 'active').length;

    const annualPremium = this.client.policies
      .filter(p => p.status === 'active')
      .reduce((sum, p) => sum + this.calculateAnnualPremium(p.premium_amount, p.payment_frequency), 0);

    const monthlySIP = this.client.sips
      .filter(s => s.status === 'active')
      .reduce((sum, s) => sum + this.calculateMonthlySIP(s.sip_amount, s.sip_frequency), 0);

    return {
      policies: activePolicies,
      sips: activeSIPs,
      premium: annualPremium,
      sipAmount: monthlySIP
    };
  }

  calculateAnnualPremium(amount: number, frequency: string): number {
    const multipliers: { [key: string]: number } = {
      'Monthly': 12,
      'Quarterly': 4,
      'Yearly': 1
    };
    return amount * (multipliers[frequency] || 1);
  }

  calculateMonthlySIP(amount: number, frequency: string): number {
    const divisors: { [key: string]: number} = {
      'Monthly': 1,
      'Quarterly': 3,
      'Yearly': 12
    };
    return amount / (divisors[frequency] || 1);
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value);
  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  }

  getStatusClass(status: string): string {
    const statusMap: { [key: string]: string } = {
      'active': 'success',
      'lapsed': 'danger',
      'paused': 'warning',
      'stopped': 'danger'
    };
    return statusMap[status] || 'info';
  }

  getScoreLevel(score: number): string {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'fair';
    return 'poor';
  }

  getRiskClass(level: string): string {
    const riskMap: { [key: string]: string } = {
      'Low': 'success',
      'Medium': 'warning',
      'High': 'danger'
    };
    return riskMap[level] || 'info';
  }
}
