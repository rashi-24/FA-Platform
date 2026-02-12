# Excel Upload Guide - Financial Advisor Platform

## Overview

The Excel ingestion feature allows you to upload client data, policies, and SIPs in a single Excel file. The AI agent will automatically:

- **Detect entity types** (clients, policies, SIPs) based on column names
- **Identify duplicates** using unique identifiers
- **Propose UPDATE** for existing records
- **Propose INSERT** for new records
- **Link policies/SIPs** to existing clients automatically

---

## Supported Entity Types

### 1. Client Data
**Required Columns:**
- `Name` or `Client Name` - Full name of the client
- `Phone` or `Mobile` - 10-digit phone number (used for duplicate detection)

**Optional Columns:**
- `Email` or `Email Address`
- `Address` or `Location`

**Duplicate Detection:**
- By phone number (unique identifier)
- If phone exists → proposes UPDATE
- If new phone → proposes INSERT

---

### 2. Policy Data
**Required Columns:**
- `Policy Number` or `Policy No` - Unique policy identifier
- `Provider` or `Insurance Company` - e.g., "LIC of India", "HDFC Life"
- `Premium Amount` or `Premium` - Annual/monthly premium
- `Renewal Date` or `Renewal` - Date in format: DD/MM/YYYY or YYYY-MM-DD
- `Phone` or `Client Phone` - Client's phone number to link policy

**Optional Columns:**
- `Policy Type` or `Type` - e.g., "Term Life", "Health", "ULIP"
- `Sum Assured` or `Coverage` - Coverage amount
- `Client Name` or `Name` - Client's name (used if phone not provided)

**Duplicate Detection:**
- By policy_number (unique identifier)
- If policy_number exists → proposes UPDATE
- If new policy_number → proposes INSERT

**Client Linking:**
- First tries to find client by phone number
- Falls back to name matching if phone not provided
- Skips if client not found

---

### 3. SIP Data
**Required Columns:**
- `Fund Name` or `Fund` - Mutual fund scheme name
- `Amount` or `SIP Amount` - Monthly investment amount
- `SIP Day` or `Day` - Day of month (1-31) for deduction
- `Start Date` or `Start` - SIP start date in format: DD/MM/YYYY
- `Phone` or `Client Phone` - Client's phone number to link SIP

**Optional Columns:**
- `Folio Number` or `Folio` - Fund folio number
- `Client Name` or `Name` - Client's name

**Duplicate Detection:**
- By folio_number (if provided)
- By client + fund_name combination
- If exists → proposes UPDATE
- If new → proposes INSERT

**Client Linking:**
- Same as policy linking (by phone or name)

---

## Excel File Formats

### Format 1: Clients Only

| Name           | Phone      | Email                  | Address                      |
|----------------|------------|------------------------|------------------------------|
| Rajesh Kumar   | 9876543210 | rajesh.k@email.com     | 123 MG Road, Bangalore       |
| Priya Sharma   | 9765432108 | priya.s@email.com      | 456 Anna Nagar, Chennai      |
| Amit Patel     | 9654321076 | amit.p@email.com       | 789 CG Road, Ahmedabad       |

### Format 2: Policies with Client Info

| Client Name    | Phone      | Policy Number | Provider      | Policy Type    | Premium Amount | Renewal Date | Sum Assured |
|----------------|------------|---------------|---------------|----------------|----------------|--------------|-------------|
| Rajesh Kumar   | 9876543210 | LIC-2023-001  | LIC of India  | Term Life      | 15000          | 15/01/2026   | 5000000     |
| Priya Sharma   | 9765432108 | HDFC-2024-045 | HDFC Life     | Health         | 8000           | 01/03/2026   | 1000000     |
| Amit Patel     | 9654321076 | ICICI-2024-012| ICICI Prudential | ULIP        | 12000          | 01/06/2025   | 2500000     |

### Format 3: SIPs with Client Info

| Client Name    | Phone      | Fund Name                          | Folio Number   | Amount | SIP Day | Start Date |
|----------------|------------|------------------------------------|----------------|--------|---------|------------|
| Priya Sharma   | 9765432108 | HDFC Mid-Cap Opportunities Fund    | HDFC-2023-8901 | 5000   | 5       | 05/01/2023 |
| Rajesh Kumar   | 9876543210 | SBI Small Cap Fund                 | SBI-2024-9876  | 4000   | 15      | 15/03/2024 |

### Format 4: Mixed (All Entities in One File)

**Option A: Separate sheets**
- Sheet 1: Clients
- Sheet 2: Policies
- Sheet 3: SIPs

**Option B: Single sheet with all columns**

| Name         | Phone      | Email            | Policy Number | Provider    | Premium | Renewal Date | Fund Name              | SIP Amount | SIP Day | Start Date |
|--------------|------------|------------------|---------------|-------------|---------|--------------|------------------------|------------|---------|------------|
| Rajesh Kumar | 9876543210 | rajesh@email.com | LIC-2023-001  | LIC of India| 15000   | 15/01/2026   | SBI Small Cap Fund     | 4000       | 15      | 15/03/2024 |

> **Note**: If a row has client + policy + SIP data, it will create/update all three entities.

---

## Column Name Variations (All Supported)

The agent uses **fuzzy matching** for column names. All these variations work:

### Client Fields:
- `Name`, `Client Name`, `Customer Name`, `Full Name`
- `Phone`, `Mobile`, `Contact`, `Phone Number`, `Mobile Number`
- `Email`, `Email ID`, `Email Address`
- `Address`, `Location`, `City`

### Policy Fields:
- `Policy Number`, `Policy No`, `Policy ID`, `PolicyNo`
- `Provider`, `Insurance Company`, `Insurer`, `Company`
- `Policy Type`, `Type`, `Plan Type`, `Plan`
- `Premium Amount`, `Premium`, `Amount`, `Premium Amt`
- `Renewal Date`, `Renewal`, `Due Date`, `Next Renewal`
- `Sum Assured`, `Coverage`, `Cover Amount`, `Sum Insured`

### SIP Fields:
- `Fund Name`, `Fund`, `Scheme Name`, `Scheme`
- `Folio Number`, `Folio`, `Folio No`, `FolioNo`
- `Amount`, `SIP Amount`, `Monthly Amount`, `Investment`
- `SIP Day`, `Day`, `Payment Day`, `Deduction Day`
- `Start Date`, `Start`, `Commenced Date`, `Inception Date`

---

## Date Format Support

All these date formats are supported:
- `DD/MM/YYYY` - 15/01/2026
- `MM/DD/YYYY` - 01/15/2026
- `YYYY-MM-DD` - 2026-01-15
- `DD-MM-YYYY` - 15-01-2026
- `DD.MM.YYYY` - 15.01.2026

---

## Phone Number Format

Phone numbers are automatically cleaned:
- `9876543210` → Valid
- `+91-9876543210` → Cleaned to `9876543210`
- `(987) 654-3210` → Cleaned to `9876543210`
- Must be 10 digits (Indian format)

---

## Upload Process

### Step 1: Upload File
- Navigate to **Home → AI Agents** tab
- Click **"Upload Excel"** button
- Select your `.xlsx` or `.xls` file
- Wait for processing

### Step 2: Review Proposed Actions
- Go to **"Approvals"** tab
- See all proposed INSERT/UPDATE actions
- Each action shows:
  - **Row number** from Excel
  - **Action type** (INSERT or UPDATE)
  - **Entity type** (client, policy, sip)
  - **Data** to be inserted/updated
  - **Reasoning** (why this action was proposed)
  - **Confidence score** (0.0 to 1.0)

### Step 3: Approve or Reject
- Review each proposed action
- Click **"Approve"** to execute
- Click **"Reject"** to skip
- Add optional review notes

### Step 4: Verify Results
- Check **Clients** page to see new/updated clients
- View client detail pages to see policies and SIPs
- Check **Audit Logs** for complete history

---

## Smart Duplicate Detection Examples

### Example 1: Updating Client Details
**Excel Row:**
```
Name: Rajesh Kumar
Phone: 9876543210
Email: rajesh.kumar.new@email.com
```

**Result:**
- ✅ Agent detects phone `9876543210` exists in database
- ✅ Proposes **UPDATE** action
- ✅ Will update email to new value
- ✅ Name unchanged (already correct)

### Example 2: Adding Policy to Existing Client
**Excel Row:**
```
Client Name: Priya Sharma
Phone: 9765432108
Policy Number: NEW-2026-100
Provider: Max Life
Premium: 10000
Renewal Date: 01/04/2026
```

**Result:**
- ✅ Finds client by phone `9765432108`
- ✅ Checks if policy `NEW-2026-100` exists → No
- ✅ Proposes **INSERT** for new policy
- ✅ Automatically links to Priya's client ID

### Example 3: Updating Existing Policy
**Excel Row:**
```
Policy Number: LIC-2023-001
Premium Amount: 18000
```

**Result:**
- ✅ Detects policy `LIC-2023-001` exists
- ✅ Proposes **UPDATE** to change premium from 15000 to 18000
- ✅ Other fields unchanged

### Example 4: Mixed Insert + Update
**Excel:**
```
Row 1: New client (INSERT)
Row 2: Existing client with new policy (UPDATE client, INSERT policy)
Row 3: Existing client, existing policy (UPDATE both)
```

**Result:**
- ✅ 1 client INSERT, 2 client UPDATEs
- ✅ 2 policy INSERTs, 1 policy UPDATE
- ✅ All proposed actions shown in Approvals tab

---

## Error Handling

### Row is Skipped If:
- **Client**: Missing name or phone
- **Policy**: Missing policy_number, provider, premium, or renewal_date
- **Policy**: Client not found (by phone or name)
- **SIP**: Missing fund_name, amount, sip_day, or start_date
- **SIP**: Client not found
- **Date**: Invalid date format

### Confidence Scores:
- **0.95** - Update action (high confidence, entity exists)
- **0.90** - Insert action (new entity, all required fields present)
- **0.60** - Insert with missing optional fields
- **0.00** - Skip action (cannot process)

---

## Best Practices

### 1. Always Include Client Identifier
- For policies and SIPs, always include either:
  - Client's **phone number** (recommended), or
  - Client's **full name** (exact match)

### 2. Use Unique Identifiers
- **Policy Number** must be unique across all policies
- **Phone Number** must be unique per client
- **Folio Number** should be unique per SIP (if provided)

### 3. Test with Small Files First
- Upload 2-3 rows initially
- Verify proposed actions in Approvals tab
- Once confident, upload larger files

### 4. Review Before Approving
- Always review proposed actions
- Check that UPDATE actions are correct
- Verify client linking is accurate

### 5. Use Consistent Date Formats
- Pick one date format and stick to it
- DD/MM/YYYY is recommended for Indian dates

### 6. Clean Your Data
- Remove duplicate rows in Excel
- Ensure phone numbers are valid
- Check for typos in names

---

## Example Workflow

### Scenario: Quarterly Portfolio Update

1. **Export client list** from existing system
2. **Add new policies** purchased this quarter
3. **Update renewal dates** for renewed policies
4. **Add new SIPs** started this quarter
5. **Upload single Excel file** with all data
6. **Review 50+ proposed actions** in Approvals tab
7. **Approve all** in one click
8. **Verify** clients, policies, SIPs updated correctly

**Time Saved:** Manual data entry would take 2-3 hours. Excel upload + approval takes 5-10 minutes!

---

## Download Sample Templates

Create these sample Excel files to get started:

### clients_template.xlsx
```
Name | Phone | Email | Address
-----|-------|-------|--------
```

### policies_template.xlsx
```
Client Name | Phone | Policy Number | Provider | Policy Type | Premium Amount | Renewal Date | Sum Assured
------------|-------|---------------|----------|-------------|----------------|--------------|-------------
```

### sips_template.xlsx
```
Client Name | Phone | Fund Name | Folio Number | Amount | SIP Day | Start Date
------------|-------|-----------|--------------|--------|---------|------------
```

### mixed_template.xlsx
```
Name | Phone | Email | Policy Number | Provider | Premium | Renewal Date | Fund Name | SIP Amount | SIP Day | Start Date
-----|-------|-------|---------------|----------|---------|--------------|-----------|------------|---------|------------
```

---

## Troubleshooting

### Issue: "Cannot find client for policy"
**Solution:** Ensure client phone number or exact name is in the row

### Issue: "No actions proposed"
**Solution:** Check column names match supported variations (case-insensitive)

### Issue: "Date parsing failed"
**Solution:** Use supported date formats: DD/MM/YYYY, YYYY-MM-DD, etc.

### Issue: "Duplicate phone number"
**Solution:** Remove duplicate clients from Excel file first

### Issue: "Policy already exists but proposing INSERT"
**Solution:** Policy number might have spaces or typos. Check for exact match.

---

## Need Help?

1. Check **Approvals** tab to see what agent detected
2. Review **Agent Reasoning** for each proposed action
3. Check **Confidence Score** (low score = uncertain detection)
4. View **Backend Logs** for detailed processing info:
   ```bash
   tail -f backend/server.log
   ```

---

**Happy Uploading!** 🚀
