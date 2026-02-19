import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private readonly API_BASE = '/api';
  private readonly STORAGE_KEY = 'fa_platform_chat_history';

  private messagesSubject = new BehaviorSubject<ChatMessage[]>([]);
  public messages$ = this.messagesSubject.asObservable();

  constructor(private http: HttpClient) {
    this.loadMessagesFromStorage();
  }

  private loadMessagesFromStorage(): void {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        const messages = JSON.parse(stored);
        // Convert timestamp strings back to Date objects
        messages.forEach((msg: ChatMessage) => {
          msg.timestamp = new Date(msg.timestamp);
        });
        this.messagesSubject.next(messages);
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  }

  private saveMessagesToStorage(messages: ChatMessage[]): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(messages));
    } catch (error) {
      console.error('Failed to save chat history:', error);
    }
  }

  sendMessage(content: string): Observable<{ response: string }> {
    // Add user message
    const userMessage: ChatMessage = {
      id: this.generateId(),
      role: 'user',
      content,
      timestamp: new Date()
    };

    const currentMessages = this.messagesSubject.value;
    const updatedMessages = [...currentMessages, userMessage];
    this.messagesSubject.next(updatedMessages);
    this.saveMessagesToStorage(updatedMessages);

    // Send to API
    return this.http.post<{ response: string }>(`${this.API_BASE}/chat`, {
      message: content,
      conversation_history: currentMessages.slice(-10).map(m => ({
        role: m.role,
        content: m.content
      }))
    }).pipe(
      tap(response => {
        // Add assistant response
        const assistantMessage: ChatMessage = {
          id: this.generateId(),
          role: 'assistant',
          content: response.response,
          timestamp: new Date()
        };

        const withResponse = [...updatedMessages, assistantMessage];
        this.messagesSubject.next(withResponse);
        this.saveMessagesToStorage(withResponse);
      })
    );
  }

  clearHistory(): void {
    this.messagesSubject.next([]);
    localStorage.removeItem(this.STORAGE_KEY);
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Quick action methods
  async getClientSummary(clientId: number): Promise<void> {
    const message = `Give me a summary of client ${clientId}'s portfolio`;
    this.sendMessage(message).subscribe();
  }

  async analyzeTrends(): Promise<void> {
    const message = "What are the current trends in my client portfolios?";
    this.sendMessage(message).subscribe();
  }

  async getRecommendations(): Promise<void> {
    const message = "What actions should I prioritize this week?";
    this.sendMessage(message).subscribe();
  }
}
