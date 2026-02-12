"""
Seed sample data for testing the Financial Advisor Platform
"""

from datetime import date, datetime, timedelta
from database import get_db
from models import (
    Client, Policy, SIP, Meeting, Reminder,
    PolicyStatus, SIPStatus, SIPFrequency, MeetingType, Advisor
)
from auth import get_password_hash

def seed_sample_data():
    """Create sample data for testing"""

    with get_db() as db:
        print("🌱 Seeding sample data...")

        # Create sample advisor (for authentication)
        advisor = db.query(Advisor).filter(Advisor.email == "demo@example.com").first()
        if not advisor:
            advisor = Advisor(
                username="demo",
                email="demo@example.com",
                password_hash=get_password_hash("demo123"),
                full_name="Demo Advisor",
                is_active=True
            )
            db.add(advisor)
            db.commit()
            db.refresh(advisor)
            print(f"✅ Created advisor: {advisor.email}")
        else:
            print(f"ℹ️  Advisor already exists: {advisor.email}")

        # Create sample clients
        clients = [
            Client(
                name="Rajesh Kumar",
                phone="9876543210",
                email="rajesh.kumar@email.com",
                address="123 MG Road, Bangalore, Karnataka 560001",
                notes="High-value client, prefers life insurance",
                last_contact_date=date.today() - timedelta(days=15)
            ),
            Client(
                name="Priya Sharma",
                phone="9876543211",
                email="priya.sharma@email.com",
                address="456 Park Street, Mumbai, Maharashtra 400001",
                notes="Interested in SIP investments",
                last_contact_date=date.today() - timedelta(days=5)
            ),
            Client(
                name="Amit Patel",
                phone="9876543212",
                email="amit.patel@email.com",
                address="789 Lake View, Ahmedabad, Gujarat 380001",
                notes="Young professional, looking for health insurance",
                last_contact_date=date.today() - timedelta(days=30)
            ),
            Client(
                name="Sneha Reddy",
                phone="9876543213",
                email="sneha.reddy@email.com",
                address="321 Tank Bund Road, Hyderabad, Telangana 500001",
                notes="Family plan, 2 children",
                last_contact_date=date.today() - timedelta(days=60)
            ),
            Client(
                name="Vikram Singh",
                phone="9876543214",
                email="vikram.singh@email.com",
                address="654 Civil Lines, Delhi 110001",
                notes="Business owner, high net worth",
                last_contact_date=date.today() - timedelta(days=10)
            ),
        ]

        for client in clients:
            db.add(client)
        db.commit()
        print(f"✅ Created {len(clients)} clients")

        # Refresh clients to get their IDs
        db.refresh(clients[0])
        db.refresh(clients[1])
        db.refresh(clients[2])
        db.refresh(clients[3])
        db.refresh(clients[4])

        # Create sample policies
        policies = [
            # Rajesh Kumar's policies
            Policy(
                client_id=clients[0].id,
                policy_number="LIC-2023-001",
                provider="LIC of India",
                policy_type="Term Life",
                premium_amount=15000,
                premium_frequency="yearly",
                sum_assured=5000000,
                renewal_date=date(2026, 1, 15),
                maturity_date=date(2043, 1, 15),
                status=PolicyStatus.ACTIVE
            ),
            Policy(
                client_id=clients[0].id,
                policy_number="HDFC-2023-045",
                provider="HDFC Life",
                policy_type="Health Insurance",
                premium_amount=8000,
                premium_frequency="yearly",
                sum_assured=1000000,
                renewal_date=date(2026, 3, 1),
                status=PolicyStatus.ACTIVE
            ),
            # Priya Sharma's policies
            Policy(
                client_id=clients[1].id,
                policy_number="ICICI-2024-012",
                provider="ICICI Prudential",
                policy_type="ULIP",
                premium_amount=12000,
                premium_frequency="yearly",
                sum_assured=2500000,
                renewal_date=date(2025, 6, 1),
                maturity_date=date(2034, 6, 1),
                status=PolicyStatus.ACTIVE
            ),
            # Amit Patel's policies
            Policy(
                client_id=clients[2].id,
                policy_number="MAX-2024-089",
                provider="Max Life",
                policy_type="Health Insurance",
                premium_amount=6000,
                premium_frequency="yearly",
                sum_assured=500000,
                renewal_date=date.today() + timedelta(days=25),  # Upcoming renewal
                status=PolicyStatus.ACTIVE
            ),
            # Sneha Reddy's policies
            Policy(
                client_id=clients[3].id,
                policy_number="SBI-2023-156",
                provider="SBI Life",
                policy_type="Term Life",
                premium_amount=20000,
                premium_frequency="yearly",
                sum_assured=10000000,
                renewal_date=date.today() + timedelta(days=5),  # Urgent renewal
                maturity_date=date(2033, 4, 1),
                status=PolicyStatus.ACTIVE
            ),
        ]

        for policy in policies:
            db.add(policy)
        db.commit()
        print(f"✅ Created {len(policies)} policies")

        # Create sample SIPs
        sips = [
            # Priya Sharma's SIPs
            SIP(
                client_id=clients[1].id,
                fund_name="HDFC Mid-Cap Opportunities Fund",
                folio_number="HDFC-2023-8901",
                amount=5000,
                sip_day=5,
                start_date=date(2023, 1, 5),
                frequency=SIPFrequency.MONTHLY,
                status=SIPStatus.ACTIVE
            ),
            SIP(
                client_id=clients[1].id,
                fund_name="Axis Bluechip Fund",
                folio_number="AXIS-2023-5632",
                amount=3000,
                sip_day=10,
                start_date=date(2023, 2, 10),
                frequency=SIPFrequency.MONTHLY,
                status=SIPStatus.ACTIVE
            ),
            # Vikram Singh's SIPs
            SIP(
                client_id=clients[4].id,
                fund_name="ICICI Prudential Technology Fund",
                folio_number="ICICI-2024-1234",
                amount=10000,
                sip_day=1,
                start_date=date(2024, 1, 1),
                frequency=SIPFrequency.MONTHLY,
                status=SIPStatus.ACTIVE
            ),
            # Rajesh Kumar's SIPs
            SIP(
                client_id=clients[0].id,
                fund_name="SBI Small Cap Fund",
                folio_number="SBI-2024-9876",
                amount=4000,
                sip_day=15,
                start_date=date(2024, 3, 15),
                frequency=SIPFrequency.MONTHLY,
                status=SIPStatus.ACTIVE
            ),
        ]

        for sip in sips:
            db.add(sip)
        db.commit()
        print(f"✅ Created {len(sips)} SIPs")

        # Create sample meetings
        meetings = [
            Meeting(
                client_id=clients[0].id,
                meeting_date=datetime.now() + timedelta(days=2, hours=10),
                notes=f"Portfolio Review - {clients[0].name}\nAnnual portfolio review and financial planning",
                location="Office",
                meeting_type=MeetingType.IN_PERSON,
                duration=60
            ),
            Meeting(
                client_id=clients[1].id,
                meeting_date=datetime.now() + timedelta(days=5, hours=14),
                notes=f"Investment Strategy - {clients[1].name}\nDiscuss new investment opportunities",
                location="Video Call",
                meeting_type=MeetingType.VIDEO,
                duration=60
            ),
            Meeting(
                client_id=clients[4].id,
                meeting_date=datetime.now() + timedelta(days=7, hours=11),
                notes=f"Tax Planning - {clients[4].name}\nYear-end tax planning session",
                location="Client Office",
                meeting_type=MeetingType.IN_PERSON,
                duration=90
            ),
        ]

        for meeting in meetings:
            db.add(meeting)
        db.commit()
        print(f"✅ Created {len(meetings)} meetings")

        # Create sample reminders
        reminders = [
            Reminder(
                client_id=clients[3].id,
                reminder_type="policy_renewal",
                entity_type="policy",
                entity_id=policies[4].id,
                due_date=date.today() + timedelta(days=5),
                urgency="high",
                message=f"Policy {policies[4].policy_number} renewal due in 5 days\nSum Assured: ₹{policies[4].sum_assured:,}\nPremium: ₹{policies[4].premium_amount:,}",
                dismissed=False
            ),
            Reminder(
                client_id=clients[2].id,
                reminder_type="policy_renewal",
                entity_type="policy",
                entity_id=policies[3].id,
                due_date=date.today() + timedelta(days=25),
                urgency="medium",
                message=f"Policy {policies[3].policy_number} renewal due in 25 days\nSum Assured: ₹{policies[3].sum_assured:,}\nPremium: ₹{policies[3].premium_amount:,}",
                dismissed=False
            ),
            Reminder(
                client_id=clients[1].id,
                reminder_type="sip_due",
                entity_type="sip",
                entity_id=sips[0].id,
                due_date=date.today() + timedelta(days=3),
                urgency="medium",
                message=f"SIP payment due: {sips[0].fund_name}\nAmount: ₹{sips[0].amount:,}\nDue Date: {date.today() + timedelta(days=3)}",
                dismissed=False
            ),
        ]

        for reminder in reminders:
            db.add(reminder)
        db.commit()
        print(f"✅ Created {len(reminders)} reminders")

        print("\n✨ Sample data seeding complete!")
        print("\n📝 Login credentials:")
        print(f"   Email: demo@example.com")
        print(f"   Password: demo123")
        print(f"\n📊 Summary:")
        print(f"   • {len(clients)} Clients")
        print(f"   • {len(policies)} Policies")
        print(f"   • {len(sips)} SIPs")
        print(f"   • {len(meetings)} Meetings")
        print(f"   • {len(reminders)} Reminders")

if __name__ == "__main__":
    seed_sample_data()
