#!/bin/bash

echo "========================================="
echo "Financial Advisor Platform Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if (( $(echo "$python_version < 3.10" | bc -l) )); then
    echo "❌ Python 3.10 or higher is required. Current version: $python_version"
    exit 1
fi
echo "✅ Python version: $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
cd backend
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Create .env file
echo "Setting up environment configuration..."
if [ ! -f ../.env ]; then
    cp ../.env.example ../.env
    echo "✅ .env file created (please update with your settings)"
else
    echo "⚠️  .env file already exists"
fi
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p ../uploads
mkdir -p ../logs
echo "✅ Directories created"
echo ""

# Database setup
echo "========================================="
echo "Database Setup"
echo "========================================="
echo ""
echo "Choose database option:"
echo "1) SQLite (recommended for development)"
echo "2) PostgreSQL (recommended for production)"
read -p "Enter choice (1 or 2): " db_choice

if [ "$db_choice" = "1" ]; then
    echo ""
    echo "Using SQLite..."
    # Update database.py to use SQLite
    sed -i 's/# DATABASE_URL = "sqlite/DATABASE_URL = "sqlite/' database.py
    sed -i 's/DATABASE_URL = "postgresql/# DATABASE_URL = "postgresql/' database.py
    
    # Initialize database
    echo "Initializing database..."
    python database.py init
    echo "✅ SQLite database initialized"
    echo ""
    
    # Generate sample data
    read -p "Generate sample data? (y/n): " gen_data
    if [ "$gen_data" = "y" ]; then
        cd ../sample_data
        python generate_data.py
        cd ../backend
        echo "✅ Sample data generated"
    fi
    
elif [ "$db_choice" = "2" ]; then
    echo ""
    echo "PostgreSQL Setup"
    echo "----------------"
    echo "Please ensure PostgreSQL is installed and running."
    echo ""
    read -p "Database name [financial_advisor]: " db_name
    db_name=${db_name:-financial_advisor}
    
    read -p "Database user [advisor]: " db_user
    db_user=${db_user:-advisor}
    
    read -sp "Database password: " db_pass
    echo ""
    
    read -p "Database host [localhost]: " db_host
    db_host=${db_host:-localhost}
    
    read -p "Database port [5432]: " db_port
    db_port=${db_port:-5432}
    
    # Create database
    echo ""
    echo "Creating PostgreSQL database..."
    PGPASSWORD=$db_pass psql -h $db_host -U $db_user -c "CREATE DATABASE $db_name;" 2>/dev/null || true
    
    # Update .env file
    echo "DATABASE_URL=postgresql://$db_user:$db_pass@$db_host:$db_port/$db_name" >> ../.env
    
    # Initialize database
    export DATABASE_URL="postgresql://$db_user:$db_pass@$db_host:$db_port/$db_name"
    python database.py init
    echo "✅ PostgreSQL database initialized"
    echo ""
    
    # Generate sample data
    read -p "Generate sample data? (y/n): " gen_data
    if [ "$gen_data" = "y" ]; then
        cd ../sample_data
        python generate_data.py
        cd ../backend
        echo "✅ Sample data generated"
    fi
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "To start the backend server:"
echo "  cd backend"
echo "  source ../venv/bin/activate"
echo "  python main.py"
echo ""
echo "Then open your browser to:"
echo "  API: http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo "  Dashboard: Open frontend/index.html in browser"
echo ""
echo "Happy coding! 🚀"
