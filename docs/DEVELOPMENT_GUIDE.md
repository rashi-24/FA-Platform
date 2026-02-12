# Development Guide

## Project Structure Philosophy

This platform follows a **layered architecture** with clear separation of concerns:

```
Presentation Layer (Frontend) → API Layer (FastAPI) → Service Layer (Agents) → Data Layer (SQLAlchemy/PostgreSQL)
```

## Key Design Patterns

### 1. Repository Pattern
All database access goes through SQLAlchemy ORM - no raw SQL.

### 2. Service Layer Pattern
Business logic lives in agent classes, not in API routes.

### 3. DTO Pattern
Pydantic schemas validate all input/output data.

### 4. Approval Queue Pattern
AI never directly mutates database - always goes through approval queue.

## Agent Development Guidelines

### Creating a New Agent

```python
# agents/my_new_agent.py

from sqlalchemy.orm import Session
from typing import Dict, List

class MyAgent:
    """
    Clear docstring describing:
    - Purpose
    - Inputs
    - Outputs
    - Approval requirements
    """
    
    def __init__(self, db: Session, config: Dict = None):
        self.db = db
        self.config = config or {}
    
    def run(self, input_data: Dict) -> Dict:
        """Main execution method"""
        
        # 1. Validate input
        validated = self._validate_input(input_data)
        
        # 2. Process with deterministic logic
        processed = self._deterministic_processing(validated)
        
        # 3. (Optional) Enhance with AI
        if self.config.get('use_ai'):
            enhanced = self._ai_enhancement(processed)
        
        # 4. Generate proposed actions
        proposed_actions = self._generate_proposals(enhanced)
        
        # 5. Return for approval
        return {
            "success": True,
            "proposed_actions": proposed_actions,
            "requires_approval": True,
            "reasoning": "..."
        }
    
    def _validate_input(self, data: Dict) -> Dict:
        """Validate and clean input"""
        pass
    
    def _deterministic_processing(self, data: Dict) -> Dict:
        """Core logic without AI"""
        pass
    
    def _ai_enhancement(self, data: Dict) -> Dict:
        """Optional AI-based enhancement"""
        pass
    
    def _generate_proposals(self, data: Dict) -> List[Dict]:
        """Generate approval queue entries"""
        pass
```

### Agent Safety Checklist

- [ ] Input validation with Pydantic
- [ ] No direct database writes
- [ ] All actions go to approval queue
- [ ] Confidence scores for AI outputs
- [ ] Comprehensive error handling
- [ ] Audit logging
- [ ] Idempotency (can run multiple times safely)

## API Development Guidelines

### Creating a New Endpoint

```python
@app.post("/api/my-endpoint", response_model=MyResponse)
def my_endpoint(
    request: MyRequest,
    db: Session = Depends(get_db_session)
):
    """
    Endpoint description for auto-generated docs
    """
    
    try:
        # 1. Validate request (Pydantic does this automatically)
        
        # 2. Call service layer (agent)
        agent = MyAgent(db)
        result = agent.run(request.dict())
        
        # 3. Return response
        return MyResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log error
        print(f"Error in my_endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### API Best Practices

1. **Always use Pydantic schemas** for request/response
2. **Use proper HTTP status codes**
   - 200: Success
   - 201: Created
   - 400: Bad request (validation error)
   - 404: Not found
   - 500: Server error
3. **Include pagination** for list endpoints
4. **Use dependency injection** for database sessions
5. **Add comprehensive docstrings** (shows in `/docs`)

## Database Guidelines

### Creating a New Model

```python
class MyEntity(Base):
    __tablename__ = "my_entities"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Business fields
    name = Column(String(255), nullable=False, index=True)
    
    # Relationships
    related_id = Column(Integer, ForeignKey("related_table.id"), nullable=False)
    related = relationship("RelatedModel", back_populates="my_entities")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('some_field > 0', name='check_positive'),
        UniqueConstraint('field1', 'field2', name='unique_combination'),
    )
```

### Database Migrations (with Alembic)

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create a migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing Guidelines

### Unit Testing an Agent

```python
# tests/test_my_agent.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from agents.my_agent import MyAgent

@pytest.fixture
def db_session():
    # Create in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_agent_basic_functionality(db_session):
    agent = MyAgent(db_session)
    result = agent.run({"test": "data"})
    
    assert result["success"] == True
    assert len(result["proposed_actions"]) > 0

def test_agent_validation(db_session):
    agent = MyAgent(db_session)
    
    with pytest.raises(ValueError):
        agent.run({"invalid": "input"})
```

### Integration Testing

```python
# tests/test_api.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_clients():
    response = client.get("/api/clients")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_client():
    response = client.post("/api/clients", json={
        "name": "Test Client",
        "phone": "+919876543210",
        "email": "test@example.com"
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Test Client"
```

## Performance Guidelines

### Database Query Optimization

```python
# ❌ Bad: N+1 queries
clients = db.query(Client).all()
for client in clients:
    policies = client.policies  # Separate query for each client

# ✅ Good: Eager loading
from sqlalchemy.orm import joinedload

clients = db.query(Client).options(
    joinedload(Client.policies)
).all()
```

### Pagination

```python
@app.get("/api/clients")
def get_clients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    clients = db.query(Client).offset(skip).limit(limit).all()
    return clients
```

### Caching (Future Enhancement)

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_dashboard_stats(date: str):
    # Expensive computation
    pass
```

## Security Guidelines

### 1. Never Trust User Input

```python
# Always use Pydantic validation
from pydantic import BaseModel, validator

class ClientCreate(BaseModel):
    phone: str
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v.startswith('+91'):
            raise ValueError('Must be Indian phone number')
        return v
```

### 2. Use Parameterized Queries

```python
# ✅ Good: ORM handles parameterization
db.query(Client).filter(Client.phone == user_input).first()

# ❌ Bad: Never do this
db.execute(f"SELECT * FROM clients WHERE phone = '{user_input}'")
```

### 3. Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash(plain_password)

# Verify password
is_valid = pwd_context.verify(plain_password, hashed)
```

## Debugging Tips

### Enable SQL Logging

```python
# In database.py
engine = create_engine(DATABASE_URL, echo=True)  # Prints all SQL queries
```

### API Request Logging

```python
# In main.py
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"{request.method} {request.url}")
    response = await call_next(request)
    print(f"Response: {response.status_code}")
    return response
```

### Interactive Debugging

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use modern breakpoint()
breakpoint()
```

## Deployment Checklist

### Production Readiness

- [ ] Change default passwords
- [ ] Set `DEBUG=False`
- [ ] Use environment variables for secrets
- [ ] Set up PostgreSQL (not SQLite)
- [ ] Configure CORS properly
- [ ] Enable HTTPS
- [ ] Set up logging to file
- [ ] Configure automatic backups
- [ ] Add rate limiting
- [ ] Set up monitoring (e.g., Sentry)
- [ ] Document API with examples
- [ ] Write user manual

### Deployment Options

**Option 1: Traditional Server**
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Nginx reverse proxy
# Configure nginx to proxy to localhost:8000
```

**Option 2: Docker**
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Option 3: Cloud Platform**
- Heroku
- AWS Elastic Beanstalk
- Google Cloud Run
- Azure App Service

## Common Issues & Solutions

### Issue: Database connection errors
**Solution**: Check DATABASE_URL, ensure PostgreSQL is running

### Issue: Import errors
**Solution**: Ensure virtual environment is activated, reinstall requirements

### Issue: CORS errors in frontend
**Solution**: Update CORS middleware in main.py

### Issue: Agent not working
**Solution**: Check agent logs, verify database permissions, test with minimal input

## Resources

- FastAPI Docs: https://fastapi.tiangolo.com
- SQLAlchemy Docs: https://docs.sqlalchemy.org
- Pydantic Docs: https://docs.pydantic.dev
- PostgreSQL Docs: https://www.postgresql.org/docs/

## Getting Help

1. Check existing issues in project
2. Review logs in `logs/app.log`
3. Test with minimal example
4. Document steps to reproduce
5. Reach out to project maintainer
