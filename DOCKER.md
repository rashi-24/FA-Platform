# 🐳 Docker Deployment Guide - FA-Platform

This guide covers running the entire FA-Platform using Docker and Docker Compose.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Docker Commands](#docker-commands)
- [Architecture](#architecture)
- [Volumes & Data Persistence](#volumes--data-persistence)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

---

## ✅ Prerequisites

### Required Software

1. **Docker Desktop** (includes Docker Compose)
   - [Download for Mac](https://www.docker.com/products/docker-desktop/)
   - [Download for Windows](https://www.docker.com/products/docker-desktop/)
   - [Download for Linux](https://docs.docker.com/engine/install/)

2. **Git** (to clone the repository)
   ```bash
   git --version  # Should show version 2.x or higher
   ```

### Verify Installation

```bash
docker --version          # Should show Docker version 20.x or higher
docker-compose --version  # Should show version 2.x or higher
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/FA-Platform.git
cd FA-Platform
```

### 2. Configure Environment

```bash
# Copy the Docker environment template
cp .env.docker .env

# Generate a secure SECRET_KEY
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

### 3. Edit `.env` File

Open `.env` and update:

```bash
# REQUIRED: Replace with generated SECRET_KEY
SECRET_KEY=your_generated_secret_key_here

# REQUIRED: Change default database password
POSTGRES_PASSWORD=your_secure_database_password

# OPTIONAL: Change demo user password
DEMO_USER_PASSWORD=YourSecurePassword123!
```

### 4. Start the Platform

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 6. Login Credentials

```
Email:    demo@example.com
Password: Demo@Pass123!  (or what you set in DEMO_USER_PASSWORD)
```

---

## ⚙️ Configuration

### Environment Variables

All configuration is done via the `.env` file:

#### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key (generate new!) | `c4ea67bd16b276b0...` |
| `POSTGRES_PASSWORD` | Database password | `MySecurePass123!` |

#### Optional Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `financial_advisor` | Database name |
| `POSTGRES_USER` | `fa_user` | Database username |
| `POSTGRES_PORT` | `5432` | Database port |
| `BACKEND_PORT` | `8000` | Backend API port |
| `FRONTEND_PORT` | `3000` | Frontend port |
| `DEBUG` | `False` | Debug mode (use `True` for development) |
| `SEED_DEMO_DATA` | `true` | Seed demo data on first run |
| `ALLOWED_ORIGINS` | `http://localhost:3000,...` | CORS allowed origins |

### Port Configuration

To change default ports, update `.env`:

```bash
BACKEND_PORT=8080   # Change backend from 8000 to 8080
FRONTEND_PORT=3001  # Change frontend from 3000 to 3001
POSTGRES_PORT=5433  # Change database from 5432 to 5433
```

---

## 🎮 Docker Commands

### Starting & Stopping

```bash
# Start all services (detached mode)
docker-compose up -d

# Start with logs visible
docker-compose up

# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes all data)
docker-compose down -v
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f db
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Rebuilding

```bash
# Rebuild after code changes
docker-compose up -d --build

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend
```

### Service Management

```bash
# Restart a service
docker-compose restart backend

# Stop a specific service
docker-compose stop backend

# Start a specific service
docker-compose start backend

# View running containers
docker-compose ps

# View service health status
docker-compose ps
```

### Database Operations

```bash
# Access PostgreSQL shell
docker-compose exec db psql -U fa_user -d financial_advisor

# Create database backup
docker-compose exec db pg_dump -U fa_user financial_advisor > backup.sql

# Restore database backup
docker-compose exec -T db psql -U fa_user financial_advisor < backup.sql

# Reset database (⚠️ destroys all data)
docker-compose down -v
docker-compose up -d
```

### Accessing Containers

```bash
# Access backend container shell
docker-compose exec backend bash

# Access database container shell
docker-compose exec db bash

# Run Python commands in backend
docker-compose exec backend python -c "print('Hello from Docker!')"

# Run database migrations (when Alembic is added)
docker-compose exec backend alembic upgrade head
```

---

## 🏗️ Architecture

### Services

```
┌─────────────────────────────────────────────────┐
│                  FA-Platform                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐   ┌─────────────┐            │
│  │   Frontend   │──>│   Backend   │            │
│  │  (Nginx:80)  │   │  (FastAPI)  │            │
│  │  Port: 3000  │   │  Port: 8000 │            │
│  └──────────────┘   └──────┬──────┘            │
│                             │                    │
│                             ▼                    │
│                      ┌─────────────┐            │
│                      │  PostgreSQL │            │
│                      │  Port: 5432 │            │
│                      └─────────────┘            │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Container Details

#### Frontend Container
- **Image**: `nginx:alpine`
- **Purpose**: Serves static HTML/CSS/JS files
- **Port**: 3000 (external) → 80 (internal)
- **Health Check**: HTTP GET to `/health`

#### Backend Container
- **Image**: Custom (built from `backend/Dockerfile`)
- **Purpose**: FastAPI REST API
- **Port**: 8000 (external) → 8000 (internal)
- **Health Check**: HTTP GET to `/health`
- **Features**:
  - Multi-stage build (optimized size)
  - Non-root user (security)
  - Auto database initialization
  - Demo data seeding

#### Database Container
- **Image**: `postgres:16-alpine`
- **Purpose**: PostgreSQL database
- **Port**: 5432 (external) → 5432 (internal)
- **Health Check**: `pg_isready`
- **Persistent Volume**: `postgres_data`

---

## 💾 Volumes & Data Persistence

### Persistent Volumes

Docker volumes ensure data survives container restarts:

| Volume Name | Purpose | Location |
|-------------|---------|----------|
| `fa-platform-postgres-data` | Database data | `/var/lib/postgresql/data` |
| `fa-platform-uploads` | File uploads | `/app/uploads` |
| `fa-platform-chromadb` | Vector DB (AI features) | `/app/data/chromadb` |

### Volume Operations

```bash
# List volumes
docker volume ls | grep fa-platform

# Inspect volume
docker volume inspect fa-platform-postgres-data

# Backup volume data
docker run --rm \
  -v fa-platform-postgres-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data

# Remove all volumes (⚠️ destroys all data)
docker-compose down -v
```

### Data Backup Strategy

```bash
#!/bin/bash
# backup.sh - Create full backup

# Database backup
docker-compose exec db pg_dump -U fa_user financial_advisor > db_backup_$(date +%Y%m%d).sql

# Volume backups
docker run --rm \
  -v fa-platform-uploads:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/uploads_$(date +%Y%m%d).tar.gz /data

echo "✅ Backup complete"
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process or change port in .env
BACKEND_PORT=8001
```

#### 2. Database Connection Fails

**Error**: `could not connect to server: Connection refused`

**Solution**:
```bash
# Check database health
docker-compose ps

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

#### 3. SECRET_KEY Not Set

**Error**: `ValueError: SECRET_KEY environment variable is required`

**Solution**:
```bash
# Generate new SECRET_KEY
python3 -c 'import secrets; print(secrets.token_hex(32))'

# Add to .env file
echo "SECRET_KEY=your_generated_key" >> .env
```

#### 4. Permission Denied on docker-entrypoint.sh

**Error**: `permission denied: ./docker-entrypoint.sh`

**Solution**:
```bash
# Make script executable
chmod +x backend/docker-entrypoint.sh

# Rebuild
docker-compose up -d --build
```

#### 5. Out of Disk Space

**Error**: `no space left on device`

**Solution**:
```bash
# Clean up unused Docker resources
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

### Debugging Commands

```bash
# Check service health
docker-compose ps

# View real-time logs
docker-compose logs -f backend

# Inspect container
docker inspect fa-platform-backend

# Check network connectivity
docker-compose exec backend ping db

# Check environment variables
docker-compose exec backend env | grep SECRET_KEY
```

---

## 🚀 Production Deployment

### Pre-Deployment Checklist

- [ ] Generated new `SECRET_KEY`
- [ ] Changed `POSTGRES_PASSWORD`
- [ ] Set `DEBUG=False`
- [ ] Configured `ALLOWED_ORIGINS` with production domain
- [ ] Changed `DEMO_USER_PASSWORD`
- [ ] Set up HTTPS/TLS (use reverse proxy like Nginx or Caddy)
- [ ] Configured database backups
- [ ] Set up monitoring and logging
- [ ] Reviewed security settings

### Production Environment Variables

```bash
# .env for production
SECRET_KEY=<generated-64-char-hex>
POSTGRES_PASSWORD=<strong-password>
DEBUG=False
ALLOWED_ORIGINS=https://yourdomain.com
SEED_DEMO_DATA=false
```

### Using Docker Compose Override

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    command: ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
    restart: always

  db:
    restart: always
```

Run with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Cloud Platform Deployment

#### AWS ECS
```bash
# Install AWS CLI and configure
aws configure

# Push images to ECR
docker-compose build
docker tag fa-platform-backend:latest <ecr-repo-url>
docker push <ecr-repo-url>
```

#### DigitalOcean App Platform
```bash
# Use doctl CLI
doctl apps create --spec docker-compose.yml
```

#### Heroku
```bash
# Install heroku CLI
heroku container:push web --app your-app-name
heroku container:release web --app your-app-name
```

---

## 📊 Monitoring

### Health Checks

```bash
# Frontend
curl http://localhost:3000/health

# Backend
curl http://localhost:8000/health

# Database
docker-compose exec db pg_isready -U fa_user
```

### Resource Usage

```bash
# View container stats
docker stats

# Check disk usage
docker system df
```

---

## 🤝 Contributing

When developing with Docker:

1. Make code changes locally
2. Rebuild: `docker-compose up -d --build`
3. Test changes
4. Commit code (not `.env` file)

---

## 📝 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify `.env` configuration
3. Review [Troubleshooting](#troubleshooting) section
4. Open an issue on GitHub

---

**Happy Dockerizing! 🐳**
