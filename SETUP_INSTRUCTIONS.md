# Setup Instructions - Financial Advisor Platform

## ✅ What's Been Fixed

### 1. **Login/Logout & User Profile** ✅
- Added logout button to header on index.html
- Added user profile display (avatar, name, email) in header
- Logout button already present on clients.html and calendar.html
- User info is now loaded from `/api/auth/me` endpoint

### 2. **AI Portfolio Analysis** ✅
- Fixed API response format mismatch
- Backend now returns `overview` object matching frontend expectations
- Portfolio analysis endpoint: `GET /api/clients/{client_id}/ai-overview`

### 3. **Environment Configuration** ✅
- Created `.env` file in `/backend/` directory
- Pre-configured with all necessary settings

### 4. **Backend Features Status**
| Feature | Status | Endpoint |
|---------|--------|----------|
| Excel Upload & AI Ingestion | ✅ Working | `POST /api/agents/excel/upload` |
| Calendar (Backend) | ✅ Working | `GET /api/meetings/calendar` |
| Portfolio Analysis | ✅ Working | `GET /api/clients/{client_id}/ai-overview` |
| Daily Insights | ✅ Working | `GET /api/agents/capital-companion/daily` |
| AI Chat | ✅ Working | `POST /api/chat` |
| User Authentication | ✅ Working | `POST /api/auth/login` |

---

## ⚠️ **ACTION REQUIRED: Get Free Hugging Face API Key**

The AI features (Capital Companion, AI Chat, Daily Insights) require a **free** Hugging Face API key.

### How to Get Your Free API Key (2 minutes):

1. **Sign up at Hugging Face** (free forever):
   - Visit: https://huggingface.co/join
   - Create a free account

2. **Generate API Token**:
   - Go to: https://huggingface.co/settings/tokens
   - Click "New token"
   - Name: `financial-advisor-platform`
   - Type: Select "Read" (default)
   - Click "Generate token"
   - **Copy the token** (starts with `hf_...`)

3. **Add Token to `.env` File**:
   ```bash
   # Open the .env file
   cd /Users/rashisharma/Desktop/Project/financial-advisor-platform/backend
   nano .env
   ```

   Find this line:
   ```
   HUGGINGFACE_API_KEY=hf_your_api_key_here_replace_this
   ```

   Replace `hf_your_api_key_here_replace_this` with your actual token:
   ```
   HUGGINGFACE_API_KEY=hf_XxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXx
   ```

   Save and exit (Ctrl+X, then Y, then Enter)

4. **Restart the Backend**:
   ```bash
   cd /Users/rashisharma/Desktop/Project/financial-advisor-platform/backend
   pkill -f "python.*main.py"
   python main.py
   ```

### Free Tier Limits:
- **1000 requests per day** (~40 per hour)
- No credit card required
- More than enough for 100+ clients
- **Cost: $0/month** 🎉

---

## 🚀 How to Use the Application

### 1. **Login**
   - Open: `file:///Users/rashisharma/Desktop/Project/financial-advisor-platform/frontend/login.html`
   - Credentials:
     - **Email**: `demo@example.com`
     - **Password**: `demo123`

### 2. **Home Dashboard**
   - View dashboard stats
   - **Capital Companion Daily Insights** (powered by AI)
   - **Urgent Reminders** (next 7 days)
   - **Upcoming Meetings** (calendar widget)
   - **User Profile** in header (top right)
   - **Logout** button (top right)

### 3. **Clients Management**
   - Navigate: Home → "👥 Clients" button or clients.html
   - View all clients
   - Click client name to see detailed profile
   - **AI Portfolio Analysis** on client detail page

### 4. **Calendar**
   - Navigate: Calendar link in nav bar
   - View all meetings in calendar format
   - FullCalendar integration with drag-and-drop

### 5. **Excel Upload & AI Ingestion** ✨ ENHANCED
   - Navigate: Home → AI Agents tab
   - Click "Upload Excel" button
   - Upload single file containing:
     - **Clients** (Name, Phone, Email, Address)
     - **Policies** (Policy Number, Provider, Premium, Renewal Date, etc.)
     - **SIPs** (Fund Name, Amount, SIP Day, Start Date, etc.)
   - AI agent automatically:
     - Detects entity types from column names
     - Identifies duplicates (by phone, policy_number, folio_number)
     - Proposes **UPDATE** for existing records
     - Proposes **INSERT** for new records
     - Links policies/SIPs to existing clients
   - Review proposed actions in "Approvals" tab
   - Each action shows: Row #, Action (INSERT/UPDATE), Entity, Data, Reasoning
   - Approve to execute, Reject to skip

   **See detailed guide:** [/docs/EXCEL_UPLOAD_GUIDE.md](docs/EXCEL_UPLOAD_GUIDE.md)

### 6. **AI Features**
   - **Daily Insights**: Auto-generated on home page
   - **Portfolio Analysis**: Click any client → AI Overview section
   - **AI Chat Widget**: Floating button on bottom-right (all pages)
     - Ask general financial questions
     - PII requests are automatically blocked

---

## 🧪 Testing Checklist

### Excel Upload Test:
**Option 1: Clients Only**
1. Create test Excel file: `clients_test.xlsx`
2. Columns: `Name`, `Phone`, `Email`, `Address`
3. Add 2-3 sample rows
4. Upload via AI Agents tab
5. Check Approvals tab → should see INSERT actions

**Option 2: Mixed (Clients + Policies + SIPs)**
1. Create `portfolio_test.xlsx` with columns:
   - `Name`, `Phone`, `Email`
   - `Policy Number`, `Provider`, `Premium Amount`, `Renewal Date`
   - `Fund Name`, `SIP Amount`, `SIP Day`, `Start Date`
2. Add 2-3 rows with client + policy + SIP data
3. Upload → AI agent detects all entity types
4. Approvals tab shows:
   - Client INSERT/UPDATE actions
   - Policy INSERT/UPDATE actions
   - SIP INSERT/UPDATE actions

**Option 3: Update Existing Data**
1. Create Excel with existing client phone number
2. Change email or address
3. Upload → should see UPDATE action (not INSERT)
4. Approve → verify client details updated

### Calendar Test:
1. Go to Calendar page
2. Verify existing meetings appear
3. Click a meeting to view details
4. (Optional) Create new meeting

### AI Features Test (After Adding API Key):
1. **Daily Insights**: Refresh home page → check Capital Companion section
2. **Portfolio Analysis**: Click any client → verify AI Overview loads with score
3. **AI Chat**: Click chat widget → ask "What is term insurance?"

### User Profile Test:
1. Verify your name/email appears in header
2. Click logout → redirected to login page
3. Login again → redirected to dashboard

---

## 📋 Current Data

The database is pre-populated with:
- **1 Advisor**: demo@example.com (password: demo123)
- **5 Clients**: Rajesh Kumar, Priya Sharma, Amit Patel, Sneha Reddy, Vikram Singh
- **5 Policies**: Various providers (LIC, HDFC, ICICI, Max, SBI)
- **4 SIPs**: Various mutual funds
- **3 Meetings**: Upcoming meetings in next 7 days
- **3 Reminders**: Policy renewals and SIP due dates

---

## ❓ Troubleshooting

### Issue: "No insights available at the moment"
**Solution**: Add Hugging Face API key to `.env` file (see section above)

### Issue: "AI analysis failed to load"
**Solution**:
1. Check if API key is set correctly in `.env`
2. Restart backend server
3. Check backend logs: `tail -f backend/server.log`

### Issue: "Calendar not showing meetings"
**Solution**:
1. Verify backend is running: `curl http://127.0.0.1:8000/health`
2. Check browser console for errors (F12 → Console tab)
3. Verify token is valid (logout and login again)

### Issue: "Excel upload not working"
**Solution**:
1. Ensure file is `.xlsx` or `.xls` format
2. Check that columns include "Name" and "Phone"
3. View Approvals tab to see proposed actions

### Issue: "User profile not showing"
**Solution**:
1. Clear browser cache and reload
2. Logout and login again
3. Check browser console for errors

---

## 🎯 Quick Start (After API Key Setup)

```bash
# 1. Start backend (if not already running)
cd /Users/rashisharma/Desktop/Project/financial-advisor-platform/backend
python main.py

# 2. Open frontend in browser
open /Users/rashisharma/Desktop/Project/financial-advisor-platform/frontend/login.html

# 3. Login with demo credentials
# Email: demo@example.com
# Password: demo123

# 4. Explore features!
```

---

## 📞 Need Help?

If you encounter any issues:
1. Check backend logs: `tail -f /Users/rashisharma/Desktop/Project/financial-advisor-platform/backend/server.log`
2. Check browser console: Press F12 → Console tab
3. Verify backend is running: `curl http://127.0.0.1:8000/health`

---

## 🎉 Summary

**What's Working Right Now (Without API Key):**
- ✅ Login/Logout
- ✅ User profile display
- ✅ Dashboard with stats
- ✅ Client management (CRUD)
- ✅ Policy & SIP management
- ✅ Excel upload (heuristic analysis)
- ✅ Calendar view
- ✅ Reminders
- ✅ Approvals workflow

**What Needs API Key:**
- ⏳ Capital Companion Daily Insights
- ⏳ AI Portfolio Analysis (client detail page)
- ⏳ AI Chat Widget

**Get your free API key** (2 minutes) to unlock all AI features! 🚀
