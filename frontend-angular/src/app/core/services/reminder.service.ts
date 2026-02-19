import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Reminder } from '../models/reminder.model';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ReminderService {
  private readonly API_BASE = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getReminders(daysAhead: number = 30, limit?: number): Observable<Reminder[]> {
    let url = `${this.API_BASE}/reminders?days_ahead=${daysAhead}`;
    if (limit) {
      url += `&limit=${limit}`;
    }
    return this.http.get<Reminder[]>(url);
  }

  dismissReminder(id: number): Observable<void> {
    return this.http.post<void>(`${this.API_BASE}/reminders/${id}/dismiss`, {});
  }

  runReminderAgent(): Observable<any> {
    return this.http.post(`${this.API_BASE}/agents/reminder/run`, {});
  }
}
