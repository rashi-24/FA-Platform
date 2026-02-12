// API Base URL
const API_BASE = 'http://localhost:8000/api';

// Get client ID from URL parameters
const urlParams = new URLSearchParams(window.location.search);
const clientId = urlParams.get('id');

// Chart instances
let policyChart, sipChart, premiumChart, sipAmountChart;

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

// Load client data on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (!checkAuth()) return;

    if (!clientId) {
        alert('No client ID specified');
        window.location.href = 'index.html';
        return;
    }

    loadClientData();
    loadAIOverview();

    // Initialize AI chat widget
    if (typeof initAIChat === 'function') {
        initAIChat();
    }
});

async function loadClientData() {
    try {
        // Fetch client details with policies and SIPs
        const response = await fetch(`${API_BASE}/clients/${clientId}`, {
            headers: getAuthHeaders()
        });
        const client = await response.json();

        // Display client information
        displayClientInfo(client);

        // Calculate summary statistics
        calculateSummaryStats(client);

        // Render charts
        renderCharts(client);

        // Render tables
        renderPoliciesTable(client.policies || []);
        renderSIPsTable(client.sips || []);

    } catch (error) {
        console.error('Error loading client data:', error);
        alert('Failed to load client data');
    }
}

// ==================== AI Overview ====================

async function loadAIOverview() {
    const container = document.getElementById('ai-overview');
    try {
        const response = await fetch(`${API_BASE}/clients/${clientId}/ai-overview`, {
            headers: getAuthHeaders()
        });
        const data = await response.json();

        if (data.overview) {
            const overview = data.overview;
            const html = `
                <div class="ai-overview-grid">
                    <div class="ai-score-card score-${getScoreLevel(overview.portfolio_score)}">
                        <div class="score-circle">
                            <div class="score-value">${overview.portfolio_score}</div>
                            <div class="score-label">Portfolio Score</div>
                        </div>
                    </div>

                    <div class="ai-insight-card">
                        <h4>📊 Risk Assessment</h4>
                        <div class="risk-badge risk-${overview.risk_level.toLowerCase()}">
                            ${overview.risk_level.toUpperCase()}
                        </div>
                        <p class="insight-text">${overview.risk_factors.join(', ')}</p>
                    </div>

                    <div class="ai-insight-card">
                        <h4>💡 Key Recommendations</h4>
                        <ul class="recommendation-list">
                            ${overview.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="ai-insight-card">
                        <h4>📈 Strengths</h4>
                        <ul class="strength-list">
                            ${overview.strengths.map(strength => `<li>✓ ${strength}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="ai-insight-card">
                        <h4>⚠️ Areas of Concern</h4>
                        <ul class="concern-list">
                            ${overview.concerns.map(concern => `<li>⚠ ${concern}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="ai-insight-card summary-card">
                        <h4>📝 Summary</h4>
                        <p class="summary-text">${overview.summary}</p>
                    </div>
                </div>
            `;
            container.innerHTML = html;
        } else {
            container.innerHTML = '<div class="empty-state"><p>No AI analysis available</p></div>';
        }
    } catch (error) {
        console.error('Error loading AI overview:', error);
        container.innerHTML = '<div class="error-state"><p>Failed to load AI analysis</p></div>';
    }
}

function getScoreLevel(score) {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'fair';
    return 'poor';
}

function displayClientInfo(client) {
    document.getElementById('client-name').textContent = `🏦 ${client.name}`;
    document.getElementById('client-info').textContent = `Client ID: ${client.id}`;
    document.getElementById('phone').textContent = client.phone;
    document.getElementById('email').textContent = client.email || 'N/A';
    document.getElementById('address').textContent = client.address || 'N/A';
    document.getElementById('member-since').textContent = formatDate(client.created_at);
    document.getElementById('notes').textContent = client.notes || 'No notes';
}

function calculateSummaryStats(client) {
    const policies = client.policies || [];
    const sips = client.sips || [];

    // Count active policies
    const activePolicies = policies.filter(p => p.status === 'active').length;
    document.getElementById('total-policies').textContent = activePolicies;

    // Count active SIPs
    const activeSips = sips.filter(s => s.status === 'active').length;
    document.getElementById('total-sips').textContent = activeSips;

    // Calculate total annual premium
    const totalPremium = policies
        .filter(p => p.status === 'active')
        .reduce((sum, p) => {
            const multiplier = {
                'monthly': 12,
                'quarterly': 4,
                'half-yearly': 2,
                'yearly': 1
            }[p.premium_frequency] || 1;
            return sum + (p.premium_amount * multiplier);
        }, 0);
    document.getElementById('total-premium').textContent = `₹${formatNumber(totalPremium)}`;

    // Calculate total monthly SIP amount
    const totalSipAmount = sips
        .filter(s => s.status === 'active')
        .reduce((sum, s) => sum + s.amount, 0);
    document.getElementById('total-sip-amount').textContent = `₹${formatNumber(totalSipAmount)}`;
}

function renderCharts(client) {
    const policies = client.policies || [];
    const sips = client.sips || [];

    // 1. Policy Distribution by Provider
    const policyProviders = {};
    policies.forEach(p => {
        policyProviders[p.provider] = (policyProviders[p.provider] || 0) + 1;
    });

    const policyCtx = document.getElementById('policyChart').getContext('2d');
    policyChart = new Chart(policyCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(policyProviders),
            datasets: [{
                data: Object.values(policyProviders),
                backgroundColor: [
                    '#667eea', '#764ba2', '#f093fb', '#4facfe',
                    '#43e97b', '#fa709a', '#fee140', '#30cfd0'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // 2. SIP Distribution by Fund
    const sipFunds = {};
    sips.forEach(s => {
        const fundName = s.fund_name.split(' ').slice(0, 2).join(' '); // Shorten names
        sipFunds[fundName] = (sipFunds[fundName] || 0) + 1;
    });

    const sipCtx = document.getElementById('sipChart').getContext('2d');
    sipChart = new Chart(sipCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(sipFunds),
            datasets: [{
                data: Object.values(sipFunds),
                backgroundColor: [
                    '#667eea', '#764ba2', '#f093fb', '#4facfe',
                    '#43e97b', '#fa709a', '#fee140', '#30cfd0'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });

    // 3. Premium Breakdown by Policy Type
    const premiumByType = {};
    policies.filter(p => p.status === 'active').forEach(p => {
        const multiplier = {
            'monthly': 12,
            'quarterly': 4,
            'half-yearly': 2,
            'yearly': 1
        }[p.premium_frequency] || 1;
        const annualPremium = p.premium_amount * multiplier;
        premiumByType[p.policy_type] = (premiumByType[p.policy_type] || 0) + annualPremium;
    });

    const premiumCtx = document.getElementById('premiumChart').getContext('2d');
    premiumChart = new Chart(premiumCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(premiumByType),
            datasets: [{
                label: 'Annual Premium (₹)',
                data: Object.values(premiumByType),
                backgroundColor: '#667eea'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    // 4. Monthly SIP Amount Breakdown
    const sipAmountByFund = {};
    sips.filter(s => s.status === 'active').forEach(s => {
        const fundName = s.fund_name.split(' ').slice(0, 3).join(' ');
        sipAmountByFund[fundName] = (sipAmountByFund[fundName] || 0) + s.amount;
    });

    const sipAmountCtx = document.getElementById('sipAmountChart').getContext('2d');
    sipAmountChart = new Chart(sipAmountCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(sipAmountByFund),
            datasets: [{
                label: 'Monthly Amount (₹)',
                data: Object.values(sipAmountByFund),
                backgroundColor: '#764ba2'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function renderPoliciesTable(policies) {
    const container = document.getElementById('policies-list');

    if (policies.length === 0) {
        container.innerHTML = '<p style="color: #888; text-align: center; padding: 40px;">No policies found</p>';
        return;
    }

    const html = `
        <table>
            <thead>
                <tr>
                    <th>Policy Number</th>
                    <th>Provider</th>
                    <th>Type</th>
                    <th>Premium</th>
                    <th>Frequency</th>
                    <th>Renewal Date</th>
                    <th>Sum Assured</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${policies.map(policy => `
                    <tr>
                        <td><strong>${policy.policy_number}</strong></td>
                        <td>${policy.provider}</td>
                        <td>${policy.policy_type}</td>
                        <td>₹${formatNumber(policy.premium_amount)}</td>
                        <td>${policy.premium_frequency}</td>
                        <td>${formatDate(policy.renewal_date)}</td>
                        <td>₹${formatNumber(policy.sum_assured || 0)}</td>
                        <td><span class="badge badge-${getStatusColor(policy.status)}">${policy.status.toUpperCase()}</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

function renderSIPsTable(sips) {
    const container = document.getElementById('sips-list');

    if (sips.length === 0) {
        container.innerHTML = '<p style="color: #888; text-align: center; padding: 40px;">No SIPs found</p>';
        return;
    }

    const html = `
        <table>
            <thead>
                <tr>
                    <th>Fund Name</th>
                    <th>Folio Number</th>
                    <th>Amount</th>
                    <th>Frequency</th>
                    <th>SIP Day</th>
                    <th>Start Date</th>
                    <th>End Date</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                ${sips.map(sip => `
                    <tr>
                        <td><strong>${sip.fund_name}</strong></td>
                        <td>${sip.folio_number || '-'}</td>
                        <td>₹${formatNumber(sip.amount)}</td>
                        <td>${sip.frequency.toUpperCase()}</td>
                        <td>${sip.sip_day}</td>
                        <td>${formatDate(sip.start_date)}</td>
                        <td>${sip.end_date ? formatDate(sip.end_date) : 'Ongoing'}</td>
                        <td><span class="badge badge-${getStatusColor(sip.status)}">${sip.status.toUpperCase()}</span></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.innerHTML = html;
}

// Utility Functions
function formatNumber(num) {
    return num.toLocaleString('en-IN');
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
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
