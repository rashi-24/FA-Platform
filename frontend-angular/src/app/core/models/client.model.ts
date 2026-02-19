import { Policy } from './policy.model';
import { SIP } from './sip.model';
import { Meeting } from './meeting.model';

export interface Client {
  id: number;
  name: string;
  phone: string;
  email?: string | null;
  address?: string | null;
  notes?: string | null;
  last_contact_date?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClientDetail extends Client {
  policies: Policy[];
  sips: SIP[];
  meetings: Meeting[];
}

export interface AIPortfolioAnalysis {
  portfolio_score: number;
  risk_level: 'Low' | 'Medium' | 'High';
  risk_factors: string[];
  recommendations: string[];
  strengths: string[];
  concerns: string[];
  summary: string;
}
