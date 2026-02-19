import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { SIP } from '../../../core/models/sip.model';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SIPService {
  private readonly API_BASE = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getSIPs(): Observable<SIP[]> {
    return this.http.get<SIP[]>(`${this.API_BASE}/sips`);
  }

  createSIP(sip: Partial<SIP>): Observable<SIP> {
    return this.http.post<SIP>(`${this.API_BASE}/sips`, sip);
  }

  updateSIP(id: number, sip: Partial<SIP>): Observable<SIP> {
    return this.http.put<SIP>(`${this.API_BASE}/sips/${id}`, sip);
  }

  deleteSIP(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API_BASE}/sips/${id}`);
  }
}
