import { Component, OnInit, ViewChild, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FullCalendarComponent, FullCalendarModule } from '@fullcalendar/angular';
import { CalendarOptions, EventClickArg, DateSelectArg } from '@fullcalendar/core';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { NavbarComponent } from '../../shared/components/navbar/navbar.component';
import { MeetingService } from './services/meeting.service';
import { ClientService } from '../clients/services/client.service';
import { Meeting } from '../../core/models/meeting.model';
import { NotificationService } from '../../core/services/notification.service';

@Component({
  selector: 'app-calendar',
  standalone: true,
  imports: [CommonModule, FormsModule, FullCalendarModule, NavbarComponent],
  templateUrl: './calendar.component.html',
  styleUrls: ['./calendar.component.scss']
})
export class CalendarComponent implements OnInit {
  @ViewChild('calendar') calendarComponent!: FullCalendarComponent;

  calendarOptions: CalendarOptions = {
    plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay'
    },
    editable: true,
    selectable: true,
    selectMirror: true,
    dayMaxEvents: true,
    weekends: true,
    select: this.handleDateSelect.bind(this),
    eventClick: this.handleEventClick.bind(this),
    eventsSet: this.handleEvents.bind(this),
    eventDrop: this.handleEventDrop.bind(this),
    eventResize: this.handleEventResize.bind(this)
  };

  currentEvents: any[] = [];
  showMeetingModal = false;
  isEditMode = false;
  selectedEvent: any = null;

  meetingForm = {
    id: null as number | null,
    client_id: null as number | null,
    client_name: '',
    meeting_date: '',
    duration: 60,
    location: '',
    meeting_type: 'In-Person' as 'In-Person' | 'Video Call' | 'Phone Call',
    notes: ''
  };

  clients: Array<{ id: number; name: string }> = [];
  loading = true;

  constructor(
    private meetingService: MeetingService,
    private clientService: ClientService,
    private notification: NotificationService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadMeetings();
    this.loadClients();
  }

  loadMeetings(): void {
    this.loading = true;
    this.cdr.detectChanges();
    this.meetingService.getMeetings().subscribe({
      next: (meetings) => {
        console.log('Loaded meetings:', meetings);
        // Convert meetings to events and filter out any null values (invalid dates)
        const events = meetings
          .map(meeting => this.convertMeetingToEvent(meeting))
          .filter(event => event !== null);
        console.log('Converted events:', events);
        this.calendarOptions = {
          ...this.calendarOptions,
          events: events
        };
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: (error) => {
        console.error('Failed to load meetings:', error);
        this.loading = false;
        this.cdr.detectChanges();
        this.notification.error('Failed to load meetings');
      }
    });
  }

  loadClients(): void {
    this.clientService.getClients().subscribe({
      next: (clients) => {
        this.clients = clients.map(c => ({ id: c.id, name: c.name }));
        this.cdr.detectChanges();
      },
      error: () => {
        this.cdr.detectChanges();
        this.notification.error('Failed to load clients');
      }
    });
  }

  convertMeetingToEvent(meeting: Meeting): any | null {
    // Validate meeting date
    if (!meeting.meeting_date) {
      console.warn('Meeting has no date:', meeting);
      return null;
    }

    // Parse the date - handle both YYYY-MM-DD and full ISO formats
    let dateStr = meeting.meeting_date;
    if (typeof dateStr === 'string' && dateStr.length === 10) {
      // If it's just a date (YYYY-MM-DD), add time
      dateStr = `${dateStr}T09:00:00`;
    }

    const meetingDateTime = new Date(dateStr);

    // Check if date is valid
    if (isNaN(meetingDateTime.getTime())) {
      console.warn('Invalid meeting date:', meeting.meeting_date, 'for meeting:', meeting);
      return null;
    }

    const endTime = new Date(meetingDateTime.getTime() + (meeting.duration || 60) * 60000);

    // Better handling for client name
    const clientName = meeting.client_name && meeting.client_name !== 'undefined'
      ? meeting.client_name
      : 'Client Meeting';

    const meetingType = meeting.meeting_type || 'Meeting';

    return {
      id: meeting.id.toString(),
      title: `${clientName} - ${meetingType}`,
      start: meetingDateTime.toISOString(),
      end: endTime.toISOString(),
      backgroundColor: '#C8A870',
      borderColor: '#C8A870',
      extendedProps: {
        clientId: meeting.client_id,
        clientName: meeting.client_name,
        location: meeting.location,
        meetingType: meeting.meeting_type,
        notes: meeting.notes,
        duration: meeting.duration
      }
    };
  }

  handleDateSelect(selectInfo: DateSelectArg): void {
    this.isEditMode = false;
    this.resetMeetingForm();

    const startDate = new Date(selectInfo.start);
    this.meetingForm.meeting_date = startDate.toISOString().split('T')[0];

    this.showMeetingModal = true;
  }

  openNewMeetingModal(): void {
    this.isEditMode = false;
    this.resetMeetingForm();

    // Set today's date as default
    const today = new Date();
    this.meetingForm.meeting_date = today.toISOString().split('T')[0];

    this.showMeetingModal = true;
  }

  handleEventClick(clickInfo: EventClickArg): void {
    this.isEditMode = true;
    this.selectedEvent = clickInfo.event;

    const startDate = new Date(clickInfo.event.start!);
    const props = clickInfo.event.extendedProps;

    this.meetingForm = {
      id: parseInt(clickInfo.event.id),
      client_id: props['clientId'],
      client_name: props['clientName'] || '',
      meeting_date: startDate.toISOString().split('T')[0],
      duration: props['duration'] || 60,
      location: props['location'] || '',
      meeting_type: props['meetingType'] as 'In-Person' | 'Video Call' | 'Phone Call',
      notes: props['notes'] || ''
    };

    this.showMeetingModal = true;
  }

  handleEvents(events: any[]): void {
    this.currentEvents = events;
  }

  handleEventDrop(info: any): void {
    const meeting = {
      ...this.extractMeetingFromEvent(info.event),
      id: parseInt(info.event.id)
    };

    this.meetingService.updateMeeting(meeting.id, meeting).subscribe({
      next: () => {
        this.notification.success('Meeting updated successfully');
      },
      error: () => {
        this.notification.error('Failed to update meeting');
        info.revert();
      }
    });
  }

  handleEventResize(info: any): void {
    const meeting = {
      ...this.extractMeetingFromEvent(info.event),
      id: parseInt(info.event.id)
    };

    this.meetingService.updateMeeting(meeting.id, meeting).subscribe({
      next: () => {
        this.notification.success('Meeting duration updated');
      },
      error: () => {
        this.notification.error('Failed to update meeting');
        info.revert();
      }
    });
  }

  extractMeetingFromEvent(event: any): Partial<Meeting> {
    const startDate = new Date(event.start);
    const endDate = new Date(event.end || event.start);
    const duration = Math.round((endDate.getTime() - startDate.getTime()) / 60000);

    return {
      client_id: event.extendedProps.clientId,
      meeting_date: startDate.toISOString().split('T')[0],
      duration: duration,
      location: event.extendedProps.location || null,
      meeting_type: event.extendedProps.meetingType,
      notes: event.extendedProps.notes || null
    };
  }

  saveMeeting(): void {
    if (!this.meetingForm.client_id) {
      this.notification.error('Please select a client');
      return;
    }

    const meetingData: Partial<Meeting> = {
      client_id: this.meetingForm.client_id,
      meeting_date: this.meetingForm.meeting_date,
      duration: this.meetingForm.duration,
      location: this.meetingForm.location || null,
      meeting_type: this.meetingForm.meeting_type,
      notes: this.meetingForm.notes || null
    };

    if (this.isEditMode && this.meetingForm.id) {
      this.meetingService.updateMeeting(this.meetingForm.id, meetingData).subscribe({
        next: () => {
          this.notification.success('Meeting updated successfully');
          this.loadMeetings();
          this.closeMeetingModal();
        },
        error: () => {
          this.notification.error('Failed to update meeting');
        }
      });
    } else {
      this.meetingService.createMeeting(meetingData).subscribe({
        next: () => {
          this.notification.success('Meeting created successfully');
          this.loadMeetings();
          this.closeMeetingModal();
        },
        error: () => {
          this.notification.error('Failed to create meeting');
        }
      });
    }
  }

  deleteMeeting(): void {
    if (!this.meetingForm.id) return;

    if (confirm('Are you sure you want to delete this meeting?')) {
      this.meetingService.deleteMeeting(this.meetingForm.id).subscribe({
        next: () => {
          this.notification.success('Meeting deleted successfully');
          this.loadMeetings();
          this.closeMeetingModal();
        },
        error: () => {
          this.notification.error('Failed to delete meeting');
        }
      });
    }
  }

  closeMeetingModal(): void {
    this.showMeetingModal = false;
    this.resetMeetingForm();
    this.selectedEvent = null;
  }

  resetMeetingForm(): void {
    this.meetingForm = {
      id: null,
      client_id: null,
      client_name: '',
      meeting_date: '',
      duration: 60,
      location: '',
      meeting_type: 'In-Person',
      notes: ''
    };
  }

  onClientChange(): void {
    const selectedClient = this.clients.find(c => c.id === this.meetingForm.client_id);
    if (selectedClient) {
      this.meetingForm.client_name = selectedClient.name;
    }
  }
}
