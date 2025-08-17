#!/bin/bash

# EasyJet Tool Inventory System Startup Script

echo "🔧 Starting EasyJet Tool Inventory System..."

# Set environment variables
export PYTHONPATH="/home/user/webapp:$PYTHONPATH"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data models qr_codes static/images templates

# Check if database exists, if not initialize with sample data
if [ ! -f "data/tool_inventory.db" ]; then
    echo "🗄️  Initializing database..."
    python -c "
from src.database.database import ToolInventoryDatabase
db = ToolInventoryDatabase()
print('Database initialized successfully')
"
fi

# Copy environment file if not exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating environment configuration..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before running the application"
fi

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application, choose one of:"
echo "   1. Simple Streamlit: streamlit run app.py"
echo "   2. Production mode:  python run_app.py"
echo "   3. Docker:          docker-compose up -d"
echo ""

# Ask user which mode to start
read -p "Start the application now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌟 Starting in production mode..."
    python run_app.py
fi