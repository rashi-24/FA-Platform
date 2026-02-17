"""
Pydantic schemas for request/response validation
Ensures type safety and automatic API documentation
"""

import re
from pydantic import BaseModel, Field, validator, EmailStr
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum


# Enums (matching database enums)


class PolicyStatusEnum(str, Enum):
    ACTIVE = "active"
    LAPSED = "lapsed"
    SURRENDERED = "surrendered"
    MATURED = "matured"


class SIPStatusEnum(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class SIPFrequencyEnum(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


# Client Schemas


class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$")
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{10,15}$")
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class ClientResponse(ClientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClientWithRelations(ClientResponse):
    """Client with associated policies, SIPs, etc."""

    policies: List["PolicyResponse"] = []
    sips: List["SIPResponse"] = []

    class Config:
        from_attributes = True


# Policy Schemas


class PolicyBase(BaseModel):
    client_id: int
    policy_number: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., min_length=1, max_length=255)
    policy_type: str = Field(..., min_length=1, max_length=100)
    premium_amount: float = Field(..., gt=0)
    premium_frequency: str = "yearly"
    renewal_date: date
    maturity_date: Optional[date] = None
    sum_assured: Optional[float] = Field(None, gt=0)
    status: PolicyStatusEnum = PolicyStatusEnum.ACTIVE
    notes: Optional[str] = None

    @validator("maturity_date")
    def validate_maturity_date(cls, v, values):
        if v and "renewal_date" in values and v < values["renewal_date"]:
            raise ValueError("Maturity date cannot be before renewal date")
        return v


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(BaseModel):
    policy_number: Optional[str] = Field(None, min_length=1, max_length=100)
    provider: Optional[str] = None
    policy_type: Optional[str] = None
    premium_amount: Optional[float] = Field(None, gt=0)
    premium_frequency: Optional[str] = None
    renewal_date: Optional[date] = None
    maturity_date: Optional[date] = None
    sum_assured: Optional[float] = Field(None, gt=0)
    status: Optional[PolicyStatusEnum] = None
    notes: Optional[str] = None


class PolicyResponse(PolicyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PolicyWithClient(PolicyResponse):
    """Policy response with client information"""

    client_name: Optional[str] = None
    client_phone: Optional[str] = None


# SIP Schemas


class SIPBase(BaseModel):
    client_id: int
    fund_name: str = Field(..., min_length=1, max_length=255)
    folio_number: Optional[str] = Field(None, max_length=100)
    amount: float = Field(..., gt=0)
    frequency: SIPFrequencyEnum = SIPFrequencyEnum.MONTHLY
    sip_day: int = Field(..., ge=1, le=31)
    start_date: date
    end_date: Optional[date] = None
    status: SIPStatusEnum = SIPStatusEnum.ACTIVE
    notes: Optional[str] = None

    @validator("end_date")
    def validate_end_date(cls, v, values):
        if v and "start_date" in values and v < values["start_date"]:
            raise ValueError("End date cannot be before start date")
        return v


class SIPCreate(SIPBase):
    pass


class SIPUpdate(BaseModel):
    fund_name: Optional[str] = None
    folio_number: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    frequency: Optional[SIPFrequencyEnum] = None
    sip_day: Optional[int] = Field(None, ge=1, le=31)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[SIPStatusEnum] = None
    notes: Optional[str] = None


class SIPResponse(SIPBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SIPWithClient(SIPResponse):
    """SIP response with client information"""

    client_name: Optional[str] = None
    client_phone: Optional[str] = None


# Meeting Schemas


class ActionItem(BaseModel):
    action: str
    due_date: Optional[date] = None
    completed: bool = False


class MeetingBase(BaseModel):
    client_id: int
    meeting_date: datetime
    notes: str = Field(..., min_length=1)
    action_items: Optional[List[ActionItem]] = None


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    meeting_date: Optional[datetime] = None
    notes: Optional[str] = None
    action_items: Optional[List[ActionItem]] = None


class MeetingResponse(MeetingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# AI Agent Schemas


class DocumentExtractionRequest(BaseModel):
    """Request schema for Document Intelligence Agent"""

    file_path: str
    file_type: str = Field(..., pattern=r"^(pdf|jpg|jpeg|png)$")


class DocumentExtractionResponse(BaseModel):
    """Response from Document Intelligence Agent"""

    success: bool
    extracted_data: Dict[str, Any]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    proposed_action: str  # INSERT or UPDATE
    requires_approval: bool = True
    reasoning: str


class ExcelIngestionRequest(BaseModel):
    """Request schema for Excel Ingestion Agent"""

    file_path: str
    sheet_name: Optional[str] = None


class ProposedAction(BaseModel):
    row_number: int
    action: str  # INSERT, UPDATE, SKIP
    entity_type: str  # client, policy, sip
    data: Dict[str, Any]
    reasoning: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ExcelIngestionResponse(BaseModel):
    """Response from Excel Ingestion Agent"""

    success: bool
    total_rows: int
    proposed_actions: List[ProposedAction]
    overall_reasoning: str


class MeetingNotesRequest(BaseModel):
    """Request schema for Meeting Notes Agent"""

    client_id: int
    meeting_date: datetime
    notes: str = Field(..., min_length=1)


class ExtractedAction(BaseModel):
    action_type: str  # new_sip, policy_change, follow_up
    description: str
    proposed_data: Dict[str, Any]
    due_date: Optional[date] = None
    confidence: float


class MeetingNotesResponse(BaseModel):
    """Response from Meeting Notes Agent"""

    success: bool
    extracted_actions: List[ExtractedAction]
    meeting_summary: str


class InsightQueryRequest(BaseModel):
    """Request schema for Advisor Insight Agent"""

    query: str = Field(..., min_length=1, max_length=500)


class InsightQueryResponse(BaseModel):
    """Response from Advisor Insight Agent"""

    success: bool
    results: List[Dict[str, Any]]
    sql_query: Optional[str] = None  # For transparency
    explanation: str


# Approval Queue Schemas


class ApprovalRequest(BaseModel):
    """Approve or reject a pending action"""

    approval_id: int
    approved: bool
    review_notes: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    job_type: str
    entity_type: str
    action_type: str
    proposed_data: Dict[str, Any]
    agent_reasoning: Optional[str] = None
    confidence_score: Optional[float] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Reminder Schemas


class ReminderResponse(BaseModel):
    id: int
    reminder_type: str
    entity_type: str
    entity_id: int
    client_id: int
    message: str
    urgency: str
    due_date: date
    notified: bool
    dismissed: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Dashboard Summary Schema


class DashboardSummary(BaseModel):
    """Aggregated stats for dashboard"""

    total_clients: int
    total_policies: int
    total_active_sips: int
    total_aum: float
    upcoming_renewals_30d: int
    upcoming_sips_this_month: int
    pending_approvals: int
    recent_meetings: int


# Audit Log Schema


class AuditLogResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    initiated_by: str
    approved_by: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# Generic response wrapper
class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


# Authentication Schemas


class AdvisorRegister(BaseModel):
    """Schema for advisor registration"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)

    @validator("password")
    def validate_password_strength(cls, value):
        """
        SECURITY: Enforce password complexity requirements
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")

        return value


class AdvisorLogin(BaseModel):
    """Schema for advisor login"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class AdvisorResponse(BaseModel):
    """Schema for advisor profile response"""

    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# Resolve forward references for Pydantic v2
ClientWithRelations.model_rebuild()
