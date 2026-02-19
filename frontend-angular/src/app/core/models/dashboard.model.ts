export interface DashboardStats {
  total_clients: number;
  total_policies: number;
  total_sips: number;
  total_aum: number;
  upcoming_renewals: number;
  upcoming_sips: number;
  pending_approvals: number;
  recent_meetings: number;
}

export interface AIInsight {
  id: string;
  icon: string;
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high';
}
