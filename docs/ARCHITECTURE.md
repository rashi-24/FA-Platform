# Financial Advisor Platform - System Architecture

## 1. Executive Summary

This is an **internal-only** agentic AI platform designed to automate financial advisory workflows while maintaining human oversight and audit trails.

**Core Principle**: AI suggests, human approves, system commits.

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Advisor Dashboard (Frontend)              │
│  HTML/CSS/JS + Jinja2 Templates                             │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────────────┐
│                  FastAPI Backend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   API Layer  │  │  Auth Layer  │  │   Scheduler  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼───────┐    │
│  │            Service Layer (Business Logic)           │    │
│  │  - Client Service    - Policy Service               │    │
│  │  - Meeting Service   - Ingestion Service            │    │
│  └──────┬──────────────────────────────────────────────┘    │
│         │                                                     │
│  ┌──────▼──────────────────────────────────────────────┐    │
│  │              AI Agent Orchestrator                   │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐      │    │
│  │  │ Reminder   │ │ Document   │ │ Meeting    │      │    │
│  │  │ Agent      │ │ Intel      │ │ Notes      │      │    │
│  │  └────────────┘ └────────────┘ └────────────┘      │    │
│  │  ┌────────────┐ ┌────────────┐                     │    │
│  │  │ Excel      │ │ Insight    │                     │    │
│  │  │ Ingestion  │ │ Agent      │                     │    │
│  │  └────────────┘ └────────────┘                     │    │
│  └──────┬──────────────────────────────────────────────┘    │
│         │                                                     │
│  ┌──────▼──────────────────────────────────────────────┐    │
│  │         Data Access Layer (SQLAlchemy ORM)          │    │
│  └──────┬──────────────────────────────────────────────┘    │
└─────────┼─────────────────────────────────────────────────────┘
          │
┌─────────▼─────────────────────────────────────────────────────┐
│                    PostgreSQL Database                         │
│  Tables: clients, policies, sips, meetings, audit_logs,       │
│          ingestion_jobs, approval_queue                        │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 External Services (Optional)                 │
│  - LLM API (OpenAI/Anthropic)                               │
│  - Email/SMS Gateway                                         │
└─────────────────────────────────────────────────────────────┘
```

## 3. Data Model

### Core Entities

**Client**
- id (PK)
- name
- phone
- email
- notes
- created_at
- updated_at

**Policy**
- id (PK)
- client_id (FK)
- policy_number
- provider
- policy_type
- premium_amount
- renewal_date
- status (active/lapsed/surrendered)
- created_at
- updated_at

**SIP**
- id (PK)
- client_id (FK)
- amount
- frequency (monthly/quarterly)
- sip_day (1-31)
- start_date
- end_date (nullable)
- status (active/paused/stopped)
- created_at
- updated_at

**Meeting**
- id (PK)
- client_id (FK)
- meeting_date
- notes (text)
- action_items (JSON)
- created_at
- updated_at

### AI System Entities

**IngestionJob**
- id (PK)
- filename
- file_type (excel/csv/pdf)
- upload_date
- status (pending/processing/approved/rejected)
- parsed_data (JSON)
- proposed_actions (JSON)
- agent_reasoning (text)
- approved_by
- approved_at
- created_at

**ApprovalQueue**
- id (PK)
- job_type (ingestion/document/meeting_action)
- job_id (FK to relevant table)
- proposed_action (JSON)
- agent_reasoning (text)
- status (pending/approved/rejected)
- reviewed_by
- reviewed_at
- created_at

**AuditLog**
- id (PK)
- entity_type (client/policy/sip)
- entity_id
- action (insert/update/delete)
- old_values (JSON)
- new_values (JSON)
- initiated_by (human/agent_name)
- approved_by
- timestamp

## 4. Agent Architecture

### Design Principles

1. **Bounded Scope**: Each agent has exactly one responsibility
2. **Approval Gates**: No autonomous DB writes
3. **Audit Trail**: Every action is logged
4. **Deterministic Core**: Use AI only where needed
5. **Structured Output**: All AI outputs are validated JSON

### Agent Communication Protocol

```python
class AgentInput:
    task_type: str
    payload: dict
    context: dict

class AgentOutput:
    success: bool
    proposed_actions: List[dict]
    reasoning: str
    confidence_score: float
    requires_approval: bool
```

### Agent 1: Renewal & SIP Reminder Agent

**Trigger**: Daily at 9:00 AM (APScheduler)

**Logic**:
```
1. Query policies WHERE renewal_date IN [today + 30d, today + 15d, today + 7d, today + 3d]
2. Query SIPs WHERE sip_day = today's day
3. Calculate urgency level
4. Generate reminder message (template-based or AI-enhanced)
5. Insert into reminder queue
6. Send notification (email/dashboard)
```

**No approval needed** - read-only + notification generation

### Agent 2: Document Intelligence Agent

**Trigger**: Manual upload of policy document

**Flow**:
```
1. Receive PDF/image upload
2. Extract text (OCR if needed)
3. LLM extracts structured data:
   - Client name
   - Policy number
   - Premium
   - Renewal date
   - Provider
4. Validate extracted data (regex, date parsing)
5. Check for duplicate policy_number
6. Create approval queue entry
7. Present to advisor for review
8. On approval: Insert + Audit log
```

**Requires approval** - proposes INSERT

### Agent 3: Meeting Notes → Action Agent

**Trigger**: Advisor submits meeting notes

**Flow**:
```
1. Receive free-text notes
2. LLM analyzes for:
   - Action items
   - New SIP commitments
   - Policy changes
   - Follow-up dates
3. Extract structured actions
4. Create approval queue entries
5. Advisor reviews each action
6. On approval: Create SIP/update policy/schedule follow-up
```

**Requires approval** - proposes INSERT/UPDATE

### Agent 4: Excel Ingestion Agent

**Trigger**: Advisor uploads Excel/CSV

**Flow**:
```
1. Parse file with pandas
2. Detect columns (deterministic + AI-assisted)
3. For each row:
   a. Map to Client/Policy/SIP schema
   b. Check for duplicates (by name/phone/policy_number)
   c. Validate data types
   d. Propose action: INSERT / UPDATE / SKIP
4. Show preview table with proposed actions
5. Advisor approves batch or individual rows
6. Transactional commit
7. Log all changes
```

**Requires approval** - proposes bulk INSERT/UPDATE

### Agent 5: Advisor Insight Agent

**Trigger**: Advisor asks question via dashboard

**Examples**:
- "Show clients with no activity in 6 months"
- "Top 10 policies by premium"
- "Which SIPs are stopping this quarter?"

**Flow**:
```
1. Receive natural language query
2. LLM converts to SQL (with safety constraints)
3. Execute read-only query
4. Format results
5. Return to dashboard
```

**No approval needed** - read-only analytics

## 5. Safety Mechanisms

### Database Safety

```python
# 1. No raw SQL from AI
# Use ORM with parametrized queries only

# 2. Transaction rollback on error
with db.begin():
    try:
        # operations
        db.commit()
    except:
        db.rollback()

# 3. Audit logging
def log_change(entity_type, entity_id, action, old, new, initiated_by):
    AuditLog.create(...)
```

### AI Safety

```python
# 1. Schema validation
from pydantic import BaseModel, validator

class PolicyExtraction(BaseModel):
    client_name: str
    policy_number: str
    premium: float
    renewal_date: date
    
    @validator('premium')
    def validate_premium(cls, v):
        if v < 0 or v > 10_000_000:
            raise ValueError("Invalid premium")
        return v

# 2. Confidence thresholds
if agent_output.confidence < 0.8:
    flag_for_manual_review()

# 3. Rate limiting
@rate_limit(max_calls=100, per_hour=1)
def call_llm_api():
    ...
```

## 6. Deployment Architecture

### Development
```
- SQLite (local)
- FastAPI dev server
- No scheduler (manual triggers)
```

### Production
```
- PostgreSQL (managed service or self-hosted)
- Gunicorn + Nginx
- APScheduler (in-process or separate worker)
- LLM API with retry logic
```

## 7. Security Considerations

1. **Authentication**: Simple password auth (advisor-only)
2. **No public exposure**: Internal network only
3. **Data encryption**: SSL/TLS for API
4. **Backup strategy**: Daily automated backups
5. **API key management**: Environment variables

## 8. Tech Stack Justification

| Technology | Reasoning |
|-----------|-----------|
| FastAPI | Modern, async, auto-documentation, AI-friendly |
| PostgreSQL | ACID compliance, financial data integrity |
| SQLAlchemy | Type-safe ORM, prevents SQL injection |
| APScheduler | Simple in-process scheduling |
| Vanilla JS | Low complexity, no build tools needed |
| Pydantic | Runtime validation, structured AI outputs |

## 9. Development Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Database schema + migrations
- [ ] CRUD APIs for all entities
- [ ] Basic dashboard (list/create/edit)
- [ ] Authentication

### Phase 2: Automation MVP (Week 3)
- [ ] APScheduler integration
- [ ] Reminder Agent (deterministic version)
- [ ] Email notification system
- [ ] Upcoming renewals dashboard

### Phase 3: AI Integration (Week 4-5)
- [ ] LLM API integration
- [ ] Document Intelligence Agent
- [ ] Excel Ingestion Agent
- [ ] Approval queue UI

### Phase 4: Advanced Agents (Week 6+)
- [ ] Meeting Notes Agent
- [ ] Advisor Insight Agent
- [ ] Analytics dashboard
- [ ] Export/reporting

## 10. Resume Talking Points

- Built production-grade agentic AI system with human-in-the-loop approval workflows
- Implemented 5 specialized AI agents with bounded scope and audit trails
- Designed and deployed full-stack platform (FastAPI, PostgreSQL, vanilla JS)
- Applied enterprise AI safety patterns: schema validation, transaction management, approval gates
- Created real-world automation reducing manual workload by ~70%
- Demonstrated modern backend architecture with async APIs, ORM, and scheduled tasks

## 11. Future Enhancements (Out of Scope for MVP)

- Multi-advisor support
- Client portal (view-only)
- Mobile app
- Advanced analytics (ML-based churn prediction)
- Integration with fund platforms APIs
- WhatsApp bot for reminders
