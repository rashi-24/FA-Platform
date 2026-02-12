/**
 * Calendar Page JavaScript
 * FullCalendar integration for meeting management
 */

const API_BASE_URL = 'http://localhost:8000';
let calendar;
let currentMeetingId = null;

// Check authentication
function checkAuth() {
    const token = localStorage.getItem('access_token');
    const expiresAt = localStorage.getItem('token_expires_at');

    if (!token || !expiresAt || Date.now() >= parseInt(expiresAt)) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    };
}

// Initialize calendar
document.addEventListener('DOMContentLoaded', function() {
    if (!checkAuth()) return;

    const calendarEl = document.getElementById('calendar');

    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        events: async function(info, successCallback, failureCallback) {
            try {
                const response = await fetch(`${API_BASE_URL}/api/meetings/calendar`, {
                    headers: getAuthHeaders()
                });

                if (response.ok) {
                    const data = await response.json();
                    successCallback(data.events);
                } else if (response.status === 401) {
                    window.location.href = 'login.html';
                } else {
                    failureCallback(new Error('Failed to load events'));
                }
            } catch (error) {
                console.error('Error loading events:', error);
                failureCallback(error);
            }
        },
        eventClick: function(info) {
            viewMeetingDetails(info.event);
        },
        dateClick: function(info) {
            showCreateMeetingForm(info.date);
        },
        editable: false,
        selectable: true,
        selectMirror: true,
        dayMaxEvents: true
    });

    calendar.render();
});

// View meeting details
function viewMeetingDetails(event) {
    currentMeetingId = event.id;

    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = `
        <div>
            <p><strong>Client:</strong> ${event.extendedProps.client_name}</p>
            <p><strong>Date:</strong> ${event.start.toLocaleString()}</p>
            <p><strong>Duration:</strong> ${Math.floor((event.end - event.start) / 60000)} minutes</p>
            <p><strong>Location:</strong> ${event.extendedProps.location || 'Not specified'}</p>
            <p><strong>Type:</strong> ${event.extendedProps.meeting_type}</p>

            <div style="margin-top: 20px; display: flex; gap: 10px;">
                <button class="btn btn-primary" onclick="editMeeting()">Edit</button>
                <button class="btn btn-danger" onclick="deleteMeeting()">Delete</button>
            </div>
        </div>
    `;

    document.getElementById('modal-title').textContent = 'Meeting Details';
    document.getElementById('meetingModal').style.display = 'block';
}

// Show create meeting form
async function showCreateMeetingForm(date) {
    // Fetch clients for dropdown
    const response = await fetch(`${API_BASE_URL}/api/clients`, {
        headers: getAuthHeaders()
    });

    if (!response.ok) {
        alert('Failed to load clients');
        return;
    }

    const clients = await response.json();

    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = `
        <form id="create-meeting-form" onsubmit="createMeeting(event)">
            <div class="form-group">
                <label for="client_id">Client *</label>
                <select id="client_id" required>
                    <option value="">Select a client</option>
                    ${clients.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
                </select>
            </div>

            <div class="form-group">
                <label for="meeting_date">Date & Time *</label>
                <input type="datetime-local" id="meeting_date" required
                       value="${date.toISOString().slice(0, 16)}">
            </div>

            <div class="form-group">
                <label for="duration">Duration (minutes) *</label>
                <input type="number" id="duration" value="60" min="15" step="15" required>
            </div>

            <div class="form-group">
                <label for="meeting_type">Type *</label>
                <select id="meeting_type" required>
                    <option value="in-person">In-Person</option>
                    <option value="video">Video Call</option>
                    <option value="phone">Phone Call</option>
                </select>
            </div>

            <div class="form-group">
                <label for="location">Location / Link</label>
                <input type="text" id="location" placeholder="Office address or video call link">
            </div>

            <div class="form-group">
                <label for="notes">Notes *</label>
                <textarea id="notes" required placeholder="Meeting agenda and notes..."></textarea>
            </div>

            <button type="submit" class="btn btn-primary">Create Meeting</button>
        </form>
    `;

    document.getElementById('modal-title').textContent = 'Create New Meeting';
    document.getElementById('meetingModal').style.display = 'block';
}

// Create meeting
async function createMeeting(event) {
    event.preventDefault();

    const formData = {
        client_id: parseInt(document.getElementById('client_id').value),
        meeting_date: new Date(document.getElementById('meeting_date').value).toISOString(),
        duration: parseInt(document.getElementById('duration').value),
        meeting_type: document.getElementById('meeting_type').value,
        location: document.getElementById('location').value || null,
        notes: document.getElementById('notes').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/meetings`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            alert('Meeting created successfully!');
            closeModal();
            calendar.refetchEvents();  // Reload events
        } else {
            const error = await response.json();
            alert('Failed to create meeting: ' + (error.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error creating meeting:', error);
        alert('Network error. Please try again.');
    }
}

// Delete meeting
async function deleteMeeting() {
    if (!confirm('Are you sure you want to delete this meeting?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/meetings/${currentMeetingId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (response.ok) {
            alert('Meeting deleted successfully!');
            closeModal();
            calendar.refetchEvents();
        } else {
            alert('Failed to delete meeting');
        }
    } catch (error) {
        console.error('Error deleting meeting:', error);
        alert('Network error. Please try again.');
    }
}

// Edit meeting (simplified - just redirect to create form with prefilled data)
function editMeeting() {
    alert('Edit functionality: Update the meeting details and save');
    // In production, load meeting data and show editable form
}

// Close modal
function closeModal() {
    document.getElementById('meetingModal').style.display = 'none';
    currentMeetingId = null;
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('meetingModal');
    if (event.target === modal) {
        closeModal();
    }
}
