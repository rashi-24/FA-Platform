"""
Sample data generator for development and testing
Creates realistic financial advisory data
"""

from datetime import datetime, date, timedelta
import random
from sqlalchemy.orm import Session

from models import (
    Client, Policy, SIP, Meeting, 
    PolicyStatus, SIPStatus, SIPFrequency
)
from database import get_db, init_db


# Sample data pools
FIRST_NAMES = [
    "Rajesh", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Rohan", "Kavya",
    "Arjun", "Meera", "Karthik", "Divya", "Rahul", "Pooja", "Sanjay", "Nisha"
]

LAST_NAMES = [
    "Sharma", "Kumar", "Patel", "Singh", "Reddy", "Nair", "Iyer", "Gupta",
    "Mehta", "Desai", "Joshi", "Verma", "Rao", "Pillai", "Agarwal", "Shah"
]

INSURANCE_PROVIDERS = [
    "LIC of India", "HDFC Life", "ICICI Prudential", "Max Life", "SBI Life",
    "Bajaj Allianz", "Kotak Life", "Tata AIA", "Birla Sun Life"
]

POLICY_TYPES = [
    "Term Insurance", "Endowment Plan", "ULIP", "Money Back Policy",
    "Whole Life Insurance", "Child Insurance Plan", "Pension Plan"
]

MUTUAL_FUNDS = [
    "HDFC Equity Fund", "ICICI Prudential Bluechip Fund", "SBI Small Cap Fund",
    "Axis Long Term Equity Fund", "Mirae Asset Emerging Bluechip",
    "Parag Parikh Flexi Cap Fund", "Kotak Standard Multicap Fund",
    "UTI Nifty Index Fund", "DSP Tax Saver Fund", "Franklin India Prima Fund"
]

MEETING_NOTES_TEMPLATES = [
    "Discussed portfolio performance. Client satisfied with returns. Suggested increasing SIP amount.",
    "Reviewed insurance coverage. Client needs additional term insurance of ₹1 crore.",
    "Client planning daughter's education abroad. Discussed debt funds for 3-year horizon.",
    "Annual review meeting. Portfolio up 12% YoY. No changes needed currently.",
    "Client concerned about market volatility. Reassured with long-term perspective.",
    "Discussed tax saving investments. Recommended ELSS funds and PPF.",
    "Client retiring in 5 years. Started planning for income generation portfolio.",
    "New policy renewal due next month. Client confirmed payment.",
]


def generate_phone():
    """Generate random Indian phone number"""
    return f"+91{random.randint(7000000000, 9999999999)}"


def generate_email(name):
    """Generate email from name"""
    clean_name = name.lower().replace(" ", ".")
    domains = ["gmail.com", "yahoo.com", "outlook.com", "rediffmail.com"]
    return f"{clean_name}@{random.choice(domains)}"


def random_date(start_days_ago, end_days_ago=0):
    """Generate random date within range"""
    start = date.today() - timedelta(days=start_days_ago)
    end = date.today() - timedelta(days=end_days_ago)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def create_sample_clients(db: Session, count: int = 20) -> list:
    """Create sample clients"""
    clients = []
    
    for _ in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        
        client = Client(
            name=name,
            phone=generate_phone(),
            email=generate_email(name),
            address=f"{random.randint(1, 999)}, {random.choice(['MG Road', 'Brigade Road', 'Residency Road', 'Koramangala', 'Indiranagar'])}, Bangalore - {random.randint(560001, 560100)}",
            notes=f"Client since {random.randint(2015, 2023)}. {random.choice(['Conservative', 'Moderate', 'Aggressive'])} risk profile."
        )
        db.add(client)
        clients.append(client)
    
    db.commit()
    print(f"Created {count} clients")
    return clients


def create_sample_policies(db: Session, clients: list) -> list:
    """Create sample policies for clients"""
    policies = []
    
    for client in clients:
        # Each client has 1-3 policies
        num_policies = random.randint(1, 3)
        
        for i in range(num_policies):
            # Random renewal date (some in past, some upcoming)
            renewal_date = date.today() + timedelta(days=random.randint(-90, 365))
            
            policy = Policy(
                client_id=client.id,
                policy_number=f"POL{random.randint(100000, 999999)}",
                provider=random.choice(INSURANCE_PROVIDERS),
                policy_type=random.choice(POLICY_TYPES),
                premium_amount=random.choice([5000, 10000, 15000, 25000, 50000, 75000, 100000]),
                premium_frequency=random.choice(["monthly", "quarterly", "yearly"]),
                renewal_date=renewal_date,
                maturity_date=renewal_date + timedelta(days=random.randint(1825, 7300)),  # 5-20 years
                sum_assured=random.choice([500000, 1000000, 2500000, 5000000, 10000000]),
                status=random.choices(
                    [PolicyStatus.ACTIVE, PolicyStatus.LAPSED],
                    weights=[0.9, 0.1]
                )[0],
                notes=f"Policy started on {random_date(1825, 365).strftime('%Y-%m-%d')}"
            )
            db.add(policy)
            policies.append(policy)
    
    db.commit()
    print(f"Created {len(policies)} policies")
    return policies


def create_sample_sips(db: Session, clients: list) -> list:
    """Create sample SIPs for clients"""
    sips = []
    
    for client in clients:
        # Each client has 0-4 SIPs
        num_sips = random.randint(0, 4)
        
        for i in range(num_sips):
            start_date = random_date(730, 90)  # Started 2 years to 3 months ago
            
            sip = SIP(
                client_id=client.id,
                fund_name=random.choice(MUTUAL_FUNDS),
                folio_number=f"FOL{random.randint(10000000, 99999999)}",
                amount=random.choice([1000, 2000, 3000, 5000, 10000, 15000, 25000]),
                frequency=random.choices(
                    [SIPFrequency.MONTHLY, SIPFrequency.QUARTERLY],
                    weights=[0.9, 0.1]
                )[0],
                sip_day=random.randint(1, 28),
                start_date=start_date,
                end_date=None if random.random() > 0.1 else start_date + timedelta(days=random.randint(365, 1825)),
                status=random.choices(
                    [SIPStatus.ACTIVE, SIPStatus.PAUSED, SIPStatus.STOPPED],
                    weights=[0.85, 0.10, 0.05]
                )[0],
                notes=f"Target: {random.choice(['Retirement', 'Child Education', 'Wealth Creation', 'Tax Saving'])}"
            )
            db.add(sip)
            sips.append(sip)
    
    db.commit()
    print(f"Created {len(sips)} SIPs")
    return sips


def create_sample_meetings(db: Session, clients: list) -> list:
    """Create sample meeting records"""
    meetings = []
    
    # Create 30-50 meetings across clients
    num_meetings = random.randint(30, 50)
    
    for _ in range(num_meetings):
        client = random.choice(clients)
        meeting_date = datetime.combine(
            random_date(365, 0),
            datetime.min.time()
        ) + timedelta(hours=random.randint(9, 17))
        
        meeting = Meeting(
            client_id=client.id,
            meeting_date=meeting_date,
            notes=random.choice(MEETING_NOTES_TEMPLATES),
            action_items=[
                {
                    "action": random.choice([
                        "Follow up on policy renewal",
                        "Send investment performance report",
                        "Schedule next review meeting",
                        "Process SIP increase"
                    ]),
                    "due_date": (date.today() + timedelta(days=random.randint(7, 30))).isoformat(),
                    "completed": random.choice([True, False])
                }
            ] if random.random() > 0.5 else None
        )
        db.add(meeting)
        meetings.append(meeting)
    
    db.commit()
    print(f"Created {len(meetings)} meetings")
    return meetings


def generate_all_sample_data(db: Session):
    """
    Generate complete sample dataset
    """
    print("=" * 60)
    print("Generating sample data for Financial Advisor Platform")
    print("=" * 60)
    
    # Create clients
    clients = create_sample_clients(db, count=20)
    
    # Create policies
    policies = create_sample_policies(db, clients)
    
    # Create SIPs
    sips = create_sample_sips(db, clients)
    
    # Create meetings
    meetings = create_sample_meetings(db, clients)
    
    print("=" * 60)
    print("Sample data generation complete!")
    print(f"  Clients: {len(clients)}")
    print(f"  Policies: {len(policies)}")
    print(f"  SIPs: {len(sips)}")
    print(f"  Meetings: {len(meetings)}")
    print("=" * 60)
    
    return {
        "clients": clients,
        "policies": policies,
        "sips": sips,
        "meetings": meetings
    }


def main():
    """Main function to initialize DB and generate data"""
    print("Initializing database...")
    init_db()
    
    with get_db() as db:
        generate_all_sample_data(db)


if __name__ == "__main__":
    main()
