"""
Main FastAPI Application
Financial Advisor Platform Backend
"""

import logging
import sys
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, cast
from datetime import datetime, date, timedelta
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from database import get_db_session
from models import Client, Policy, SIP, Meeting, ApprovalQueue, AuditLog, Advisor, SIPFrequency
from schemas import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientWithRelations,
    PolicyCreate,
    PolicyUpdate,
    PolicyResponse,
    PolicyWithClient,
    SIPCreate,
    SIPResponse,
    SIPWithClient,
    MeetingCreate,
    MeetingResponse,
    ApprovalRequest,
    ApprovalResponse,
    ReminderResponse,
    DashboardSummary,
    AuditLogResponse,
    SuccessResponse,
    AdvisorRegister,
    AdvisorLogin,
    TokenResponse,
    AdvisorResponse,
)
from auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# Create FastAPI app
app = FastAPI(
    title="Financial Advisor Platform",
    description="Agentic AI-powered platform for financial advisory operations",
    version="1.0.0",
)

# CORS middleware - SECURITY: Configure allowed origins via environment variable
# CRITICAL: Never use ["*"] with allow_credentials=True in production
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Whitelist specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # Explicit methods
    allow_headers=["Content-Type", "Authorization"],  # Explicit headers
)

# Mount static files (for frontend)
# app.mount("/static", StaticFiles(directory="frontend"), name="static")


# ==================== Health & Info ====================


@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Financial Advisor Platform API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    from datetime import timezone

    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}


# ==================== Authentication ====================


@app.post("/api/auth/register", response_model=AdvisorResponse, status_code=status.HTTP_201_CREATED)
def register_advisor(advisor_data: AdvisorRegister, db: Session = Depends(get_db_session)):
    """
    Register a new advisor account
    """
    # Check if email already exists
    existing_advisor = db.query(Advisor).filter(Advisor.email == advisor_data.email).first()
    if existing_advisor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    existing_username = db.query(Advisor).filter(Advisor.username == advisor_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Create new advisor
    new_advisor = Advisor(
        username=advisor_data.username,
        email=advisor_data.email,
        password_hash=get_password_hash(advisor_data.password),
        full_name=advisor_data.full_name,
        is_active=True
    )

    db.add(new_advisor)
    db.commit()
    db.refresh(new_advisor)

    return new_advisor


@app.post("/api/auth/login", response_model=TokenResponse)
def login_advisor(login_data: AdvisorLogin, db: Session = Depends(get_db_session)):
    """
    Login with email and password, returns JWT token
    """
    advisor = authenticate_user(db, login_data.email, login_data.password)
    if not advisor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    from datetime import timezone
    advisor.last_login = datetime.now(timezone.utc)
    db.commit()

    # Create access token
    access_token = create_access_token(data={"sub": advisor.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }


@app.post("/api/auth/refresh", response_model=TokenResponse)
def refresh_token(current_user: Advisor = Depends(get_current_user)):
    """
    Refresh access token (requires valid existing token)
    """
    access_token = create_access_token(data={"sub": current_user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@app.get("/api/auth/me", response_model=AdvisorResponse)
def get_current_advisor_info(current_user: Advisor = Depends(get_current_user)):
    """
    Get current authenticated advisor information
    """
    return current_user


# ==================== Dashboard ====================


@app.get("/api/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db_session)):
    """
    Get aggregated dashboard statistics
    """
    from sqlalchemy import func, and_
    from models import PolicyStatus, SIPStatus, ApprovalStatus

    # Total clients
    total_clients = db.query(func.count(Client.id)).scalar()

    # Total policies
    total_policies = db.query(func.count(Policy.id)).scalar()

    # Total active SIPs
    total_active_sips = (
        db.query(func.count(SIP.id)).filter(SIP.status == SIPStatus.ACTIVE).scalar()
    )

    # Total AUM (sum of all active SIP amounts * 12 for yearly)
    # Simplified calculation
    total_aum = (
        db.query(func.sum(SIP.amount)).filter(SIP.status == SIPStatus.ACTIVE).scalar()
        or 0
    )
    total_aum = total_aum * 12  # Rough yearly estimate

    # Upcoming renewals (next 30 days)
    today = date.today()
    date_30d = today + timedelta(days=30)
    upcoming_renewals_30d = (
        db.query(func.count(Policy.id))
        .filter(
            and_(
                Policy.renewal_date >= today,
                Policy.renewal_date <= date_30d,
                Policy.status == PolicyStatus.ACTIVE,
            )
        )
        .scalar()
    )

    # Upcoming SIPs this month
    current_day = today.day
    upcoming_sips_this_month = (
        db.query(func.count(SIP.id))
        .filter(and_(SIP.sip_day >= current_day, SIP.status == SIPStatus.ACTIVE))
        .scalar()
    )

    # Pending approvals
    pending_approvals = (
        db.query(func.count(ApprovalQueue.id))
        .filter(ApprovalQueue.status == ApprovalStatus.PENDING)
        .scalar()
    )

    # Recent meetings (last 7 days)
    date_7d_ago = today - timedelta(days=7)
    recent_meetings = (
        db.query(func.count(Meeting.id))
        .filter(
            Meeting.meeting_date >= datetime.combine(date_7d_ago, datetime.min.time())
        )
        .scalar()
    )

    return DashboardSummary(
        total_clients=total_clients,
        total_policies=total_policies,
        total_active_sips=total_active_sips,
        total_aum=total_aum,
        upcoming_renewals_30d=upcoming_renewals_30d,
        upcoming_sips_this_month=upcoming_sips_this_month,
        pending_approvals=pending_approvals,
        recent_meetings=recent_meetings,
    )


# ==================== Client CRUD ====================


@app.get("/api/clients", response_model=List[ClientResponse])
def get_clients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db_session),
):
    """Get all clients with optional search"""
    query = db.query(Client)

    if search:
        query = query.filter(
            (Client.name.ilike(f"%{search}%"))
            | (Client.phone.ilike(f"%{search}%"))
            | (Client.email.ilike(f"%{search}%"))
        )

    # Sort alphabetically by name
    clients = query.order_by(Client.name).offset(skip).limit(limit).all()
    return clients


@app.get("/api/clients/{client_id}", response_model=ClientWithRelations)
def get_client(client_id: int, db: Session = Depends(get_db_session)):
    """Get single client with all related data"""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@app.post(
    "/api/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED
)
def create_client(client: ClientCreate, db: Session = Depends(get_db_session)):
    """Create new client"""
    # Check if phone already exists
    existing = db.query(Client).filter(Client.phone == client.phone).first()
    if existing:
        raise HTTPException(
            status_code=400, detail="Client with this phone already exists"
        )

    db_client = Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)

    # Create audit log
    assert db_client.id is not None  # After commit, id will be set
    _create_audit_log(
        db,
        "client",
        cast(int, db_client.id),
        "insert",
        None,
        client.model_dump(),
        "advisor",
    )

    return db_client


@app.put("/api/clients/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db_session)
):
    """Update client"""
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    old_values = {
        "name": db_client.name,
        "phone": db_client.phone,
        "email": db_client.email,
    }

    update_data = client_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_client, key, value)

    db.commit()
    db.refresh(db_client)

    # Create audit log
    assert db_client.id is not None
    _create_audit_log(
        db,
        "client",
        cast(int, db_client.id),
        "update",
        old_values,
        update_data,
        "advisor",
    )

    return db_client


@app.delete("/api/clients/{client_id}", response_model=SuccessResponse)
def delete_client(client_id: int, db: Session = Depends(get_db_session)):
    """Delete client (cascade deletes policies, SIPs, meetings)"""
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")

    db.delete(db_client)
    db.commit()

    return SuccessResponse(success=True, message="Client deleted successfully")


# ==================== Policy CRUD ====================


@app.get("/api/policies", response_model=List[PolicyWithClient])
def get_policies(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    db: Session = Depends(get_db_session),
):
    """Get all policies, optionally filtered by client"""
    query = db.query(Policy).join(Client)

    if client_id:
        query = query.filter(Policy.client_id == client_id)

    policies = query.offset(skip).limit(limit).all()

    # Add client information to each policy
    result = []
    for policy in policies:
        policy_dict = {
            **policy.__dict__,
            "client_name": policy.client.name,
            "client_phone": policy.client.phone,
        }
        result.append(policy_dict)

    return result


@app.post(
    "/api/policies", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED
)
def create_policy(policy: PolicyCreate, db: Session = Depends(get_db_session)):
    """Create new policy"""
    # Verify client exists
    client = db.query(Client).filter(Client.id == policy.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Check if policy number already exists
    existing = (
        db.query(Policy).filter(Policy.policy_number == policy.policy_number).first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Policy number already exists")

    db_policy = Policy(**policy.model_dump())
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)

    assert db_policy.id is not None
    _create_audit_log(
        db,
        "policy",
        cast(int, db_policy.id),
        "insert",
        None,
        policy.model_dump(),
        "advisor",
    )

    return db_policy


@app.put("/api/policies/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: int, policy_update: PolicyUpdate, db: Session = Depends(get_db_session)
):
    """Update policy"""
    db_policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not db_policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    update_data = policy_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_policy, key, value)

    db.commit()
    db.refresh(db_policy)

    return db_policy


# ==================== SIP CRUD ====================


@app.get("/api/sips", response_model=List[SIPWithClient])
def get_sips(
    skip: int = 0,
    limit: int = 100,
    client_id: Optional[int] = None,
    db: Session = Depends(get_db_session),
):
    """Get all SIPs, optionally filtered by client"""
    query = db.query(SIP).join(Client)

    if client_id:
        query = query.filter(SIP.client_id == client_id)

    sips = query.offset(skip).limit(limit).all()

    # Add client information to each SIP
    result = []
    for sip in sips:
        sip_dict = {
            **sip.__dict__,
            "client_name": sip.client.name,
            "client_phone": sip.client.phone,
        }
        result.append(sip_dict)

    return result


@app.post("/api/sips", response_model=SIPResponse, status_code=status.HTTP_201_CREATED)
def create_sip(sip: SIPCreate, db: Session = Depends(get_db_session)):
    """Create new SIP"""
    # Verify client exists
    client = db.query(Client).filter(Client.id == sip.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    db_sip = SIP(**sip.model_dump())
    db.add(db_sip)
    db.commit()
    db.refresh(db_sip)

    assert db_sip.id is not None
    _create_audit_log(
        db, "sip", cast(int, db_sip.id), "insert", None, sip.model_dump(), "advisor"
    )

    return db_sip


# ==================== Meetings ====================


@app.get("/api/meetings", response_model=List[MeetingResponse])
def get_meetings(
    skip: int = 0,
    limit: int = 50,
    client_id: Optional[int] = None,
    db: Session = Depends(get_db_session),
):
    """Get all meetings"""
    query = db.query(Meeting).order_by(Meeting.meeting_date.desc())

    if client_id:
        query = query.filter(Meeting.client_id == client_id)

    meetings = query.offset(skip).limit(limit).all()
    return meetings


@app.post(
    "/api/meetings", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED
)
def create_meeting(meeting: MeetingCreate, db: Session = Depends(get_db_session)):
    """Create new meeting"""
    db_meeting = Meeting(**meeting.model_dump())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting


# ==================== Reminders ====================


@app.get("/api/reminders", response_model=List[ReminderResponse])
def get_reminders(
    days_ahead: int = 30, dismissed: bool = False, db: Session = Depends(get_db_session)
):
    """Get upcoming reminders"""
    from agents.reminder_agent import ReminderAgent

    agent = ReminderAgent(db)
    reminders = agent.get_upcoming_reminders(days_ahead, dismissed)
    return reminders


@app.post("/api/reminders/{reminder_id}/dismiss", response_model=SuccessResponse)
def dismiss_reminder(reminder_id: int, db: Session = Depends(get_db_session)):
    """Dismiss a reminder"""
    from agents.reminder_agent import ReminderAgent

    agent = ReminderAgent(db)
    success = agent.dismiss_reminder(reminder_id)

    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")

    return SuccessResponse(success=True, message="Reminder dismissed")


# ==================== Approval Queue ====================


@app.get("/api/approvals", response_model=List[ApprovalResponse])
def get_pending_approvals(db: Session = Depends(get_db_session)):
    """Get all pending approvals"""
    from models import ApprovalStatus

    approvals = (
        db.query(ApprovalQueue)
        .filter(ApprovalQueue.status == ApprovalStatus.PENDING)
        .all()
    )
    return approvals


def _execute_approved_action(approval: ApprovalQueue, db: Session):
    """Execute an approved action based on entity type and action type"""
    from models import AuditAction, Client, Policy, SIP, PolicyStatus, SIPStatus
    from datetime import datetime

    entity_type = approval.entity_type
    action_type = approval.action_type
    data = approval.proposed_data

    logger.info(f"Executing {action_type} on {entity_type}")

    # Execute based on entity type
    if entity_type == "client":
        if action_type == AuditAction.INSERT:
            client = Client(
                name=data["name"],
                phone=data["phone"],
                email=data.get("email"),
                address=data.get("address"),
            )
            db.add(client)
            db.flush()  # Get the ID
            logger.info(f"Created client ID: {client.id}")

        elif action_type == AuditAction.UPDATE:
            client_id = data.get("id")
            if not client_id:
                raise ValueError("Client ID required for UPDATE")

            client = db.query(Client).filter(Client.id == client_id).first()
            if not client:
                raise ValueError(f"Client {client_id} not found")

            # Update fields
            if "name" in data:
                client.name = data["name"]
            if "email" in data:
                client.email = data["email"]
            if "address" in data:
                client.address = data["address"]

            logger.info(f"Updated client ID: {client.id}")

    elif entity_type == "policy":
        if action_type == AuditAction.INSERT:
            # Parse renewal_date if it's a string
            renewal_date = data["renewal_date"]
            if isinstance(renewal_date, str):
                renewal_date = datetime.fromisoformat(renewal_date).date()

            policy = Policy(
                client_id=data["client_id"],
                policy_number=data["policy_number"],
                provider=data["provider"],
                policy_type=data["policy_type"],
                premium_amount=data["premium_amount"],
                renewal_date=renewal_date,
                sum_assured=data.get("sum_assured"),
                status=PolicyStatus(data.get("status", "active")),
            )
            db.add(policy)
            db.flush()
            logger.info(f"Created policy ID: {policy.id}")

        elif action_type == AuditAction.UPDATE:
            policy_id = data.get("id")
            if not policy_id:
                raise ValueError("Policy ID required for UPDATE")

            policy = db.query(Policy).filter(Policy.id == policy_id).first()
            if not policy:
                raise ValueError(f"Policy {policy_id} not found")

            # Update fields
            if "provider" in data:
                policy.provider = data["provider"]
            if "policy_type" in data:
                policy.policy_type = data["policy_type"]
            if "premium_amount" in data:
                policy.premium_amount = data["premium_amount"]
            if "renewal_date" in data:
                renewal_date = data["renewal_date"]
                if isinstance(renewal_date, str):
                    renewal_date = datetime.fromisoformat(renewal_date).date()
                policy.renewal_date = renewal_date
            if "sum_assured" in data:
                policy.sum_assured = data["sum_assured"]
            if "status" in data:
                policy.status = PolicyStatus(data["status"])

            logger.info(f"Updated policy ID: {policy.id}")

    elif entity_type == "sip":
        if action_type == AuditAction.INSERT:
            # Parse start_date if it's a string
            start_date = data["start_date"]
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date).date()

            sip = SIP(
                client_id=data["client_id"],
                fund_name=data["fund_name"],
                folio_number=data.get("folio_number"),
                amount=data["amount"],
                sip_day=data["sip_day"],
                start_date=start_date,
                frequency=SIPFrequency(data.get("frequency", "monthly")),
                status=SIPStatus(data.get("status", "active")),
            )
            db.add(sip)
            db.flush()
            logger.info(f"Created SIP ID: {sip.id}")

        elif action_type == AuditAction.UPDATE:
            sip_id = data.get("id")
            if not sip_id:
                raise ValueError("SIP ID required for UPDATE")

            sip = db.query(SIP).filter(SIP.id == sip_id).first()
            if not sip:
                raise ValueError(f"SIP {sip_id} not found")

            # Update fields
            if "fund_name" in data:
                sip.fund_name = data["fund_name"]
            if "folio_number" in data:
                sip.folio_number = data["folio_number"]
            if "amount" in data:
                sip.amount = data["amount"]
            if "sip_day" in data:
                sip.sip_day = data["sip_day"]
            if "start_date" in data:
                start_date = data["start_date"]
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date).date()
                sip.start_date = start_date
            if "frequency" in data:
                sip.frequency = SIPFrequency(data["frequency"])
            if "status" in data:
                sip.status = SIPStatus(data["status"])

            logger.info(f"Updated SIP ID: {sip.id}")

    # Commit changes
    db.commit()


@app.post("/api/approvals/{approval_id}/review", response_model=SuccessResponse)
def review_approval(
    approval_id: int, review: ApprovalRequest, db: Session = Depends(get_db_session)
):
    """Approve or reject a pending action"""
    from models import ApprovalStatus

    approval = db.query(ApprovalQueue).filter(ApprovalQueue.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    if review.approved:
        approval.status = ApprovalStatus.APPROVED  # type: ignore[assignment]

        # Execute the approved action
        try:
            _execute_approved_action(approval, db)
        except Exception as e:
            # SECURITY: Log full error internally but return generic message to client
            logger.error(f"Failed to execute approved action {approval_id}: {str(e)}", exc_info=True)
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to execute approved action. Please contact support."
            )
    else:
        approval.status = ApprovalStatus.REJECTED  # type: ignore[assignment]

    approval.reviewed_by = "advisor"  # type: ignore[assignment]
    from datetime import timezone

    approval.reviewed_at = datetime.now(timezone.utc)  # type: ignore[assignment]
    approval.review_notes = review.review_notes  # type: ignore[assignment]

    db.commit()

    return SuccessResponse(success=True, message="Approval reviewed successfully")


# ==================== Audit Logs ====================


@app.get("/api/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db_session),
):
    """Get audit logs"""
    query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    logs = query.offset(skip).limit(limit).all()
    return logs


# ==================== Agent Endpoints ====================


@app.post("/api/agents/reminder/run", response_model=SuccessResponse)
def run_reminder_agent(db: Session = Depends(get_db_session)):
    """Manually trigger reminder agent"""
    from agents.reminder_agent import ReminderAgent

    agent = ReminderAgent(db)
    result = agent.run()

    return SuccessResponse(success=True, message="Reminder agent executed", data=result)


@app.post("/api/agents/excel/upload")
async def upload_excel_file(
    file: UploadFile = File(...), db: Session = Depends(get_db_session)
):
    """Upload Excel file for ingestion"""
    import secrets
    import re
    from pathlib import Path

    # SECURITY: Validate filename exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # SECURITY: Validate file extension (whitelist approach)
    allowed_extensions = {'.xlsx', '.xls', '.csv'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )

    # SECURITY: Validate MIME type
    allowed_mime_types = {
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'text/csv',
        'application/csv'
    }
    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {file.content_type}"
        )

    # SECURITY: Sanitize filename to prevent directory traversal
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', Path(file.filename).name)
    unique_filename = f"{secrets.token_hex(8)}_{safe_filename}"

    # SECURITY: Read file with size limit (10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read(max_size + 1)
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {max_size / 1024 / 1024}MB"
        )

    # Save uploaded file with secure permissions
    upload_dir = "uploads"
    os.makedirs(upload_dir, mode=0o750, exist_ok=True)  # Restricted permissions
    file_path = os.path.join(upload_dir, unique_filename)

    # SECURITY: Write file with restricted permissions
    with open(file_path, "wb") as f:
        f.write(content)
    os.chmod(file_path, 0o640)  # Owner read/write, group read only

    try:
        # Process with agent
        from agents.excel_ingestion_agent import ExcelIngestionAgent

        agent = ExcelIngestionAgent(db)
        result = agent.process_file(file_path)
        return result
    finally:
        # SECURITY: Clean up uploaded file after processing
        if os.path.exists(file_path):
            os.remove(file_path)


# ==================== Capital Companion (AI Insights) ====================


@app.post("/api/agents/capital-companion/query")
def query_capital_companion(
    query: dict,
    db: Session = Depends(get_db_session),
    current_user: Advisor = Depends(get_current_user)
):
    """
    Query Capital Companion for general financial insights
    SECURITY: Blocks queries requesting client PII
    """
    from agents.capital_companion_agent import get_capital_companion_agent

    question = query.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    agent = get_capital_companion_agent()
    result = agent.query(question, db)

    return result


@app.get("/api/agents/capital-companion/daily")
def get_daily_insights(
    db: Session = Depends(get_db_session),
    current_user: Advisor = Depends(get_current_user)
):
    """
    Get daily AI-powered insights for the dashboard
    Returns aggregated analytics, no client-specific PII
    """
    from agents.capital_companion_agent import get_capital_companion_agent

    agent = get_capital_companion_agent()
    insights = agent.get_daily_insights(db)

    return {"insights": insights}


# ==================== Portfolio Analysis ====================


@app.get("/api/clients/{client_id}/ai-overview")
def get_client_ai_overview(
    client_id: int,
    db: Session = Depends(get_db_session),
    current_user: Advisor = Depends(get_current_user)
):
    """
    Get AI-powered portfolio analysis for a client
    Uses rule-based analysis (no external API calls)
    """
    from agents.portfolio_agent import get_portfolio_agent

    # Verify client exists
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    agent = get_portfolio_agent()
    analysis = agent.analyze_client(client_id, db)

    if "error" in analysis:
        raise HTTPException(status_code=500, detail=analysis["error"])

    # Format response to match frontend expectations
    return {
        "overview": {
            "portfolio_score": analysis.get("portfolio_score", 0),
            "risk_level": analysis.get("risk_level", "Undefined"),
            "risk_factors": [analysis.get("risk_level", "")],
            "recommendations": analysis.get("recommendations", []),
            "strengths": [
                f"{analysis.get('active_policies_count', 0)} active policies",
                f"{analysis.get('active_sips_count', 0)} active SIPs",
                f"Total monthly SIP: ₹{analysis.get('total_monthly_sip', 0):,.0f}"
            ],
            "concerns": analysis.get("coverage_gaps", []),
            "summary": analysis.get("summary", "")
        }
    }


# ==================== AI Chat ====================


@app.post("/api/chat")
def chat_with_ai(
    request: dict,
    db: Session = Depends(get_db_session),
    current_user: Advisor = Depends(get_current_user)
):
    """
    General AI chat endpoint for financial questions
    SECURITY: Filters out PII requests
    """
    from agents.capital_companion_agent import get_capital_companion_agent

    message = request.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    agent = get_capital_companion_agent()
    result = agent.query(message, db)

    return {
        "response": result.get("answer", ""),
        "is_blocked": result.get("is_blocked", False)
    }


# ==================== Meeting Enhancements ====================


@app.get("/api/meetings/calendar")
def get_calendar_meetings(
    db: Session = Depends(get_db_session),
    current_user: Advisor = Depends(get_current_user)
):
    """
    Get all meetings in FullCalendar format
    """
    meetings = db.query(Meeting).all()

    events = []
    for meeting in meetings:
        events.append({
            "id": meeting.id,
            "title": f"Meeting with {meeting.client.name}",
            "start": meeting.meeting_date.isoformat(),
            "end": (meeting.meeting_date + timedelta(minutes=meeting.duration)).isoformat(),
            "client_id": meeting.client_id,
            "client_name": meeting.client.name,
            "location": meeting.location,
            "meeting_type": meeting.meeting_type,
            "color": "#667eea"
        })

    return {"events": events}


@app.put("/api/meetings/{meeting_id}")
def update_meeting(
    meeting_id: int,
    meeting_data: dict,
    db: Session = Depends(get_db_session),
    current_user: Advisor = Depends(get_current_user)
):
    """
    Update a meeting
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Update fields if provided
    if "meeting_date" in meeting_data:
        meeting.meeting_date = datetime.fromisoformat(meeting_data["meeting_date"])
    if "notes" in meeting_data:
        meeting.notes = meeting_data["notes"]
    if "duration" in meeting_data:
        meeting.duration = meeting_data["duration"]
    if "location" in meeting_data:
        meeting.location = meeting_data["location"]
    if "meeting_type" in meeting_data:
        from models import MeetingType
        meeting.meeting_type = MeetingType(meeting_data["meeting_type"])

    # Update client last_contact_date
    meeting.client.last_contact_date = meeting.meeting_date.date()

    db.commit()
    db.refresh(meeting)

    return {"success": True, "message": "Meeting updated"}


@app.delete("/api/meetings/{meeting_id}")
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db_session),
    current_user: Advisor = Depends(get_current_user)
):
    """
    Delete a meeting
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    db.delete(meeting)
    db.commit()

    return {"success": True, "message": "Meeting deleted"}


# ==================== Payment Confirmation ====================


@app.post("/api/policies/{policy_id}/confirm-payment")
def confirm_policy_payment(
    policy_id: int,
    payment_data: dict,
    db: Session = Depends(get_db_session),
    current_user: Advisor = Depends(get_current_user)
):
    """
    Confirm policy premium payment
    """
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Update payment status
    from datetime import date as date_type
    policy.payment_confirmed = True
    policy.last_payment_date = date_type.today()

    db.commit()

    # Send confirmation email if client has email
    if policy.client.email:
        from services.email_service import get_email_service
        email_service = get_email_service()
        email_service.send_payment_confirmation(
            client_name=policy.client.name,
            client_email=policy.client.email,
            payment_type="policy",
            item_name=policy.policy_number,
            amount=policy.premium_amount,
            payment_date=policy.last_payment_date
        )

    return {"success": True, "message": "Payment confirmed"}


@app.post("/api/sips/{sip_id}/confirm-payment")
def confirm_sip_payment(
    sip_id: int,
    payment_data: dict,
    db: Session = Depends(get_db_session),
    current_user: Advisor = Depends(get_current_user)
):
    """
    Confirm SIP payment
    """
    sip = db.query(SIP).filter(SIP.id == sip_id).first()
    if not sip:
        raise HTTPException(status_code=404, detail="SIP not found")

    # Update payment status
    from datetime import date as date_type
    sip.payment_confirmed = True
    sip.last_payment_date = date_type.today()

    db.commit()

    # Send confirmation email if client has email
    if sip.client.email:
        from services.email_service import get_email_service
        email_service = get_email_service()
        email_service.send_payment_confirmation(
            client_name=sip.client.name,
            client_email=sip.client.email,
            payment_type="sip",
            item_name=sip.fund_name,
            amount=sip.amount,
            payment_date=sip.last_payment_date
        )

    return {"success": True, "message": "Payment confirmed"}


# ==================== Knowledge Base Initialization ====================


@app.post("/api/admin/index-knowledge-base")
def index_knowledge_base(
    db: Session = Depends(get_db_session),
    current_user: Advisor = Depends(get_current_user)
):
    """
    Index all data into ChromaDB knowledge base
    Admin endpoint - call after bulk data import
    """
    from services.knowledge_indexer import get_knowledge_indexer

    try:
        indexer = get_knowledge_indexer()
        indexer.index_all(db)

        from services.rag_service import get_rag_service
        rag = get_rag_service()
        doc_count = rag.get_collection_count()

        return {
            "success": True,
            "message": f"Knowledge base indexed successfully. Total documents: {doc_count}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Helper Functions ====================


def _create_audit_log(
    db: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    old_values: Optional[dict],
    new_values: dict,
    initiated_by: str,
):
    """Create audit log entry"""
    from models import AuditAction

    # Convert action string to AuditAction enum (case-insensitive)
    action_enum = AuditAction[action.upper()]

    log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action_enum,
        old_values=old_values,
        new_values=new_values,
        initiated_by=initiated_by,
        approved_by=initiated_by,
    )
    db.add(log)
    db.commit()


# ==================== Startup Event ====================


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Financial Advisor Platform starting...")
    logger.info("Initializing database...")
    # init_db()  # Uncomment if you want auto-init
    logger.info("Platform ready!")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
