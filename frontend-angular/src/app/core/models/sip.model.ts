export interface SIP {
  id: number;
  client_id: number;
  client_name?: string;
  fund_name: string;
  folio_number: string;
  sip_amount: number;
  sip_frequency: 'Monthly' | 'Quarterly' | 'Yearly';
  sip_day: number;
  start_date: string;
  end_date?: string | null;
  status: 'active' | 'paused' | 'stopped';
  created_at: string;
  updated_at: string;
}
