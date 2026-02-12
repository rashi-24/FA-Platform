"""
Agent 4: Excel Ingestion Agent

Safely ingests bulk client/policy/SIP data from Excel/CSV files.
Uses deterministic parsing + AI-assisted column mapping and duplicate detection.

Flow:
1. Parse Excel file with pandas
2. AI maps columns to schema
3. AI proposes INSERT/UPDATE/SKIP for each row
4. Advisor reviews and approves
5. Transactional DB commit + audit log
"""

import pandas as pd
import json
from typing import List, Dict, Optional, Tuple, Iterable
from datetime import datetime, date
from sqlalchemy.orm import Session

from models import Client, Policy, SIP, IngestionJob, ApprovalQueue, AuditLog
from models import JobStatus, ApprovalStatus, AuditAction


class ExcelIngestionAgent:
    """
    Ingests and proposes actions for bulk data from Excel files
    Requires human approval before any DB writes
    """
    
    def __init__(self, db: Session, use_ai: bool = True):
        self.db = db
        self.use_ai = use_ai
        
    def process_file(
        self, 
        file_path: str, 
        sheet_name: Optional[str] = None
    ) -> Dict:
        """
        Main processing method
        Returns ingestion job with proposed actions
        """
        print(f"[ExcelAgent] Processing file: {file_path}")
        
        # Create ingestion job
        job = IngestionJob(
            filename=file_path.split('/')[-1],
            file_type=self._detect_file_type(file_path),
            file_path=file_path,
            status=JobStatus.PROCESSING
        )
        self.db.add(job)
        self.db.commit()
        
        try:
            # Parse file
            df = self._read_file(file_path, sheet_name)
            
            # Detect entity type and map columns
            entity_type, column_mapping = self._detect_entity_and_columns(df)
            
            # Process each row
            proposed_actions = []
            for idx, row in df.iterrows():
                action = self._process_row(
                    row_number=idx + 1,  # type: ignore[operator]
                    row_data=row.to_dict(),
                    entity_type=entity_type,
                    column_mapping=column_mapping
                )
                proposed_actions.append(action)
            
            # Update job with results
            job.parsed_data = df.to_dict(orient='records')  # type: ignore[assignment]
            job.proposed_actions = proposed_actions  # type: ignore[assignment]
            job.agent_reasoning = self._generate_overall_reasoning(  # type: ignore[assignment]
                entity_type,
                len(df),
                proposed_actions
            )
            job.status = JobStatus.PENDING  # type: ignore[assignment]
            self.db.commit()
            
            # Create approval queue entries
            self._create_approval_queue_entries(job.id, proposed_actions)  # type: ignore[arg-type]
            
            print(f"[ExcelAgent] Processed {len(df)} rows, {len(proposed_actions)} actions proposed")
            
            return {
                "success": True,
                "job_id": job.id,
                "total_rows": len(df),
                "proposed_actions": proposed_actions,
                "entity_type": entity_type
            }
            
        except Exception as e:
            job.status = JobStatus.FAILED  # type: ignore[assignment]
            job.error_message = str(e)  # type: ignore[assignment]
            self.db.commit()
            print(f"[ExcelAgent] Error: {e}")
            raise e
    
    def _read_file(self, file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Read Excel or CSV file
        """
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path, sheet_name=sheet_name or 0)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        # Clean column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        return df
    
    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from extension"""
        if file_path.endswith('.csv'):
            return 'csv'
        elif file_path.endswith(('.xls', '.xlsx')):
            return 'excel'
        return 'unknown'
    
    def _detect_entity_and_columns(self, df: pd.DataFrame) -> Tuple[str, Dict[str, str]]:
        """
        Detect whether this is client, policy, or SIP data
        Map columns to our schema
        
        In real implementation, this would use LLM.
        Here we use heuristic matching.
        """
        columns = set(df.columns)
        
        # Heuristic detection
        if 'policy_number' in columns or 'policy_no' in columns:
            entity_type = 'policy'
            column_mapping = self._map_policy_columns(df.columns)
        elif 'fund_name' in columns or 'sip_amount' in columns:
            entity_type = 'sip'
            column_mapping = self._map_sip_columns(df.columns)
        else:
            # Default to client
            entity_type = 'client'
            column_mapping = self._map_client_columns(df.columns)
        
        print(f"[ExcelAgent] Detected entity type: {entity_type}")
        print(f"[ExcelAgent] Column mapping: {column_mapping}")
        
        return entity_type, column_mapping
    
    def _map_client_columns(self, columns: Iterable[str]) -> Dict[str, str]:
        """Map Excel columns to Client schema"""
        mapping = {}
        
        # Fuzzy column matching
        for col in columns:
            col_lower = col.lower()
            if 'name' in col_lower and 'client' not in col_lower:
                mapping['name'] = col
            elif 'phone' in col_lower or 'mobile' in col_lower or 'contact' in col_lower:
                mapping['phone'] = col
            elif 'email' in col_lower:
                mapping['email'] = col
            elif 'address' in col_lower:
                mapping['address'] = col
            elif 'note' in col_lower:
                mapping['notes'] = col
        
        return mapping
    
    def _map_policy_columns(self, columns: Iterable[str]) -> Dict[str, str]:
        """Map Excel columns to Policy schema"""
        mapping = {}
        
        for col in columns:
            col_lower = col.lower()
            if 'client' in col_lower and 'name' in col_lower:
                mapping['client_name'] = col
            elif 'policy' in col_lower and ('number' in col_lower or 'no' in col_lower):
                mapping['policy_number'] = col
            elif 'provider' in col_lower or 'company' in col_lower:
                mapping['provider'] = col
            elif 'type' in col_lower:
                mapping['policy_type'] = col
            elif 'premium' in col_lower:
                mapping['premium_amount'] = col
            elif 'renewal' in col_lower:
                mapping['renewal_date'] = col
            elif 'sum' in col_lower and 'assured' in col_lower:
                mapping['sum_assured'] = col
        
        return mapping
    
    def _map_sip_columns(self, columns: Iterable[str]) -> Dict[str, str]:
        """Map Excel columns to SIP schema"""
        mapping = {}
        
        for col in columns:
            col_lower = col.lower()
            if 'client' in col_lower and 'name' in col_lower:
                mapping['client_name'] = col
            elif 'fund' in col_lower:
                mapping['fund_name'] = col
            elif 'folio' in col_lower:
                mapping['folio_number'] = col
            elif 'amount' in col_lower:
                mapping['amount'] = col
            elif 'sip' in col_lower and 'day' in col_lower:
                mapping['sip_day'] = col
            elif 'start' in col_lower and 'date' in col_lower:
                mapping['start_date'] = col
        
        return mapping
    
    def _process_row(
        self,
        row_number: int,
        row_data: Dict,
        entity_type: str,
        column_mapping: Dict[str, str]
    ) -> Dict:
        """
        Process a single row and propose action
        """
        # Extract mapped data
        extracted_data = {}
        for schema_field, excel_column in column_mapping.items():
            if excel_column in row_data:
                value = row_data[excel_column]
                # Clean value
                if pd.isna(value):
                    value = None
                else:
                    # Convert phone numbers to strings (Excel often reads them as integers)
                    if schema_field == 'phone' and value is not None:
                        value = str(int(value)) if isinstance(value, (int, float)) else str(value)
                extracted_data[schema_field] = value
        
        # Check for duplicates and determine action
        action, reasoning, confidence = self._determine_action(
            entity_type,
            extracted_data
        )
        
        return {
            "row_number": row_number,
            "action": action,  # INSERT, UPDATE, SKIP
            "entity_type": entity_type,
            "data": extracted_data,
            "reasoning": reasoning,
            "confidence": confidence
        }
    
    def _determine_action(
        self,
        entity_type: str,
        data: Dict
    ) -> Tuple[str, str, float]:
        """
        Determine whether to INSERT, UPDATE, or SKIP
        Check for duplicates
        """
        if entity_type == "client":
            # Check if client exists by phone
            if 'phone' in data and data['phone']:
                existing = self.db.query(Client).filter(
                    Client.phone == data['phone']
                ).first()
                
                if existing:
                    return (
                        "UPDATE",
                        f"Client with phone {data['phone']} already exists (ID: {existing.id})",
                        0.9
                    )
            
            return ("INSERT", "New client record", 0.95)
        
        elif entity_type == "policy":
            # Check if policy exists by policy_number
            if 'policy_number' in data and data['policy_number']:
                existing = self.db.query(Policy).filter(
                    Policy.policy_number == data['policy_number']
                ).first()
                
                if existing:
                    return (
                        "UPDATE",
                        f"Policy {data['policy_number']} already exists (ID: {existing.id})",
                        0.9
                    )
            
            # Need to find client first
            if 'client_name' not in data:
                return ("SKIP", "Missing client name - cannot link policy", 0.8)
            
            return ("INSERT", "New policy record", 0.85)
        
        elif entity_type == "sip":
            # Check if similar SIP exists
            if 'client_name' in data and 'fund_name' in data:
                # This would need more sophisticated duplicate detection
                return ("INSERT", "New SIP record", 0.8)
            
            return ("SKIP", "Insufficient data for SIP", 0.7)
        
        return ("SKIP", "Unknown entity type", 0.5)
    
    def _create_approval_queue_entries(
        self,
        job_id: int,
        proposed_actions: List[Dict]
    ):
        """
        Create approval queue entries for each proposed action
        """
        for action in proposed_actions:
            if action['action'] == 'SKIP':
                continue  # Don't create approval for skipped rows
            
            approval = ApprovalQueue(
                job_type='ingestion',
                job_id=job_id,
                entity_type=action['entity_type'],
                action_type=AuditAction.INSERT if action['action'] == 'INSERT' else AuditAction.UPDATE,
                proposed_data=action['data'],
                agent_reasoning=action['reasoning'],
                confidence_score=action['confidence'],
                status=ApprovalStatus.PENDING
            )
            self.db.add(approval)
        
        self.db.commit()
    
    def _generate_overall_reasoning(
        self,
        entity_type: str,
        total_rows: int,
        proposed_actions: List[Dict]
    ) -> str:
        """
        Generate summary reasoning for the entire ingestion job
        """
        inserts = sum(1 for a in proposed_actions if a['action'] == 'INSERT')
        updates = sum(1 for a in proposed_actions if a['action'] == 'UPDATE')
        skips = sum(1 for a in proposed_actions if a['action'] == 'SKIP')
        
        reasoning = (
            f"Processed {total_rows} rows of {entity_type} data.\n"
            f"Proposed actions: {inserts} inserts, {updates} updates, {skips} skips.\n"
            f"All proposed changes require advisor approval before committing to database."
        )
        
        return reasoning
    
    def approve_and_commit(
        self,
        job_id: int,
        approved_actions: List[int],  # List of approval_queue IDs
        advisor_name: str = "advisor"
    ) -> Dict:
        """
        Commit approved actions to database
        """
        job = self.db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        committed = []
        failed = []
        
        for approval_id in approved_actions:
            approval = self.db.query(ApprovalQueue).filter(
                ApprovalQueue.id == approval_id
            ).first()
            
            if not approval:
                failed.append({"id": approval_id, "reason": "Approval not found"})
                continue
            
            try:
                # Commit the action
                entity = self._commit_action(approval, advisor_name)
                committed.append({"id": approval_id, "entity_id": entity.id})
                
                # Update approval status
                approval.status = ApprovalStatus.APPROVED  # type: ignore[assignment]
                approval.reviewed_by = advisor_name  # type: ignore[assignment]
                approval.reviewed_at = datetime.utcnow()  # type: ignore[assignment]
                
            except Exception as e:
                failed.append({"id": approval_id, "reason": str(e)})
        
        # Update job status
        job.status = JobStatus.APPROVED  # type: ignore[assignment]
        job.approved_by = advisor_name  # type: ignore[assignment]
        job.approved_at = datetime.utcnow()  # type: ignore[assignment]

        self.db.commit()
        
        return {
            "success": True,
            "committed": len(committed),
            "failed": len(failed),
            "details": {"committed": committed, "failed": failed}
        }
    
    def _commit_action(self, approval: ApprovalQueue, advisor_name: str):
        """
        Actually insert/update the entity in database
        """
        data = approval.proposed_data
        
        entity = None

        if approval.entity_type == 'client':  # type: ignore[comparison-overlap]
            if approval.action_type == AuditAction.INSERT:  # type: ignore[comparison-overlap]
                entity = Client(**data)  # type: ignore[arg-type]
                self.db.add(entity)
                self.db.flush()  # Get ID

                # Log audit
                self._create_audit_log(
                    'client', entity.id, AuditAction.INSERT,  # type: ignore[arg-type]
                    None, data, advisor_name  # type: ignore[arg-type]
                )
            else:  # UPDATE
                # Find client and update
                client = self.db.query(Client).filter(Client.phone == data['phone']).first()
                if client:
                    for key, value in data.items():
                        setattr(client, key, value)
                    entity = client

                    self._create_audit_log(
                        'client', entity.id, AuditAction.UPDATE,  # type: ignore[arg-type]
                        {}, data, advisor_name  # type: ignore[arg-type]
                    )

        # Similar for policy and sip...
        # (Abbreviated for brevity)

        if entity is None:
            raise ValueError(f"Failed to commit {approval.entity_type} action")

        return entity
    
    def _create_audit_log(
        self,
        entity_type: str,
        entity_id: int,
        action: AuditAction,
        old_values: Optional[Dict],
        new_values: Dict,
        advisor_name: str
    ):
        """Create audit log entry"""
        log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            initiated_by=f"agent:excel_ingestion",
            approved_by=advisor_name,
            timestamp=datetime.utcnow()
        )
        self.db.add(log)


if __name__ == "__main__":
    # Test the agent
    from database import get_db
    
    # Example usage
    with get_db() as db:
        agent = ExcelIngestionAgent(db)
        # result = agent.process_file('/path/to/clients.xlsx')
        # print(result)
