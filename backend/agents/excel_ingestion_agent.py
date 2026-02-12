"""
Excel Ingestion Agent - Enhanced Multi-Entity Support
Processes uploaded Excel files containing clients, policies, and SIPs
Supports duplicate detection and UPDATE vs INSERT logic
"""

from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import os
import re
from datetime import datetime, date

from models import (
    IngestionJob,
    JobStatus,
    ApprovalQueue,
    ApprovalStatus,
    AuditAction,
    Client,
    Policy,
    SIP,
    PolicyStatus,
    SIPStatus,
    SIPFrequency,
)


class ExcelIngestionAgent:
    """Agent that processes Excel files and proposes data ingestion actions"""

    def __init__(self, db: Session):
        self.db = db

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process an uploaded Excel file"""

        if not os.path.exists(file_path):
            return {"success": False, "error": "File not found"}

        # Create ingestion job
        filename = os.path.basename(file_path)
        job = IngestionJob(
            filename=filename,
            file_type="excel",
            file_path=file_path,
            status=JobStatus.PROCESSING,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        try:
            # Read Excel file
            df = pd.read_excel(file_path)

            # Normalize column names (remove spaces, lowercase)
            df.columns = [self._normalize_column_name(col) for col in df.columns]

            # Convert to JSON for storage
            parsed_data = df.to_dict("records")
            job.parsed_data = parsed_data  # type: ignore

            # Analyze and propose actions
            proposed_actions = self._analyze_and_propose(df)
            job.proposed_actions = proposed_actions  # type: ignore

            # Create approval queue entries
            for action in proposed_actions:
                approval = ApprovalQueue(
                    job_type="ingestion",
                    job_id=job.id,
                    entity_type=action.get("entity", "client"),
                    action_type=AuditAction(action.get("action", "INSERT").upper()),
                    proposed_data=action.get("data", {}),
                    agent_reasoning=action.get("reasoning", ""),
                    confidence_score=action.get("confidence", 0.8),
                    status=ApprovalStatus.PENDING,
                )
                self.db.add(approval)

            job.status = JobStatus.APPROVED  # type: ignore
            job.agent_reasoning = (  # type: ignore
                f"Successfully parsed {len(parsed_data)} rows. "
                f"Detected {len([a for a in proposed_actions if a['entity'] == 'client'])} clients, "
                f"{len([a for a in proposed_actions if a['entity'] == 'policy'])} policies, "
                f"{len([a for a in proposed_actions if a['entity'] == 'sip'])} SIPs."
            )

            self.db.commit()

            return {
                "success": True,
                "job_id": job.id,
                "rows_parsed": len(parsed_data),
                "actions_proposed": len(proposed_actions),
                "message": "File processed successfully. Awaiting approval.",
            }

        except Exception as e:
            job.status = JobStatus.FAILED  # type: ignore
            job.error_message = str(e)  # type: ignore
            self.db.commit()

            return {"success": False, "error": str(e), "job_id": job.id}

    def _normalize_column_name(self, col: str) -> str:
        """Normalize column names for easier matching"""
        return col.lower().strip().replace(" ", "_").replace("-", "_")

    def _analyze_and_propose(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Analyze Excel data and propose database actions for all entity types"""
        actions = []

        # Detect entity type based on columns
        entity_type = self._detect_entity_type(df.columns.tolist())

        print(f"📊 Detected entity type: {entity_type}")

        for idx, row in df.iterrows():
            row_actions = []

            # Process based on detected entity type
            if entity_type == "client" or entity_type == "mixed":
                client_action = self._process_client_row(row, idx)
                if client_action:
                    row_actions.append(client_action)

            if entity_type == "policy" or entity_type == "mixed":
                policy_action = self._process_policy_row(row, idx)
                if policy_action:
                    row_actions.append(policy_action)

            if entity_type == "sip" or entity_type == "mixed":
                sip_action = self._process_sip_row(row, idx)
                if sip_action:
                    row_actions.append(sip_action)

            actions.extend(row_actions)

        return actions

    def _detect_entity_type(self, columns: List[str]) -> str:
        """Detect entity type based on column names"""
        columns_str = " ".join(columns)

        has_client = any(
            col in columns_str
            for col in ["name", "phone", "email", "client_name", "mobile"]
        )
        has_policy = any(
            col in columns_str
            for col in ["policy_number", "policy_type", "premium", "provider", "renewal"]
        )
        has_sip = any(
            col in columns_str
            for col in ["fund_name", "folio", "sip_amount", "sip_day", "fund"]
        )

        # Determine entity type
        entity_count = sum([has_client, has_policy, has_sip])

        if entity_count > 1:
            return "mixed"
        elif has_policy:
            return "policy"
        elif has_sip:
            return "sip"
        else:
            return "client"

    def _process_client_row(
        self, row: pd.Series, idx: Any
    ) -> Optional[Dict[str, Any]]:
        """Process a row that contains client data"""

        # Extract client fields with fuzzy matching
        name = self._extract_field(
            row, ["name", "client_name", "customer_name", "full_name"]
        )
        phone = self._extract_field(
            row, ["phone", "mobile", "contact", "phone_number", "mobile_number"]
        )
        email = self._extract_field(row, ["email", "email_id", "email_address"])
        address = self._extract_field(row, ["address", "location", "city"])

        # Validate required fields
        if not name or not phone:
            return None

        # Clean phone number
        phone = self._clean_phone(phone)
        if not phone:
            return None

        # Check for existing client by phone
        existing = self.db.query(Client).filter(Client.phone == phone).first()

        if existing:
            # Propose UPDATE
            return {
                "row": int(idx) + 2,  # Excel row (1-indexed + header)
                "action": "UPDATE",
                "entity": "client",
                "entity_id": existing.id,
                "data": {
                    "id": existing.id,
                    "name": str(name),
                    "phone": phone,
                    "email": str(email) if pd.notna(email) else existing.email,
                    "address": str(address) if pd.notna(address) else existing.address,
                },
                "reasoning": f"Client with phone {phone} already exists (ID: {existing.id}). Updating details.",
                "confidence": 0.95,
            }
        else:
            # Propose INSERT
            return {
                "row": int(idx) + 2,
                "action": "INSERT",
                "entity": "client",
                "data": {
                    "name": str(name),
                    "phone": phone,
                    "email": str(email) if pd.notna(email) else None,
                    "address": str(address) if pd.notna(address) else None,
                },
                "reasoning": f"New client detected. Proposing insert.",
                "confidence": 0.9,
            }

    def _process_policy_row(
        self, row: pd.Series, idx: Any
    ) -> Optional[Dict[str, Any]]:
        """Process a row that contains policy data"""

        # Extract policy fields
        policy_number = self._extract_field(
            row, ["policy_number", "policy_no", "policy_id", "policyno"]
        )
        provider = self._extract_field(
            row, ["provider", "insurance_company", "insurer", "company"]
        )
        policy_type = self._extract_field(
            row, ["policy_type", "type", "plan_type", "plan"]
        )
        premium_amount = self._extract_field(
            row, ["premium_amount", "premium", "amount", "premium_amt"]
        )
        renewal_date = self._extract_field(
            row, ["renewal_date", "renewal", "due_date", "next_renewal"]
        )
        sum_assured = self._extract_field(
            row, ["sum_assured", "coverage", "cover_amount", "sum_insured"]
        )

        # Get client identifier (phone or name)
        client_phone = self._extract_field(
            row, ["phone", "mobile", "client_phone", "contact"]
        )
        client_name = self._extract_field(
            row, ["name", "client_name", "customer_name"]
        )

        # Validate required fields
        if not policy_number or not provider or not premium_amount or not renewal_date:
            return None

        # Find or identify client
        client_id: Optional[int] = None
        if client_phone:
            phone = self._clean_phone(client_phone)
            client = self.db.query(Client).filter(Client.phone == phone).first()
            if client:
                client_id = int(client.id)  # type: ignore

        if client_id is None and client_name:
            # Try to find by name
            client = (
                self.db.query(Client).filter(Client.name.ilike(f"%{client_name}%")).first()
            )
            if client:
                client_id = int(client.id)  # type: ignore

        if client_id is None:
            return {
                "row": int(idx) + 2,
                "action": "SKIP",
                "entity": "policy",
                "data": {},
                "reasoning": f"Cannot find client for policy {policy_number}. Client phone/name required.",
                "confidence": 0.0,
            }

        # Parse renewal date
        renewal_date_obj = self._parse_date(renewal_date)
        if not renewal_date_obj:
            return None

        # Check for existing policy by policy_number
        existing = (
            self.db.query(Policy).filter(Policy.policy_number == str(policy_number)).first()
        )

        policy_data = {
            "client_id": client_id,
            "policy_number": str(policy_number),
            "provider": str(provider),
            "policy_type": str(policy_type) if pd.notna(policy_type) else "General",
            "premium_amount": float(premium_amount),
            "renewal_date": renewal_date_obj.isoformat(),
            "sum_assured": float(sum_assured) if pd.notna(sum_assured) else None,
            "status": "active",
        }

        if existing:
            # Propose UPDATE
            policy_data["id"] = existing.id
            return {
                "row": int(idx) + 2,
                "action": "UPDATE",
                "entity": "policy",
                "entity_id": existing.id,
                "data": policy_data,
                "reasoning": f"Policy {policy_number} already exists (ID: {existing.id}). Updating details.",
                "confidence": 0.95,
            }
        else:
            # Propose INSERT
            return {
                "row": int(idx) + 2,
                "action": "INSERT",
                "entity": "policy",
                "data": policy_data,
                "reasoning": f"New policy detected for client ID {client_id}.",
                "confidence": 0.9,
            }

    def _process_sip_row(self, row: pd.Series, idx: Any) -> Optional[Dict[str, Any]]:
        """Process a row that contains SIP data"""

        # Extract SIP fields
        fund_name = self._extract_field(
            row, ["fund_name", "fund", "scheme_name", "scheme"]
        )
        folio_number = self._extract_field(
            row, ["folio_number", "folio", "folio_no", "foliono"]
        )
        amount = self._extract_field(
            row, ["amount", "sip_amount", "monthly_amount", "investment"]
        )
        sip_day = self._extract_field(
            row, ["sip_day", "day", "payment_day", "deduction_day"]
        )
        start_date = self._extract_field(
            row, ["start_date", "start", "commenced_date", "inception_date"]
        )

        # Get client identifier
        client_phone = self._extract_field(
            row, ["phone", "mobile", "client_phone", "contact"]
        )
        client_name = self._extract_field(
            row, ["name", "client_name", "customer_name"]
        )

        # Validate required fields
        if not fund_name or not amount or not sip_day or not start_date:
            return None

        # Find client
        client_id: Optional[int] = None
        if client_phone:
            phone = self._clean_phone(client_phone)
            client = self.db.query(Client).filter(Client.phone == phone).first()
            if client:
                client_id = int(client.id)  # type: ignore

        if client_id is None and client_name:
            client = (
                self.db.query(Client).filter(Client.name.ilike(f"%{client_name}%")).first()
            )
            if client:
                client_id = int(client.id)  # type: ignore

        if client_id is None:
            return {
                "row": int(idx) + 2,
                "action": "SKIP",
                "entity": "sip",
                "data": {},
                "reasoning": f"Cannot find client for SIP {fund_name}. Client phone/name required.",
                "confidence": 0.0,
            }

        # Parse start date
        start_date_obj = self._parse_date(start_date)
        if not start_date_obj:
            return None

        # Validate SIP day (1-31)
        try:
            sip_day_int = int(sip_day)
            if sip_day_int < 1 or sip_day_int > 31:
                return None
        except:
            return None

        # Check for existing SIP by folio_number or combination
        existing = None
        if folio_number and pd.notna(folio_number):
            existing = (
                self.db.query(SIP).filter(SIP.folio_number == str(folio_number)).first()
            )

        if not existing:
            # Check by client + fund name combination
            existing = (
                self.db.query(SIP)
                .filter(SIP.client_id == client_id, SIP.fund_name == str(fund_name))
                .first()
            )

        sip_data = {
            "client_id": client_id,
            "fund_name": str(fund_name),
            "folio_number": str(folio_number) if pd.notna(folio_number) else None,
            "amount": float(amount),
            "sip_day": sip_day_int,
            "start_date": start_date_obj.isoformat(),
            "frequency": "monthly",
            "status": "active",
        }

        if existing:
            # Propose UPDATE
            sip_data["id"] = existing.id
            return {
                "row": int(idx) + 2,
                "action": "UPDATE",
                "entity": "sip",
                "entity_id": existing.id,
                "data": sip_data,
                "reasoning": f"SIP for {fund_name} already exists (ID: {existing.id}). Updating details.",
                "confidence": 0.95,
            }
        else:
            # Propose INSERT
            return {
                "row": int(idx) + 2,
                "action": "INSERT",
                "entity": "sip",
                "data": sip_data,
                "reasoning": f"New SIP detected for client ID {client_id}.",
                "confidence": 0.9,
            }

    def _extract_field(self, row: pd.Series, possible_names: List[str]) -> Any:
        """Extract field value from row using fuzzy column matching"""
        for name in possible_names:
            if name in row.index and pd.notna(row[name]):
                return row[name]
        return None

    def _clean_phone(self, phone: Any) -> Optional[str]:
        """Clean and validate phone number"""
        if pd.isna(phone):
            return None

        # Convert to string and remove non-digits
        phone_str = str(phone).strip()
        phone_digits = re.sub(r"[^\d]", "", phone_str)

        # Validate length (Indian phone: 10 digits)
        if len(phone_digits) == 10:
            return phone_digits
        elif len(phone_digits) > 10:
            # Take last 10 digits
            return phone_digits[-10:]

        return None

    def _parse_date(self, date_value: Any) -> Optional[date]:
        """Parse date from various formats"""
        if pd.isna(date_value):
            return None

        # If already a datetime
        if isinstance(date_value, (datetime, pd.Timestamp)):
            return date_value.date()

        # If already a date
        if isinstance(date_value, date):
            return date_value

        # Try parsing string
        date_str = str(date_value).strip()

        # Common date formats
        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d.%m.%Y",
            "%Y.%m.%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue

        return None


# Singleton
_excel_agent = None


def get_excel_agent(db: Session) -> ExcelIngestionAgent:
    """Get or create Excel ingestion agent"""
    return ExcelIngestionAgent(db)
