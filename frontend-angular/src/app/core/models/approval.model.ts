export interface Approval {
  id: number;
  job_type: string;
  entity_type: string;
  entity_id?: number | null;
  action: string;
  data: Record<string, any>;
  confidence: number;
  reasoning: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  updated_at: string;
}

export interface ApprovalReview {
  approval_id: number;
  approved: boolean;
}
