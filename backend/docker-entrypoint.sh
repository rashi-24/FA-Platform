#!/bin/bash
# ============================================================================
# Docker Entrypoint Script for FA-Platform Backend
# Handles database initialization and health checks
# ============================================================================

set -e

echo "🚀 FA-Platform Backend Starting..."

# Function to wait for PostgreSQL to be ready
wait_for_postgres() {
    echo "⏳ Waiting for PostgreSQL to be ready..."

    max_retries=30
    retry_count=0

    until python -c "
import psycopg2
import os
import sys
from urllib.parse import urlparse

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('❌ DATABASE_URL not set')
    sys.exit(1)

parsed = urlparse(db_url)
try:
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=parsed.password,
        dbname=parsed.path[1:],
        connect_timeout=5
    )
    conn.close()
    print('✅ PostgreSQL is ready!')
    sys.exit(0)
except Exception as e:
    print(f'⏳ PostgreSQL not ready yet: {e}')
    sys.exit(1)
" 2>/dev/null; do
        retry_count=$((retry_count + 1))

        if [ $retry_count -ge $max_retries ]; then
            echo "❌ PostgreSQL did not become ready in time"
            exit 1
        fi

        echo "⏳ Attempt $retry_count/$max_retries - Waiting for PostgreSQL..."
        sleep 2
    done
}

# Function to initialize database
initialize_database() {
    echo "📊 Initializing database..."

    if python -c "
import sys
from database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = \\'public\\''))
        table_count = result.scalar()
        if table_count > 0:
            print(f'ℹ️  Database already has {table_count} tables')
            sys.exit(0)
        else:
            print('📊 Database is empty, needs initialization')
            sys.exit(1)
except Exception as e:
    print(f'📊 Database needs initialization: {e}')
    sys.exit(1)
" 2>/dev/null; then
        echo "✅ Database already initialized"
    else
        echo "🔧 Running database initialization..."
        python database.py init

        # Optionally seed demo data if SEED_DEMO_DATA is set
        if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
            echo "🌱 Seeding demo data..."
            python seed_data.py
        fi

        echo "✅ Database initialization complete"
    fi
}

# Main execution
main() {
    # Wait for PostgreSQL to be ready
    wait_for_postgres

    # Initialize database if needed
    initialize_database

    echo "✅ All startup checks passed"
    echo "🚀 Starting application..."
    echo ""

    # Execute the main command (passed as arguments)
    exec "$@"
}

# Run main function
main "$@"
