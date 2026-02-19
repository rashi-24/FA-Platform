import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { NavbarComponent } from '../../../shared/components/navbar/navbar.component';
import { ClientService } from '../services/client.service';
import { Client } from '../../../core/models/client.model';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-client-list',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, NavbarComponent],
  templateUrl: './client-list.component.html',
  styleUrls: ['./client-list.component.scss']
})
export class ClientListComponent implements OnInit {
  clients: Client[] = [];
  filteredClients: Client[] = [];
  searchTerm: string = '';
  activeFilter: 'all' | 'recent' | 'no-contact' = 'all';
  loading = true;
  showAddModal = false;

  newClient = {
    name: '',
    phone: '',
    email: '',
    address: '',
    notes: ''
  };

  constructor(
    private clientService: ClientService,
    private notification: NotificationService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadClients();
  }

  loadClients(): void {
    this.loading = true;
    this.clientService.getClients().subscribe({
      next: (clients) => {
        this.clients = clients;
        this.applyFilters();
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.cdr.detectChanges();
        this.notification.error('Failed to load clients');
      }
    });
  }

  applyFilters(): void {
    let filtered = [...this.clients];

    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      filtered = filtered.filter(client =>
        client.name.toLowerCase().includes(term) ||
        client.phone.includes(term) ||
        (client.email && client.email.toLowerCase().includes(term))
      );
    }

    if (this.activeFilter === 'recent') {
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      filtered = filtered.filter(client =>
        client.last_contact_date && new Date(client.last_contact_date) >= thirtyDaysAgo
      );
    } else if (this.activeFilter === 'no-contact') {
      const sixtyDaysAgo = new Date();
      sixtyDaysAgo.setDate(sixtyDaysAgo.getDate() - 60);
      filtered = filtered.filter(client =>
        !client.last_contact_date || new Date(client.last_contact_date) < sixtyDaysAgo
      );
    }

    this.filteredClients = filtered;
  }

  onSearchChange(): void {
    this.applyFilters();
  }

  setFilter(filter: 'all' | 'recent' | 'no-contact'): void {
    this.activeFilter = filter;
    this.applyFilters();
  }

  openAddModal(): void {
    this.showAddModal = true;
    this.resetNewClient();
  }

  closeAddModal(): void {
    this.showAddModal = false;
    this.resetNewClient();
  }

  resetNewClient(): void {
    this.newClient = {
      name: '',
      phone: '',
      email: '',
      address: '',
      notes: ''
    };
  }

  addClient(): void {
    const cleanPhone = this.newClient.phone.replace(/[\s\-\(\)]/g, '');

    const clientData = {
      ...this.newClient,
      phone: cleanPhone,
      email: this.newClient.email || null,
      address: this.newClient.address || null,
      notes: this.newClient.notes || null
    };

    this.clientService.createClient(clientData).subscribe({
      next: (client) => {
        this.notification.success('Client added successfully!');
        this.clients.push(client);
        this.applyFilters();
        this.closeAddModal();
      },
      error: (error) => {
        this.notification.error(error.error?.detail || 'Failed to add client');
      }
    });
  }

  deleteClient(client: Client): void {
    if (!confirm(`Delete ${client.name}? This will also delete all associated policies, SIPs, and meetings.`)) {
      return;
    }

    this.clientService.deleteClient(client.id).subscribe({
      next: () => {
        this.notification.success('Client deleted successfully');
        this.clients = this.clients.filter(c => c.id !== client.id);
        this.applyFilters();
      },
      error: () => {
        this.notification.error('Failed to delete client');
      }
    });
  }

  formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  }
}
