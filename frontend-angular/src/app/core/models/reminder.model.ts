export interface Reminder {
  id: number;
  reminder_type: 'policy_renewal' | 'sip_due' | 'meeting_follow_up' | 'other';
  message: string;
  due_date: string;
  urgency: 'low' | 'medium' | 'high';
  is_dismissed: boolean;
  created_at: string;
  updated_at: string;
}
