"""
Generate a test Excel file with 5 new clients for testing the Excel Ingestion Agent
"""

import pandas as pd
from datetime import datetime

# Sample client data for testing
test_clients = [
    {
        "Name": "Amit Kumar Sharma",
        "Phone": "9876543210",
        "Email": "amit.sharma@example.com",
        "Address": "123 MG Road, Bangalore, Karnataka 560001",
        "Notes": "Interested in mutual funds and term insurance"
    },
    {
        "Name": "Priya Patel",
        "Phone": "9123456780",
        "Email": "priya.patel@example.com",
        "Address": "456 Satellite Road, Ahmedabad, Gujarat 380015",
        "Notes": "Looking for retirement planning solutions"
    },
    {
        "Name": "Rajesh Mehta",
        "Phone": "9988776655",
        "Email": "rajesh.mehta@example.com",
        "Address": "789 Juhu Beach Road, Mumbai, Maharashtra 400049",
        "Notes": "High net worth individual, interested in portfolio diversification"
    },
    {
        "Name": "Sneha Reddy",
        "Phone": "9876501234",
        "Email": "sneha.reddy@example.com",
        "Address": "321 Banjara Hills, Hyderabad, Telangana 500034",
        "Notes": "First-time investor, wants to start SIPs"
    },
    {
        "Name": "Vikram Singh",
        "Phone": "9123450987",
        "Email": "vikram.singh@example.com",
        "Address": "654 Civil Lines, Delhi, NCR 110054",
        "Notes": "Owns multiple policies, needs consolidation and review"
    }
]

# Create DataFrame
df = pd.DataFrame(test_clients)

# Generate filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"test_clients_{timestamp}.xlsx"
filepath = f"/Users/rashisharma/Desktop/financial-advisor-platform/sample_data/{filename}"

# Save to Excel
df.to_excel(filepath, index=False, sheet_name="Clients")

print(f"✅ Test Excel file generated successfully!")
print(f"📄 File location: {filepath}")
print(f"\n📊 File contains {len(test_clients)} clients:")
for i, client in enumerate(test_clients, 1):
    print(f"   {i}. {client['Name']} - {client['Phone']}")

print(f"\n💡 To test the Excel Ingestion Agent:")
print(f"   1. Use this file: {filename}")
print(f"   2. Upload it through the AI Agents tab")
print(f"   3. Review the proposed actions")
print(f"   4. Approve to add clients to the database")
