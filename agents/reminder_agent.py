"""
Agent 1: Renewal & SIP Reminder Agent

Runs daily to detect upcoming policy renewals and SIP due dates.
Generates reminders with appropriate urgency levels.

This is primarily deterministic with optional AI-enhanced messaging.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import Policy, SIP, Client, Reminder, PolicyStatus, SIPStatus
from database import get_db


class ReminderAgent:
    """
    Detects upcoming events and generates reminders
    No approval needed - read-only + notification generation
    """
    
    URGENCY_THRESHOLDS = {
        "high": 3,      # 3 days or less
        "medium": 7,    # 7 days or less
        "low": 30       # 30 days or less
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def run(self) -> Dict[str, int]:
        """
        Main execution method - called by scheduler
        Returns count of reminders generated
        """
        today = date.today()
        
        # Check policy renewals
        policy_reminders = self._check_policy_renewals(today)
        
        # Check SIP due dates
        sip_reminders = self._check_sip_due_dates(today)
        
        print(f"[ReminderAgent] Generated {len(policy_reminders)} policy reminders")
        print(f"[ReminderAgent] Generated {len(sip_reminders)} SIP reminders")
        
        return {
            "policy_reminders": len(policy_reminders),
            "sip_reminders": len(sip_reminders),
            "total": len(policy_reminders) + len(sip_reminders)
        }
    
    def _check_policy_renewals(self, today: date) -> List[Reminder]:
        """
        Check for upcoming policy renewals within 30 days
        """
        reminders = []
        
        # Calculate date ranges
        date_30d = today + timedelta(days=30)
        date_7d = today + timedelta(days=7)
        date_3d = today + timedelta(days=3)
        
        # Query active policies with upcoming renewals
        upcoming_policies = self.db.query(Policy).join(Client).filter(
            and_(
                Policy.status == PolicyStatus.ACTIVE,
                Policy.renewal_date <= date_30d,
                Policy.renewal_date >= today
            )
        ).all()
        
        for policy in upcoming_policies:
            days_until = (policy.renewal_date - today).days
            
            # Check if reminder already exists for this date
            existing = self.db.query(Reminder).filter(
                and_(
                    Reminder.entity_type == "policy",
                    Reminder.entity_id == policy.id,
                    Reminder.due_date == policy.renewal_date,
                    Reminder.dismissed == False
                )
            ).first()
            
            if existing:
                continue  # Skip if reminder already exists
            
            # Determine urgency
            if days_until <= self.URGENCY_THRESHOLDS["high"]:
                urgency = "high"
            elif days_until <= self.URGENCY_THRESHOLDS["medium"]:
                urgency = "medium"
            else:
                urgency = "low"
            
            # Generate reminder message
            message = self._generate_policy_renewal_message(
                policy, 
                policy.client, 
                days_until, 
                urgency
            )
            
            # Create reminder
            reminder = Reminder(
                reminder_type="policy_renewal",
                entity_type="policy",
                entity_id=policy.id,
                client_id=policy.client_id,
                message=message,
                urgency=urgency,
                due_date=policy.renewal_date
            )
            
            self.db.add(reminder)
            reminders.append(reminder)
        
        self.db.commit()
        return reminders
    
    def _check_sip_due_dates(self, today: date) -> List[Reminder]:
        """
        Check for SIPs due this month
        """
        reminders = []
        
        # Get current month's SIP day range
        current_day = today.day
        current_month = today.month
        
        # Query active SIPs
        active_sips = self.db.query(SIP).join(Client).filter(
            SIP.status == SIPStatus.ACTIVE
        ).all()
        
        for sip in active_sips:
            # Check if SIP is due this month
            sip_day_val = int(sip.sip_day)  # type: ignore[arg-type]
            if sip_day_val == current_day:  # type: ignore[comparison-overlap]
                # SIP is due today
                urgency = "high"
            elif sip_day_val > current_day and sip_day_val <= current_day + 7:  # type: ignore[comparison-overlap]
                # SIP due within next 7 days
                urgency = "medium"
            elif sip_day_val < current_day:  # type: ignore[comparison-overlap]
                # SIP was due earlier this month (might be missed)
                urgency = "high"
            else:
                continue  # Not urgent enough
            
            # Check if reminder already exists for this month
            existing = self.db.query(Reminder).filter(
                and_(
                    Reminder.entity_type == "sip",
                    Reminder.entity_id == sip.id,
                    Reminder.due_date >= date(today.year, today.month, 1),
                    Reminder.dismissed == False
                )
            ).first()
            
            if existing:
                continue
            
            # Calculate actual due date for this month
            try:
                due_date = date(today.year, today.month, sip_day_val)
            except ValueError:
                # Handle months with fewer days (e.g., Feb 30)
                import calendar
                last_day = calendar.monthrange(today.year, today.month)[1]
                due_date = date(today.year, today.month, min(sip_day_val, last_day))
            
            # Generate reminder message
            message = self._generate_sip_due_message(sip, sip.client, due_date, urgency)
            
            # Create reminder
            reminder = Reminder(
                reminder_type="sip_due",
                entity_type="sip",
                entity_id=sip.id,
                client_id=sip.client_id,
                message=message,
                urgency=urgency,
                due_date=due_date
            )
            
            self.db.add(reminder)
            reminders.append(reminder)
        
        self.db.commit()
        return reminders
    
    def _generate_policy_renewal_message(
        self, 
        policy: Policy, 
        client: Client, 
        days_until: int,
        urgency: str
    ) -> str:
        """
        Generate human-readable reminder message for policy renewal
        Can be enhanced with LLM for more personalized messages
        """
        if days_until == 0:
            time_text = "TODAY"
        elif days_until == 1:
            time_text = "TOMORROW"
        else:
            time_text = f"in {days_until} days"
        
        message = (
            f"Policy Renewal Due {time_text}\n"
            f"Client: {client.name}\n"
            f"Policy: {policy.policy_number} ({policy.provider})\n"
            f"Premium: ₹{policy.premium_amount:,.2f}\n"
            f"Renewal Date: {policy.renewal_date.strftime('%d-%b-%Y')}"
        )
        
        return message
    
    def _generate_sip_due_message(
        self,
        sip: SIP,
        client: Client,
        due_date: date,
        urgency: str
    ) -> str:
        """
        Generate human-readable reminder message for SIP
        """
        days_diff = (due_date - date.today()).days
        
        if days_diff == 0:
            time_text = "TODAY"
        elif days_diff == 1:
            time_text = "TOMORROW"
        elif days_diff < 0:
            time_text = f"{abs(days_diff)} days ago (MISSED?)"
        else:
            time_text = f"in {days_diff} days"
        
        message = (
            f"SIP Due {time_text}\n"
            f"Client: {client.name}\n"
            f"Fund: {sip.fund_name}\n"
            f"Amount: ₹{sip.amount:,.2f}\n"
            f"SIP Day: {sip.sip_day} of every month"
        )
        
        return message
    
    def get_upcoming_reminders(
        self, 
        days_ahead: int = 30,
        dismissed: bool = False
    ) -> List[Reminder]:
        """
        Get all upcoming reminders for dashboard display
        """
        today = date.today()
        future_date = today + timedelta(days=days_ahead)
        
        reminders = self.db.query(Reminder).filter(
            and_(
                Reminder.due_date >= today,
                Reminder.due_date <= future_date,
                Reminder.dismissed == dismissed
            )
        ).order_by(Reminder.due_date, Reminder.urgency.desc()).all()
        
        return reminders
    
    def dismiss_reminder(self, reminder_id: int) -> bool:
        """
        Mark a reminder as dismissed
        """
        reminder = self.db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            reminder.dismissed = True  # type: ignore[assignment]
            reminder.dismissed_at = datetime.utcnow()  # type: ignore[assignment]
            self.db.commit()
            return True
        return False


# Standalone function for scheduler
def run_reminder_agent():
    """
    Function to be called by APScheduler
    """
    from database import get_db
    
    with get_db() as db:
        agent = ReminderAgent(db)
        result = agent.run()
        print(f"[Scheduler] Reminder Agent completed: {result}")
        return result


if __name__ == "__main__":
    # Test the agent
    from database import get_db
    
    with get_db() as db:
        agent = ReminderAgent(db)
        result = agent.run()
        print(f"\nAgent Results: {result}")
        
        print("\nUpcoming Reminders:")
        reminders = agent.get_upcoming_reminders(days_ahead=30)
        for r in reminders:
            print(f"  [{r.urgency}] {r.reminder_type} - {r.message[:50]}...")
