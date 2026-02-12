"""
Generate Sample Excel Files for Testing Excel Ingestion Agent

This script creates sample Excel files that demonstrate:
1. Clients only
2. Policies with client info
3. SIPs with client info
4. Mixed (all entities in one file)
"""

import pandas as pd
from datetime import datetime, timedelta
import os

# Create samples directory
samples_dir = "../samples"
os.makedirs(samples_dir, exist_ok=True)

print("📊 Generating sample Excel files...")


# ==================== Sample 1: Clients Only ====================
print("\n1. Creating clients_sample.xlsx...")

clients_data = [
    {
        "Name": "Ravi Verma",
        "Phone": "9123456789",
        "Email": "ravi.verma@example.com",
        "Address": "45 Park Street, Kolkata"
    },
    {
        "Name": "Meena Iyer",
        "Phone": "9234567890",
        "Email": "meena.iyer@example.com",
        "Address": "78 MG Road, Bengaluru"
    },
    {
        "Name": "Suresh Malhotra",
        "Phone": "9345678901",
        "Email": "suresh.m@example.com",
        "Address": "12 Connaught Place, New Delhi"
    },
]

df_clients = pd.DataFrame(clients_data)
df_clients.to_excel(f"{samples_dir}/clients_sample.xlsx", index=False)
print("   ✅ clients_sample.xlsx created (3 new clients)")


# ==================== Sample 2: Policies with Client Info ====================
print("\n2. Creating policies_sample.xlsx...")

# Calculate dates
today = datetime.now()
renewal_1 = (today + timedelta(days=30)).strftime("%d/%m/%Y")
renewal_2 = (today + timedelta(days=60)).strftime("%d/%m/%Y")
renewal_3 = (today + timedelta(days=90)).strftime("%d/%m/%Y")

policies_data = [
    {
        "Client Name": "Ravi Verma",
        "Phone": "9123456789",
        "Policy Number": "LIC-2025-5001",
        "Provider": "LIC of India",
        "Policy Type": "Term Life",
        "Premium Amount": 25000,
        "Renewal Date": renewal_1,
        "Sum Assured": 10000000
    },
    {
        "Client Name": "Meena Iyer",
        "Phone": "9234567890",
        "Policy Number": "HDFC-2025-3045",
        "Provider": "HDFC Life",
        "Policy Type": "Health Insurance",
        "Premium Amount": 15000,
        "Renewal Date": renewal_2,
        "Sum Assured": 500000
    },
    {
        "Client Name": "Suresh Malhotra",
        "Phone": "9345678901",
        "Policy Number": "ICICI-2025-7812",
        "Provider": "ICICI Prudential",
        "Policy Type": "ULIP",
        "Premium Amount": 50000,
        "Renewal Date": renewal_3,
        "Sum Assured": 2500000
    },
]

df_policies = pd.DataFrame(policies_data)
df_policies.to_excel(f"{samples_dir}/policies_sample.xlsx", index=False)
print("   ✅ policies_sample.xlsx created (3 policies for existing clients)")


# ==================== Sample 3: SIPs with Client Info ====================
print("\n3. Creating sips_sample.xlsx...")

start_1 = (today - timedelta(days=365)).strftime("%d/%m/%Y")
start_2 = (today - timedelta(days=180)).strftime("%d/%m/%Y")
start_3 = (today - timedelta(days=90)).strftime("%d/%m/%Y")

sips_data = [
    {
        "Client Name": "Ravi Verma",
        "Phone": "9123456789",
        "Fund Name": "HDFC Top 100 Fund",
        "Folio Number": "HDFC-2024-1234",
        "Amount": 10000,
        "SIP Day": 5,
        "Start Date": start_1
    },
    {
        "Client Name": "Meena Iyer",
        "Phone": "9234567890",
        "Fund Name": "ICICI Bluechip Fund",
        "Folio Number": "ICICI-2024-5678",
        "Amount": 7500,
        "SIP Day": 10,
        "Start Date": start_2
    },
    {
        "Client Name": "Suresh Malhotra",
        "Phone": "9345678901",
        "Fund Name": "SBI Magnum Midcap Fund",
        "Folio Number": "SBI-2025-9012",
        "Amount": 15000,
        "SIP Day": 1,
        "Start Date": start_3
    },
]

df_sips = pd.DataFrame(sips_data)
df_sips.to_excel(f"{samples_dir}/sips_sample.xlsx", index=False)
print("   ✅ sips_sample.xlsx created (3 SIPs for existing clients)")


# ==================== Sample 4: Mixed - All Entities ====================
print("\n4. Creating mixed_portfolio_sample.xlsx...")

mixed_data = [
    {
        # Client info
        "Name": "Anjali Desai",
        "Phone": "9456789012",
        "Email": "anjali.desai@example.com",
        "Address": "33 Linking Road, Mumbai",
        # Policy info
        "Policy Number": "MAX-2025-4001",
        "Provider": "Max Life Insurance",
        "Policy Type": "Endowment",
        "Premium Amount": 35000,
        "Renewal Date": (today + timedelta(days=45)).strftime("%d/%m/%Y"),
        "Sum Assured": 1500000,
        # SIP info
        "Fund Name": "Axis Bluechip Fund",
        "Folio Number": "AXIS-2024-3344",
        "SIP Amount": 8000,
        "SIP Day": 7,
        "Start Date": (today - timedelta(days=200)).strftime("%d/%m/%Y")
    },
    {
        # Client info
        "Name": "Karthik Nair",
        "Phone": "9567890123",
        "Email": "karthik.nair@example.com",
        "Address": "56 Brigade Road, Bengaluru",
        # Policy info
        "Policy Number": "SBI-2025-8899",
        "Provider": "SBI Life",
        "Policy Type": "Term Life",
        "Premium Amount": 20000,
        "Renewal Date": (today + timedelta(days=75)).strftime("%d/%m/%Y"),
        "Sum Assured": 7500000,
        # SIP info
        "Fund Name": "Mirae Asset Large Cap Fund",
        "Folio Number": "MIRAE-2024-7788",
        "SIP Amount": 12000,
        "SIP Day": 15,
        "Start Date": (today - timedelta(days=150)).strftime("%d/%m/%Y")
    },
]

df_mixed = pd.DataFrame(mixed_data)
df_mixed.to_excel(f"{samples_dir}/mixed_portfolio_sample.xlsx", index=False)
print("   ✅ mixed_portfolio_sample.xlsx created (2 clients + policies + SIPs)")


# ==================== Sample 5: Update Existing Client ====================
print("\n5. Creating client_update_sample.xlsx...")

# This file contains existing client data with updated information
# Use phone numbers from the seed data in the database
update_data = [
    {
        "Name": "Rajesh Kumar",  # Existing client from seed data
        "Phone": "9876543210",  # Existing phone number
        "Email": "rajesh.kumar.updated@email.com",  # Updated email
        "Address": "123 MG Road, Bangalore - UPDATED"  # Updated address
    },
]

df_update = pd.DataFrame(update_data)
df_update.to_excel(f"{samples_dir}/client_update_sample.xlsx", index=False)
print("   ✅ client_update_sample.xlsx created (UPDATE existing client)")


# ==================== Sample 6: Add Policy to Existing Client ====================
print("\n6. Creating policy_for_existing_client_sample.xlsx...")

existing_policy_data = [
    {
        "Client Name": "Rajesh Kumar",  # Existing client
        "Phone": "9876543210",  # Existing phone
        "Policy Number": "NEW-2026-100",  # New policy
        "Provider": "Bajaj Allianz",
        "Policy Type": "Health Insurance",
        "Premium Amount": 18000,
        "Renewal Date": (today + timedelta(days=120)).strftime("%d/%m/%Y"),
        "Sum Assured": 750000
    },
    {
        "Client Name": "Priya Sharma",  # Existing client
        "Phone": "9765432108",  # Existing phone
        "Policy Number": "NEW-2026-101",  # New policy
        "Provider": "Star Health",
        "Policy Type": "Family Floater",
        "Premium Amount": 25000,
        "Renewal Date": (today + timedelta(days=150)).strftime("%d/%m/%Y"),
        "Sum Assured": 1000000
    },
]

df_existing_policy = pd.DataFrame(existing_policy_data)
df_existing_policy.to_excel(f"{samples_dir}/policy_for_existing_client_sample.xlsx", index=False)
print("   ✅ policy_for_existing_client_sample.xlsx created (NEW policies for existing clients)")


# ==================== Sample 7: Update Existing Policy ====================
print("\n7. Creating policy_update_sample.xlsx...")

policy_update_data = [
    {
        "Policy Number": "LIC-2023-001",  # Existing policy from seed data
        "Premium Amount": 18000,  # Updated premium (was 15000)
        "Renewal Date": (today + timedelta(days=200)).strftime("%d/%m/%Y"),  # Updated renewal
    },
]

df_policy_update = pd.DataFrame(policy_update_data)
df_policy_update.to_excel(f"{samples_dir}/policy_update_sample.xlsx", index=False)
print("   ✅ policy_update_sample.xlsx created (UPDATE existing policy)")


# ==================== Summary ====================
print("\n" + "="*60)
print("✅ All sample Excel files generated successfully!")
print("="*60)
print(f"\nLocation: {os.path.abspath(samples_dir)}/")
print("\nFiles created:")
print("1. clients_sample.xlsx - 3 new clients")
print("2. policies_sample.xlsx - 3 policies for new clients")
print("3. sips_sample.xlsx - 3 SIPs for new clients")
print("4. mixed_portfolio_sample.xlsx - 2 clients + policies + SIPs")
print("5. client_update_sample.xlsx - UPDATE existing client (Rajesh)")
print("6. policy_for_existing_client_sample.xlsx - NEW policies for existing clients")
print("7. policy_update_sample.xlsx - UPDATE existing policy")
print("\n" + "="*60)
print("\n📝 Testing Instructions:")
print("="*60)
print("\n1. Start backend server:")
print("   cd backend && python main.py")
print("\n2. Open frontend in browser:")
print("   file:///Users/rashisharma/Desktop/Project/financial-advisor-platform/frontend/login.html")
print("\n3. Login (demo@example.com / demo123)")
print("\n4. Go to AI Agents tab → Upload Excel")
print("\n5. Test each sample file:")
print("   - clients_sample.xlsx → Should see 3 INSERT actions")
print("   - client_update_sample.xlsx → Should see UPDATE action for Rajesh")
print("   - policies_sample.xlsx → Should see INSERT actions + client linking")
print("   - mixed_portfolio_sample.xlsx → Should see multiple entity types")
print("\n6. Review in Approvals tab, then Approve")
print("\n7. Verify in Clients page and client detail pages")
print("\n" + "="*60)
