export interface Meeting {
  id: number;
  client_id: number;
  client_name?: string;
  meeting_date: string;
  duration: number;
  meeting_type: 'In-Person' | 'Video Call' | 'Phone Call';
  location?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end?: string;
  backgroundColor?: string;
  extendedProps?: {
    client_id: number;
    meeting_type: string;
    location?: string;
    notes?: string;
  };
}
