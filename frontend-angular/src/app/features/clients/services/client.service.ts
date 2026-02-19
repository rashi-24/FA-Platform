import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Client, ClientDetail, AIPortfolioAnalysis } from '../../../core/models/client.model';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ClientService {
  private readonly API_BASE = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  getClients(): Observable<Client[]> {
    return this.http.get<Client[]>(`${this.API_BASE}/clients`);
  }

  getClient(id: number): Observable<ClientDetail> {
    return this.http.get<ClientDetail>(`${this.API_BASE}/clients/${id}`);
  }

  createClient(client: Partial<Client>): Observable<Client> {
    return this.http.post<Client>(`${this.API_BASE}/clients`, client);
  }

  updateClient(id: number, client: Partial<Client>): Observable<Client> {
    return this.http.put<Client>(`${this.API_BASE}/clients/${id}`, client);
  }

  deleteClient(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API_BASE}/clients/${id}`);
  }

  getAIPortfolioAnalysis(id: number): Observable<AIPortfolioAnalysis> {
    return this.http.get<AIPortfolioAnalysis>(`${this.API_BASE}/clients/${id}/ai-overview`);
  }
}
