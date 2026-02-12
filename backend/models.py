"""
Database models for Financial Advisor Platform
SQLAlchemy ORM definitions with relationships and constraints
"""

from datetime import datetime, date, timezone
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Enum,
    Boolean,
    CheckConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


# Helper function for timezone-aware datetime defaults
def utc_now():
    """Return current UTC time with timezone info"""
    return datetime.now(timezone.utc)


# Enums for type safety
class PolicyStatus(str, enum.Enum):
    ACTIVE = "active"
    LAPSED = "lapsed"
    SURRENDERED = "surrendered"
    MATURED = "matured"


class SIPStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class SIPFrequency(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class MeetingType(str, enum.Enum):
    IN_PERSON = "in-person"
    VIDEO = "video"
    PHONE = "phone"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AuditAction(str, enum.Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


# Core Business Entities


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    last_contact_date = Column(Date, nullable=True)  # Last meeting/interaction date

    # Metadata
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    policies = relationship(
        "Policy", back_populates="client", cascade="all, delete-orphan"
    )
    sips = relationship("SIP", back_populates="client", cascade="all, delete-orphan")
    meetings = relationship(
        "Meeting", back_populates="client", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', phone='{self.phone}')>"


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(
        Integer,
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    policy_number = Column(String(100), unique=True, nullable=False, index=True)
    provider = Column(String(255), nullable=False)  # e.g., LIC, HDFC Life, Max Life
    policy_type = Column(String(100), nullable=False)  # e.g., Term, Endowment, ULIP

    premium_amount = Column(Float, nullable=False)
    premium_frequency = Column(
        String(20), default="yearly"
    )  # monthly, quarterly, yearly

    renewal_date = Column(Date, nullable=False, index=True)
    maturity_date = Column(Date, nullable=True)
    sum_assured = Column(Float, nullable=True)

    status = Column(Enum(PolicyStatus), default=PolicyStatus.ACTIVE, nullable=False)

    notes = Column(Text, nullable=True)

    # Payment tracking
    last_payment_date = Column(Date, nullable=True)
    payment_confirmed = Column(Boolean, default=False, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    client = relationship("Client", back_populates="policies")

    # Constraints
    __table_args__ = (
        CheckConstraint("premium_amount > 0", name="check_premium_positive"),
    )

    def __repr__(self):
        return f"<Policy(id={self.id}, number='{self.policy_number}', client_id={self.client_id})>"


class SIP(Base):
    __tablename__ = "sips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(
        Integer,
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    fund_name = Column(String(255), nullable=False)
    folio_number = Column(String(100), nullable=True)

    amount = Column(Float, nullable=False)
    frequency = Column(Enum(SIPFrequency), default=SIPFrequency.MONTHLY, nullable=False)
    sip_day = Column(Integer, nullable=False)  # 1-31

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # null = ongoing

    status = Column(Enum(SIPStatus), default=SIPStatus.ACTIVE, nullable=False)

    notes = Column(Text, nullable=True)

    # Payment tracking
    last_payment_date = Column(Date, nullable=True)
    payment_confirmed = Column(Boolean, default=False, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    client = relationship("Client", back_populates="sips")

    # Constraints
    __table_args__ = (
        CheckConstraint("amount > 0", name="check_sip_amount_positive"),
        CheckConstraint("sip_day >= 1 AND sip_day <= 31", name="check_sip_day_range"),
    )

    def __repr__(self):
        return f"<SIP(id={self.id}, fund='{self.fund_name}', amount={self.amount}, client_id={self.client_id})>"


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(
        Integer,
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    meeting_date = Column(DateTime, nullable=False, index=True)
    notes = Column(Text, nullable=False)

    # Meeting details
    duration = Column(Integer, default=60, nullable=False)  # Duration in minutes
    location = Column(String(255), nullable=True)  # Meeting location or video link
    meeting_type = Column(Enum(MeetingType), default=MeetingType.IN_PERSON, nullable=False)

    # AI-extracted action items (stored as JSON array)
    action_items = Column(JSON, nullable=True)
    # Example: [{"action": "Follow up on policy renewal", "due_date": "2025-03-01", "completed": false}]

    # Metadata
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    client = relationship("Client", back_populates="meetings")

    def __repr__(self):
        return f"<Meeting(id={self.id}, client_id={self.client_id}, date={self.meeting_date})>"


# AI System Entities


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # excel, csv, pdf
    file_path = Column(String(500), nullable=True)  # storage path

    status = Column(
        Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True
    )

    # Parsed data from file (raw)
    parsed_data = Column(JSON, nullable=True)

    # AI-proposed actions (INSERT/UPDATE/SKIP for each row)
    proposed_actions = Column(JSON, nullable=True)
    # Example: [{"row": 1, "action": "INSERT", "entity": "client", "data": {...}, "reasoning": "..."}]

    agent_reasoning = Column(Text, nullable=True)

    # Approval tracking
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    error_message = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self):
        return f"<IngestionJob(id={self.id}, file='{self.filename}', status={self.status})>"


class ApprovalQueue(Base):
    __tablename__ = "approval_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)

    job_type = Column(String(50), nullable=False)  # ingestion, document, meeting_action
    job_id = Column(Integer, nullable=True)  # FK to ingestion_jobs, meetings, etc.

    entity_type = Column(String(50), nullable=False)  # client, policy, sip
    action_type = Column(Enum(AuditAction), nullable=False)  # INSERT, UPDATE, DELETE

    # Proposed data (what will be inserted/updated)
    proposed_data = Column(JSON, nullable=False)

    agent_reasoning = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0.0 - 1.0

    status = Column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False, index=True
    )

    # Review tracking
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=utc_now, nullable=False)

    def __repr__(self):
        return (
            f"<ApprovalQueue(id={self.id}, type={self.job_type}, status={self.status})>"
        )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    entity_type = Column(
        String(50), nullable=False, index=True
    )  # client, policy, sip, meeting
    entity_id = Column(Integer, nullable=False, index=True)

    action = Column(Enum(AuditAction), nullable=False)

    # JSON snapshots of data before/after
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    # Who initiated this action
    initiated_by = Column(
        String(100), nullable=False
    )  # "advisor" or "agent:<agent_name>"
    approved_by = Column(String(100), nullable=True)

    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, entity={self.entity_type}:{self.entity_id}, action={self.action})>"


class Reminder(Base):
    """
    Stores generated reminders for policies and SIPs
    Created by Reminder Agent
    """

    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)

    reminder_type = Column(String(20), nullable=False)  # policy_renewal, sip_due
    entity_type = Column(String(20), nullable=False)  # policy, sip
    entity_id = Column(Integer, nullable=False, index=True)

    client_id = Column(
        Integer,
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    message = Column(Text, nullable=False)
    urgency = Column(String(20), nullable=False)  # high, medium, low

    due_date = Column(Date, nullable=False, index=True)

    # Notification status
    notified = Column(Boolean, default=False, nullable=False)
    notified_at = Column(DateTime, nullable=True)

    # Email tracking
    email_sent = Column(Boolean, default=False, nullable=False)
    email_sent_at = Column(DateTime, nullable=True)
    email_status = Column(String(20), nullable=True)  # sent, failed, bounced

    dismissed = Column(Boolean, default=False, nullable=False)
    dismissed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)

    def __repr__(self):
        return f"<Reminder(id={self.id}, type={self.reminder_type}, urgency={self.urgency})>"


# Optional: User/Advisor table (for future multi-user support)
class Advisor(Base):
    __tablename__ = "advisors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # Use bcrypt/argon2
    full_name = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Advisor(id={self.id}, username='{self.username}')>"
