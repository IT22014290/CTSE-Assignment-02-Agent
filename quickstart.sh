#!/bin/bash

# 🚀 CTSE Assignment 2 - Quick Start Script
# This script sets up and runs the complete MAS Code Review Pipeline

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   MAS Code Review Pipeline - Quick Start                ║"
echo "║   CTSE Assignment 2 - Multi-Agent System                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Function to print colored output
print_info() {
    echo "ℹ️  $1"
}

print_success() {
    echo "✅ $1"
}

print_warning() {
    echo "⚠️  $1"
}

print_error() {
    echo "❌ $1"
}

# Check Python version
print_info "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
print_success "Python $python_version found"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate
print_success "Virtual environment activated"

# Install dependencies
print_info "Installing dependencies..."
pip install -q -r requirements.txt
print_success "Dependencies installed"

# Check Ollama
print_info "Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    print_success "Ollama found"
else
    print_warning "Ollama not found. Please install from https://ollama.com"
    print_info "After installing Ollama, run: ollama serve"
fi

# Show menu
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Choose how to run the pipeline:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "1) CLI - Command Line (simple, no UI)"
echo "2) Web UI - Modern React Frontend"
echo "3) Docker - Full Stack (Recommended for production)"
echo "4) Run Evaluations - Test each agent"
echo "5) Exit"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Running CLI Mode..."
        echo ""
        read -p "Enter directory to analyze (default: tests/sample_code): " input_dir
        input_dir=${input_dir:-tests/sample_code}
        
        read -p "Use parallel execution? (y/n, default: n): " parallel
        parallel_flag=""
        if [ "$parallel" = "y" ] || [ "$parallel" = "Y" ]; then
            parallel_flag="--parallel"
        fi
        
        python main.py --input "$input_dir" $parallel_flag
        ;;
        
    2)
        echo ""
        echo "🎨 Starting Web UI..."
        echo ""
        
        # Check if Node.js is installed
        if ! command -v npm &> /dev/null; then
            print_error "Node.js/npm not found. Please install from https://nodejs.org"
            exit 1
        fi
        
        print_info "Starting API server..."
        python -m uvicorn api:app --reload &
        API_PID=$!
        sleep 3
        
        print_info "Setting up frontend..."
        cd frontend
        if [ ! -d "node_modules" ]; then
            npm install -q
        fi
        
        print_success "Starting frontend on http://localhost:3000"
        npm start
        
        # Cleanup
        kill $API_PID 2>/dev/null || true
        ;;
        
    3)
        echo ""
        echo "🐳 Starting Docker Stack..."
        echo ""
        
        if ! command -v docker &> /dev/null; then
            print_error "Docker not found. Please install from https://www.docker.com"
            exit 1
        fi
        
        print_info "Starting all services..."
        docker-compose up
        ;;
        
    4)
        echo ""
        echo "🧪 Running Evaluations..."
        echo ""
        
        print_info "Running Member 1 (Coordinator) evaluation..."
        python evaluation/eval_coordinator.py
        echo ""
        
        print_info "Running Member 2 (Security) evaluation..."
        python evaluation/eval_security.py
        echo ""
        
        print_info "Running Member 3 (Report) evaluation..."
        python evaluation/eval_report.py
        echo ""
        
        print_success "All evaluations complete!"
        ;;
        
    5)
        echo "Exiting..."
        exit 0
        ;;
        
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
print_success "Done!"
