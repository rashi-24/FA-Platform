// API Base URL
const API_BASE = 'http://localhost:8000/api';

// Global state
let currentData = {
    clients: [],
    policies: [],
    sips: [],
    reminders: [],
    approvals: []
};

// ==================== Authentication ====================

function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
}

function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token && !window.location.pathname.includes('login.html')) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_expires_at');
    window.location.href = 'login.html';
}

async function loadUserInfo() {
    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Failed to fetch user info');
        }

        const user = await response.json();

        // Update UI with user info
        const userNameEl = document.getElementById('user-name');
        const userEmailEl = document.getElementById('user-email');

        if (userNameEl) userNameEl.textContent = user.full_name || user.username;
        if (userEmailEl) userEmailEl.textContent = user.email;
    } catch (error) {
        console.error('Error loading user info:', error);
        // If auth fails, redirect to login
        if (error.message.includes('401') || error.message.includes('Unauthorized')) {
            logout();
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (!checkAuth()) return;

    // Load user info
    loadUserInfo();

    // Load all dashboard data
    loadDashboard();
    loadDailyInsights();
    loadUrgentReminders();
    loadCalendarWidget();
    loadPolicies();

    // Initialize AI chat widget
    if (typeof initAIChat === 'function') {
        initAIChat();
    }
});

// ==================== Dashboard ====================

async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/dashboard`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();

        document.getElementById('total-clients').textContent = data.total_clients;
        document.getElementById('total-policies').textContent = data.total_policies;
        document.getElementById('total-sips').textContent = data.total_active_sips;
        document.getElementById('total-aum').textContent = formatCurrency(data.total_aum);
        document.getElementById('upcoming-renewals').textContent = data.upcoming_renewals_30d;
        document.getElementById('upcoming-sips').textContent = data.upcoming_sips_this_month;
        document.getElementById('pending-approvals').textContent = data.pending_approvals;
        document.getElementById('recent-meetings').textContent = data.recent_meetings;
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard data');
    }
}

// ==================== Capital Companion ====================

async function loadDailyInsights() {
    const container = document.getElementById('daily-insights');
    try {
        const response = await fetch(`${API_BASE}/agents/capital-companion/daily`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();

        if (data.insights && data.insights.length > 0) {
            const html = data.insights.map(insight => `
                <div class="insight-card insight-${insight.priority}">
                    <div class="insight-icon">${insight.icon}</div>
                    <div class="insight-content">
                        <h4>${insight.title}</h4>
                        <p>${insight.message}</p>
                    </div>
                </div>
            `).join('');
            container.innerHTML = html;
        } else {
            container.innerHTML = '<div class="empty-state"><p>No insights available at the moment. Check back later!</p></div>';
        }
    } catch (error) {
        console.error('Error loading daily insights:', error);
        container.innerHTML = '<div class="error-state"><p>Failed to load daily insights</p></div>';
    }
}

async function loadUrgentReminders() {
    const container = document.getElementById('urgent-reminders-list');
    try {
        const response = await fetch(`${API_BASE}/reminders?days_ahead=7&limit=5`, {
            headers: getAuthHeaders()
        });
        const reminders = await response.json();

        if (reminders.length > 0) {
            const html = reminders.map(reminder => `
                <div class="widget-item urgency-${reminder.urgency}">
                    <div class="widget-item-header">
                        <span class="reminder-type">${reminder.reminder_type.replace('_', ' ').toUpperCase()}</span>
                        <span class="urgency-badge urgency-${reminder.urgency}">${reminder.urgency}</span>
                    </div>
                    <div class="widget-item-content">
                        ${reminder.message.split('\n')[0]}
                    </div>
                    <div class="widget-item-footer">
                        <span>Due: ${formatDate(reminder.due_date)}</span>
                    </div>
                </div>
            `).join('');
            container.innerHTML = html;
        } else {
            container.innerHTML = '<div class="empty-state"><p>No urgent reminders 🎉</p></div>';
        }
    } catch (error) {
        console.error('Error loading urgent reminders:', error);
        container.innerHTML = '<div class="error-state"><p>Failed to load reminders</p></div>';
    }
}

async function loadCalendarWidget() {
    const container = document.getElementById('calendar-widget-list');
    try {
        const response = await fetch(`${API_BASE}/meetings/calendar`, {
            headers: getAuthHeaders()
        });
        const meetings = await response.json();

        // Get upcoming meetings (next 7 days)
        const now = new Date();
        const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
        const upcomingMeetings = meetings.filter(meeting => {
            const meetingDate = new Date(meeting.start);
            return meetingDate >= now && meetingDate <= nextWeek;
        }).slice(0, 5); // Limit to 5

        if (upcomingMeetings.length > 0) {
            const html = upcomingMeetings.map(meeting => `
                <div class="widget-item">
                    <div class="widget-item-header">
                        <span class="meeting-client">${meeting.title}</span>
                    </div>
                    <div class="widget-item-content">
                        ${meeting.location || 'No location specified'}
                    </div>
                    <div class="widget-item-footer">
                        <span>📅 ${formatDateTime(meeting.start)}</span>
                    </div>
                </div>
            `).join('');
            container.innerHTML = html;
        } else {
            container.innerHTML = '<div class="empty-state"><p>No upcoming meetings</p></div>';
        }
    } catch (error) {
        console.error('Error loading calendar widget:', error);
        container.innerHTML = '<div class="error-state"><p>Failed to load meetings</p></div>';
    }
}

// ==================== Tab Navigation ====================

function showTab(tabName) {
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Remove active class from all buttons
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
    
    // Load data for the tab
    switch(tabName) {
        case 'clients':
            loadClients();
            break;
        case 'policies':
            loadPolicies();
            break;
        case 'sips':
            loadSIPs();
            break;
        case 'reminders':
            loadReminders();
            break;
        case 'approvals':
            loadApprovals();
            break;
    }
}

// ==================== Clients ====================

async function loadClients() {
    try {
        const response = await fetch(`${API_BASE}/clients`, {
            headers: getAuthHeaders()
        });
        currentData.clients = await response.json();
        renderClients(currentData.clients);
    } catch (error) {
        console.error('Error loading clients:', error);
        showError('Failed to load clients');
    }
}

function renderClients(clients) {
    const container = document.getElementById('clients-list');

    if (clients.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No clients found</h3><p>Add your first client to get started</p></div>';
        return;
    }

    const html = `
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Phone</th>
                    <th>Email</th>
                    <th>Created</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${clients.map(client => `
                    <tr>
                        <td><strong>${client.name}</strong></td>
                        <td>${client.phone}</td>
                        <td>${client.email || '-'}</td>
                        <td>${formatDate(client.created_at)}</td>
                        <td>
                            <button onclick="viewClient(${client.id})" style="margin-right: 5px;">View</button>
                            <button onclick="deleteClient(${client.id}, '${client.name}')" style="background: #e53e3e;">Delete</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

function searchClients() {
    const searchTerm = document.getElementById('client-search').value.toLowerCase();
    const filtered = currentData.clients.filter(client =>
        client.name.toLowerCase().includes(searchTerm) ||
        client.phone.includes(searchTerm) ||
        (client.email && client.email.toLowerCase().includes(searchTerm))
    );
    renderClients(filtered);
}

function searchPolicies() {
    const searchTerm = document.getElementById('policy-search').value.toLowerCase();
    const filtered = currentData.policies.filter(policy =>
        (policy.client_name && policy.client_name.toLowerCase().includes(searchTerm)) ||
        policy.policy_number.toLowerCase().includes(searchTerm) ||
        policy.provider.toLowerCase().includes(searchTerm) ||
        policy.policy_type.toLowerCase().includes(searchTerm)
    );
    renderPolicies(filtered);
}

function searchSIPs() {
    const searchTerm = document.getElementById('sip-search').value.toLowerCase();
    const filtered = currentData.sips.filter(sip =>
        (sip.client_name && sip.client_name.toLowerCase().includes(searchTerm)) ||
        sip.fund_name.toLowerCase().includes(searchTerm) ||
        (sip.folio_number && sip.folio_number.toLowerCase().includes(searchTerm))
    );
    renderSIPs(filtered);
}

// ==================== Policies ====================

async function loadPolicies() {
    try {
        const response = await fetch(`${API_BASE}/policies`, {
            headers: getAuthHeaders()
        });
        currentData.policies = await response.json();
        renderPolicies(currentData.policies);
    } catch (error) {
        console.error('Error loading policies:', error);
    }
}

function renderPolicies(policies) {
    const container = document.getElementById('policies-list');

    if (policies.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No policies found</h3></div>';
        return;
    }

    const html = `
        <table>
            <thead>
                <tr>
                    <th>Client Name</th>
                    <th>Policy Number</th>
                    <th>Provider</th>
                    <th>Type</th>
                    <th>Premium</th>
                    <th>Renewal Date</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${policies.map(policy => `
                    <tr>
                        <td><strong>${policy.client_name || 'N/A'}</strong></td>
                        <td>${policy.policy_number}</td>
                        <td>${policy.provider}</td>
                        <td>${policy.policy_type}</td>
                        <td>₹${formatNumber(policy.premium_amount)}</td>
                        <td>${formatDate(policy.renewal_date)}</td>
                        <td><span class="badge badge-${getStatusColor(policy.status)}">${policy.status.toUpperCase()}</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

// ==================== SIPs ====================

async function loadSIPs() {
    try {
        const response = await fetch(`${API_BASE}/sips`, {
            headers: getAuthHeaders()
        });
        currentData.sips = await response.json();
        renderSIPs(currentData.sips);
    } catch (error) {
        console.error('Error loading SIPs:', error);
    }
}

function renderSIPs(sips) {
    const container = document.getElementById('sips-list');

    if (sips.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No SIPs found</h3></div>';
        return;
    }

    const html = `
        <table>
            <thead>
                <tr>
                    <th>Client Name</th>
                    <th>Fund Name</th>
                    <th>Folio Number</th>
                    <th>Amount</th>
                    <th>SIP Day</th>
                    <th>Start Date</th>
                    <th>Frequency</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${sips.map(sip => `
                    <tr>
                        <td><strong>${sip.client_name || 'N/A'}</strong></td>
                        <td>${sip.fund_name}</td>
                        <td>${sip.folio_number || '-'}</td>
                        <td>₹${formatNumber(sip.amount)}</td>
                        <td>${sip.sip_day}</td>
                        <td>${formatDate(sip.start_date)}</td>
                        <td>${sip.frequency.toUpperCase()}</td>
                        <td><span class="badge badge-${getStatusColor(sip.status)}">${sip.status.toUpperCase()}</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

// ==================== Reminders ====================

async function loadReminders() {
    try {
        const response = await fetch(`${API_BASE}/reminders?days_ahead=30`, {
            headers: getAuthHeaders()
        });
        currentData.reminders = await response.json();
        renderReminders(currentData.reminders);
    } catch (error) {
        console.error('Error loading reminders:', error);
    }
}

function renderReminders(reminders) {
    const container = document.getElementById('reminders-list');
    
    if (reminders.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No upcoming reminders</h3><p>All caught up! 🎉</p></div>';
        return;
    }
    
    const html = `
        <table>
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Message</th>
                    <th>Due Date</th>
                    <th>Urgency</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${reminders.map(reminder => `
                    <tr>
                        <td>${reminder.reminder_type.replace('_', ' ').toUpperCase()}</td>
                        <td>${reminder.message.split('\n')[0]}</td>
                        <td>${formatDate(reminder.due_date)}</td>
                        <td><span class="urgency-${reminder.urgency}">${reminder.urgency.toUpperCase()}</span></td>
                        <td>
                            <button onclick="dismissReminder(${reminder.id})">Dismiss</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
}

async function dismissReminder(reminderId) {
    try {
        await fetch(`${API_BASE}/reminders/${reminderId}/dismiss`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        showSuccess('Reminder dismissed');
        loadReminders();
        loadDashboard();
    } catch (error) {
        showError('Failed to dismiss reminder');
    }
}

// ==================== Approvals ====================

async function loadApprovals() {
    try {
        const response = await fetch(`${API_BASE}/approvals`, {
            headers: getAuthHeaders()
        });
        currentData.approvals = await response.json();
        renderApprovals(currentData.approvals);
    } catch (error) {
        console.error('Error loading approvals:', error);
    }
}

function renderApprovals(approvals) {
    const container = document.getElementById('approvals-list');
    
    if (approvals.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No pending approvals</h3><p>All AI actions have been reviewed</p></div>';
        return;
    }
    
    const html = `
        <table>
            <thead>
                <tr>
                    <th>Job Type</th>
                    <th>Entity</th>
                    <th>Action</th>
                    <th>Confidence</th>
                    <th>Reasoning</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${approvals.map(approval => `
                    <tr>
                        <td>${approval.job_type}</td>
                        <td>${approval.entity_type}</td>
                        <td><span class="badge badge-info">${approval.action_type}</span></td>
                        <td>${approval.confidence_score ? (approval.confidence_score * 100).toFixed(0) + '%' : '-'}</td>
                        <td>${approval.agent_reasoning || '-'}</td>
                        <td>
                            <button onclick="reviewApproval(${approval.id}, true)">✓ Approve</button>
                            <button onclick="reviewApproval(${approval.id}, false)" style="background: #e53e3e;">✗ Reject</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
}

async function reviewApproval(approvalId, approved) {
    try {
        await fetch(`${API_BASE}/approvals/${approvalId}/review`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ approval_id: approvalId, approved })
        });

        showSuccess(approved ? 'Action approved' : 'Action rejected');
        loadApprovals();
        loadDashboard();
    } catch (error) {
        showError('Failed to review approval');
    }
}

// ==================== AI Agents ====================

async function runReminderAgent() {
    try {
        showLoading('Running Reminder Agent...');
        const response = await fetch(`${API_BASE}/agents/reminder/run`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        const result = await response.json();

        showSuccess(`Reminder Agent completed! Generated ${result.data.total} reminders`);
        document.getElementById('reminder-agent-status').textContent = new Date().toLocaleString();

        loadReminders();
        loadDashboard();
    } catch (error) {
        showError('Failed to run Reminder Agent');
    }
}

async function uploadExcel() {
    const fileInput = document.getElementById('excel-upload');
    const file = fileInput.files[0];

    if (!file) {
        showError('Please select a file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        showLoading('Processing Excel file...');
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE}/agents/excel/upload`, {
            method: 'POST',
            headers: {
                'Authorization': token ? `Bearer ${token}` : ''
            },
            body: formData
        });

        const result = await response.json();
        showSuccess(`Excel processed! ${result.proposed_actions.length} actions proposed`);

        // Reload approvals
        loadApprovals();
        loadDashboard();
    } catch (error) {
        showError('Failed to process Excel file');
    }
}

// ==================== Utility Functions ====================

function formatNumber(num) {
    return num.toLocaleString('en-IN');
}

function formatCurrency(num) {
    // Format large numbers in Indian notation (Lakhs/Crores)
    if (num >= 10000000) { // 1 Crore
        return `₹${(num / 10000000).toFixed(2)}Cr`;
    } else if (num >= 100000) { // 1 Lakh
        return `₹${(num / 100000).toFixed(2)}L`;
    } else if (num >= 1000) {
        return `₹${(num / 1000).toFixed(1)}K`;
    } else {
        return `₹${num.toLocaleString('en-IN')}`;
    }
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getStatusColor(status) {
    const colors = {
        'active': 'success',
        'lapsed': 'danger',
        'paused': 'warning',
        'stopped': 'danger',
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger'
    };
    return colors[status] || 'info';
}

function showSuccess(message) {
    alert(`✓ ${message}`);
}

function showError(message) {
    alert(`✗ Error: ${message}`);
}

function showLoading(message) {
    // Simple implementation - could be enhanced with a proper loading overlay
    console.log(`Loading: ${message}`);
}

function showModal(content) {
    document.getElementById('modal-body').innerHTML = content;
    document.getElementById('modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('modal').style.display = 'none';
}

// ==================== Form Handlers ====================

function showAddClientForm() {
    const form = `
        <h2>Add New Client</h2>
        <form onsubmit="submitClientForm(event)">
            <div class="form-group">
                <label>Name *</label>
                <input type="text" name="name" required>
            </div>
            <div class="form-group">
                <label>Phone * <small>(10-15 digits, e.g., 9876543210)</small></label>
                <input type="tel" name="phone" required placeholder="9876543210" pattern="[0-9\\+\\s\\-\\(\\)]{10,20}">
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" name="email">
            </div>
            <div class="form-group">
                <label>Address</label>
                <textarea name="address" rows="3"></textarea>
            </div>
            <div class="form-group">
                <label>Notes</label>
                <textarea name="notes" rows="3"></textarea>
            </div>
            <button type="submit">Add Client</button>
        </form>
    `;
    showModal(form);
}

async function submitClientForm(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);

    // Clean phone number - remove spaces, dashes, parentheses
    if (data.phone) {
        data.phone = data.phone.replace(/[\s\-\(\)]/g, '');
    }

    try {
        const response = await fetch(`${API_BASE}/clients`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Validation failed');
        }

        closeModal();
        showSuccess('Client added successfully');
        loadClients();
        loadDashboard();
    } catch (error) {
        showError(error.message || 'Failed to add client');
    }
}

function viewClient(clientId) {
    // Navigate to dedicated client detail page
    window.location.href = `client-detail.html?id=${clientId}`;
}

async function deleteClient(clientId, clientName) {
    // Confirm deletion
    const confirmed = confirm(
        `Are you sure you want to delete "${clientName}"?\n\n` +
        `This will also delete:\n` +
        `• All associated policies\n` +
        `• All associated SIPs\n` +
        `• All meeting records\n\n` +
        `This action cannot be undone.`
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/clients/${clientId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error('Failed to delete client');
        }

        showSuccess(`Client "${clientName}" deleted successfully`);
        loadClients();
        loadDashboard();
    } catch (error) {
        showError('Failed to delete client: ' + error.message);
        console.error('Error:', error);
    }
}

function showAddPolicyForm() {
    alert('Add Policy form - Coming soon!');
}

function showAddSIPForm() {
    alert('Add SIP form - Coming soon!');
}
