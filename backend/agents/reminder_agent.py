"""
Reminder Agent
Generates reminders for policy renewals and SIP due dates
Sends email notifications based on cadence (10/3/1 days)
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime, timedelta, timezone
from typing import List
import logging

from models import Reminder, Policy, SIP, PolicyStatus, SIPStatus

logger = logging.getLogger(__name__)


class ReminderAgent:
    """Agent that generates and manages reminders for policies and SIPs"""

    def __init__(self, db: Session):
        self.db = db

    def run(self) -> dict:
        """Main execution: scan for upcoming renewals/SIPs and create reminders"""
        created_count = 0

        # Generate policy renewal reminders
        created_count += self._generate_policy_reminders()

        # Generate SIP due date reminders
        created_count += self._generate_sip_reminders()

        return {"reminders_created": created_count, "status": "success"}

    def _generate_policy_reminders(self) -> int:
        """Generate reminders for upcoming policy renewals"""
        today = date.today()
        date_30d = today + timedelta(days=30)

        # Find policies renewing in next 30 days
        policies = (
            self.db.query(Policy)
            .filter(
                and_(
                    Policy.renewal_date >= today,
                    Policy.renewal_date <= date_30d,
                    Policy.status == PolicyStatus.ACTIVE,
                )
            )
            .all()
        )

        created = 0
        for policy in policies:
            # Check if reminder already exists
            existing = (
                self.db.query(Reminder)
                .filter(
                    and_(
                        Reminder.entity_type == "policy",
                        Reminder.entity_id == policy.id,
                        Reminder.dismissed.is_(False),
                    )
                )
                .first()
            )

            if not existing:
                days_until = (policy.renewal_date - today).days

                if days_until <= 7:
                    urgency = "high"
                elif days_until <= 14:
                    urgency = "medium"
                else:
                    urgency = "low"

                message = f"Policy {policy.policy_number} renewal due on {policy.renewal_date}"

                reminder = Reminder(
                    reminder_type="policy_renewal",
                    entity_type="policy",
                    entity_id=policy.id,
                    client_id=policy.client_id,
                    message=message,
                    urgency=urgency,
                    due_date=policy.renewal_date,
                )
                self.db.add(reminder)
                created += 1

                # Send email based on cadence (10/3/1 days before)
                if days_until in [10, 3, 1] and policy.client.email:
                    self._send_policy_email(policy, days_until, reminder)

        self.db.commit()
        return created

    def _generate_sip_reminders(self) -> int:
        """Generate reminders for upcoming SIP payments"""
        today = date.today()
        current_day = today.day

        # Find SIPs due this month
        sips = (
            self.db.query(SIP)
            .filter(and_(SIP.sip_day >= current_day, SIP.status == SIPStatus.ACTIVE))
            .all()
        )

        created = 0
        for sip in sips:
            # Check if reminder already exists for this month
            existing = (
                self.db.query(Reminder)
                .filter(
                    and_(
                        Reminder.entity_type == "sip",
                        Reminder.entity_id == sip.id,
                        Reminder.dismissed.is_(False),
                        Reminder.due_date >= today.replace(day=1),  # This month
                    )
                )
                .first()
            )

            if not existing:
                days_until = sip.sip_day - current_day

                if days_until <= 3:
                    urgency = "high"
                elif days_until <= 7:
                    urgency = "medium"
                else:
                    urgency = "low"

                due_date = today.replace(day=sip.sip_day)
                message = f"SIP payment due for {sip.fund_name} on day {sip.sip_day}"

                # Send email for SIP reminder if client has email
                send_sip_email = sip.client.email and days_until in [3, 1]

                reminder = Reminder(
                    reminder_type="sip_due",
                    entity_type="sip",
                    entity_id=sip.id,
                    client_id=sip.client_id,
                    message=message,
                    urgency=urgency,
                    due_date=due_date,
                )
                self.db.add(reminder)
                created += 1

                # Send email if applicable
                if send_sip_email:
                    self._send_sip_email(sip, reminder)

        self.db.commit()
        return created

    def get_upcoming_reminders(
        self, days_ahead: int = 30, dismissed: bool = False
    ) -> List[Reminder]:
        """Get upcoming reminders"""
        today = date.today()
        future_date = today + timedelta(days=days_ahead)

        query = (
            self.db.query(Reminder)
            .filter(
                and_(
                    Reminder.due_date >= today,
                    Reminder.due_date <= future_date,
                    Reminder.dismissed.is_(dismissed),
                )
            )
            .order_by(Reminder.due_date, Reminder.urgency.desc())
        )

        return query.all()

    def dismiss_reminder(self, reminder_id: int) -> bool:
        """Dismiss a reminder"""
        reminder = self.db.query(Reminder).filter(Reminder.id == reminder_id).first()

        if not reminder:
            return False

        reminder.dismissed = True
        reminder.dismissed_at = datetime.now(timezone.utc)
        self.db.commit()

        return True

    def _send_policy_email(self, policy: Policy, days_until: int, reminder: Reminder):
        """
        Send policy renewal reminder email
        Updates reminder email status
        """
        try:
            from services.email_service import get_email_service

            email_service = get_email_service()
            success = email_service.send_policy_renewal_reminder(
                client_name=policy.client.name,
                client_email=policy.client.email,
                policy_number=policy.policy_number,
                provider=policy.provider,
                renewal_date=policy.renewal_date,
                days_until=days_until
            )

            # Update reminder email status
            reminder.email_sent = success
            reminder.email_sent_at = datetime.now(timezone.utc) if success else None
            reminder.email_status = "sent" if success else "failed"

            logger.info(f"Policy reminder email {'sent' if success else 'failed'} to {policy.client.email}")

        except Exception as e:
            logger.error(f"Failed to send policy reminder email: {e}")
            reminder.email_status = "failed"

    def _send_sip_email(self, sip: SIP, reminder: Reminder):
        """
        Send SIP payment reminder email
        Updates reminder email status
        """
        try:
            from services.email_service import get_email_service

            email_service = get_email_service()
            success = email_service.send_sip_due_reminder(
                client_name=sip.client.name,
                client_email=sip.client.email,
                fund_name=sip.fund_name,
                amount=sip.amount,
                sip_day=sip.sip_day
            )

            # Update reminder email status
            reminder.email_sent = success
            reminder.email_sent_at = datetime.now(timezone.utc) if success else None
            reminder.email_status = "sent" if success else "failed"

            logger.info(f"SIP reminder email {'sent' if success else 'failed'} to {sip.client.email}")

        except Exception as e:
            logger.error(f"Failed to send SIP reminder email: {e}")
            reminder.email_status = "failed"
