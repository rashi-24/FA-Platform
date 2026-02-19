export interface Policy {
  id: number;
  client_id: number;
  client_name?: string;
  policy_number: string;
  provider: string;
  policy_type: string;
  premium_amount: number;
  payment_frequency: 'Monthly' | 'Quarterly' | 'Yearly';
  renewal_date: string;
  sum_assured?: number | null;
  status: 'active' | 'lapsed' | 'pending';
  created_at: string;
  updated_at: string;
}
