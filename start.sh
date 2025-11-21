#!/bin/bash

# Visual AI Assistant - Quick Start Script

echo "====================================="
echo "Visual AI Assistant - Quick Start"
echo "====================================="
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  No .env file found!"
    echo "Creating .env from .env.example..."
    cp backend/.env.example backend/.env
    echo "✓ Created backend/.env"
    echo ""
    echo "📝 IMPORTANT: Edit backend/.env with your API keys before continuing!"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

# Check if venv exists
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
    echo "✓ Virtual environment created"
fi

# Activate venv and install dependencies
echo ""
echo "Installing dependencies..."
cd backend
source venv/bin/activate
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Check if ChromaDB directory exists
if [ ! -d "data/chroma" ]; then
    echo "Creating ChromaDB directory..."
    mkdir -p data/chroma
    echo "✓ ChromaDB directory created"
fi

# Start backend
echo ""
echo "====================================="
echo "Starting Backend Server..."
echo "====================================="
echo ""
echo "Backend will be available at: http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python run.py
