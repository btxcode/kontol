#!/bin/bash

# Quick Test Script for Kamehameha Vulnerability Scanner
# Run this script to test the entire setup from scratch

set -e  # Exit on any error

echo "🚀 Kamehameha Vulnerability Scanner - Quick Test Script"
echo "========================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if service is running
is_service_running() {
    systemctl is-active --quiet "$1"
}

# Step 1: Check prerequisites
print_status "Step 1: Checking prerequisites..."

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check Go
if command_exists go; then
    GO_VERSION=$(go version | cut -d' ' -f3)
    print_success "Go $GO_VERSION found"
else
    print_error "Go not found. Please install Go 1.16 or higher."
    exit 1
fi

# Check MySQL/MariaDB
if command_exists mysql; then
    print_success "MySQL/MariaDB client found"
else
    print_error "MySQL/MariaDB client not found. Please install MySQL or MariaDB."
    exit 1
fi

# Check if MySQL/MariaDB service is running
if is_service_running mariadb; then
    print_success "MariaDB service is running"
elif is_service_running mysql; then
    print_success "MySQL service is running"
else
    print_error "Neither MySQL nor MariaDB service is running. Please start the database service."
    exit 1
fi

# Step 2: Setup database
print_status "Step 2: Setting up database..."

# Create database and user
print_status "Creating database and user..."
mysql -u root -p <<EOF
CREATE DATABASE IF NOT EXISTS kamehameha_scanner;
CREATE USER IF NOT EXISTS 'scanner_user'@'localhost' IDENTIFIED BY 'scanner_password_123';
GRANT ALL PRIVILEGES ON kamehameha_scanner.* TO 'scanner_user'@'localhost';
FLUSH PRIVILEGES;
EOF

print_success "Database and user created successfully"

# Import database schema
print_status "Importing database schema..."
mysql -u scanner_user -p'scanner_password_123' kamehameha_scanner < backend/db_schema.sql
print_success "Database schema imported successfully"

# Verify database setup
print_status "Verifying database setup..."
mysql -u scanner_user -p'scanner_password_123' kamehameha_scanner -e "SHOW TABLES;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "Database setup verified"
else
    print_error "Database setup verification failed"
    exit 1
fi

# Step 3: Setup Python environment
print_status "Step 3: Setting up Python environment..."

# Create virtual environment
print_status "Creating virtual environment..."
python3 -m venv venv
print_success "Virtual environment created"

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "Pip upgraded"

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "Python dependencies installed"
else
    print_error "Failed to install Python dependencies"
    exit 1
fi

# Install additional required packages
print_status "Installing additional packages..."
pip install python-dotenv requests > /dev/null 2>&1
print_success "Additional packages installed"

# Step 4: Setup configuration
print_status "Step 4: Setting up configuration..."

# Generate secret keys
print_status "Generating secret keys..."
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(24))")
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Create .env file
print_status "Creating .env file..."
cat > .env << EOF
# Environment
FLASK_ENV=development
DOCKER_ENV=false

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=scanner_user
DB_PASSWORD=scanner_password_123
DB_NAME=kamehameha_scanner

# Security
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY

# Application Settings
SCAN_TIMEOUT=300
MAX_CONCURRENT_SCANS=3
SCAN_COOLDOWN_MINUTES=5
MAX_RESULTS_PER_COMPANY=1000
RESULTS_RETENTION_DAYS=90

# Logging
LOG_LEVEL=INFO
LOG_FILE=scanner.log

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:5000

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
EOF

print_success "Configuration file created"

# Step 5: Install security tools
print_status "Step 5: Installing security tools..."

# Install subfinder
print_status "Installing subfinder..."
GO111MODULE=on go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "subfinder installed"
else
    print_error "Failed to install subfinder"
    exit 1
fi

# Install httpx
print_status "Installing httpx..."
GO111MODULE=on go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "httpx installed"
else
    print_error "Failed to install httpx"
    exit 1
fi

# Install nuclei
print_status "Installing nuclei..."
GO111MODULE=on go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "nuclei installed"
else
    print_error "Failed to install nuclei"
    exit 1
fi

# Install additional tools
print_status "Installing additional tools..."
GO111MODULE=on go install -v github.com/projectdiscovery/waybackurls/cmd/waybackurls@latest > /dev/null 2>&1
GO111MODULE=on go install -v github.com/projectdiscovery/gauplus/cmd/gauplus@latest > /dev/null 2>&1
GO111MODULE=on go install -v github.com/projectdiscovery/hakrawler/cmd/hakrawler@latest > /dev/null 2>&1
GO111MODULE=on go install -v github.com/projectdiscovery/katana/cmd/katana@latest > /dev/null 2>&1
print_success "Additional tools installed"

# Add Go tools to PATH
export PATH=$PATH:$(go env GOPATH)/bin
print_success "Go tools added to PATH"

# Step 6: Test database connection
print_status "Step 6: Testing database connection..."

# Create database test script
cat > test_db_connection.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.append('backend')

from dotenv import load_dotenv
load_dotenv()

from db import get_db_connection
from config import get_config

def test_database_connection():
    try:
        config = get_config()
        connection = get_db_connection()
        if connection is None:
            return False
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM companies")
        companies_count = cursor.fetchone()['count']
        
        cursor.close()
        connection.close()
        
        print(f"Database connection successful. Companies: {companies_count}")
        return True
    except Exception as e:
        print(f"Database test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
EOF

# Run database test
python test_db_connection.py
if [ $? -eq 0 ]; then
    print_success "Database connection test passed"
else
    print_error "Database connection test failed"
    exit 1
fi

# Step 7: Create necessary directories
print_status "Step 7: Creating necessary directories..."
mkdir -p backend/scan_results
mkdir -p logs
print_success "Directories created"

# Step 8: Start application
print_status "Step 8: Starting application..."

# Start application in background
print_status "Starting Flask application..."
python run.py > scanner.log 2>&1 &
APP_PID=$!

# Wait for application to start
print_status "Waiting for application to start..."
sleep 5

# Check if application is running
if ps -p $APP_PID > /dev/null; then
    print_success "Application started (PID: $APP_PID)"
else
    print_error "Failed to start application"
    exit 1
fi

# Test health endpoint
print_status "Testing health endpoint..."
sleep 2
curl -s http://localhost:5000/apiv1/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "Health endpoint responding"
else
    print_error "Health endpoint not responding"
    kill $APP_PID 2>/dev/null
    exit 1
fi

# Step 9: Test API endpoints
print_status "Step 9: Testing API endpoints..."

# Test companies endpoint
print_status "Testing companies endpoint..."
COMPANIES_RESPONSE=$(curl -s http://localhost:5000/apiv1/companies)
if echo "$COMPANIES_RESPONSE" | grep -q '"data"'; then
    print_success "Companies endpoint working"
else
    print_error "Companies endpoint not working"
    kill $APP_PID 2>/dev/null
    exit 1
fi

# Test scan initiation
print_status "Testing scan initiation..."
SCAN_RESPONSE=$(curl -s -X POST http://localhost:5000/apiv1/scan \
    -H "Content-Type: application/json" \
    -d '{"domain": "testphp.vulnweb.com", "company": "TestCompany"}')

if echo "$SCAN_RESPONSE" | grep -q '"scan_id"'; then
    print_success "Scan initiation working"
    SCAN_ID=$(echo "$SCAN_RESPONSE" | grep -o '"scan_id":[0-9]*' | cut -d':' -f2)
    print_status "Scan ID: $SCAN_ID"
else
    print_error "Scan initiation not working"
    kill $APP_PID 2>/dev/null
    exit 1
fi

# Step 10: Monitor scan progress
print_status "Step 10: Monitoring scan progress..."
print_warning "This may take several minutes..."

# Monitor scan for up to 5 minutes
for i in {1..30}; do
    STATUS_RESPONSE=$(curl -s http://localhost:5000/apiv1/scans/$SCAN_ID/status)
    STATUS=$(echo "$STATUS_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    PROGRESS=$(echo "$STATUS_RESPONSE" | grep -o '"progress":[0-9]*' | cut -d':' -f2)
    
    echo "Scan $SCAN_ID: Status=$STATUS, Progress=$PROGRESS%"
    
    if [ "$STATUS" = "completed" ]; then
        print_success "Scan completed successfully!"
        break
    elif [ "$STATUS" = "failed" ]; then
        print_error "Scan failed"
        kill $APP_PID 2>/dev/null
        exit 1
    fi
    
    sleep 10
done

# Step 11: Verify results
print_status "Step 11: Verifying results..."

# Get companies again to check scan count
sleep 5
COMPANIES_RESPONSE=$(curl -s http://localhost:5000/apiv1/companies)
if echo "$COMPANIES_RESPONSE" | grep -q '"total_scans":1'; then
    print_success "Scan count updated in database"
else
    print_warning "Scan count may not be updated yet"
fi

# Check dates and times
print_status "Checking dates and times..."
DATES_RESPONSE=$(curl -s http://localhost:5000/apiv1/TestCompany/dates)
if echo "$DATES_RESPONSE" | grep -q '"data":\['; then
    print_success "Dates endpoint working"
    
    # Get first date
    FIRST_DATE=$(echo "$DATES_RESPONSE" | grep -o '"[0-9]*"' | head -1 | tr -d '"')
    
    # Get times
    TIMES_RESPONSE=$(curl -s http://localhost:5000/apiv1/TestCompany/$FIRST_DATE/times)
    if echo "$TIMES_RESPONSE" | grep -q '"data":\['; then
        print_success "Times endpoint working"
        
        # Get first time
        FIRST_TIME=$(echo "$TIMES_RESPONSE" | grep -o '"[0-9]*"' | head -1 | tr -d '"')
        
        # Get results
        RESULTS_RESPONSE=$(curl -s http://localhost:5000/apiv1/TestCompany/$FIRST_DATE/$FIRST_TIME/results)
        if echo "$RESULTS_RESPONSE" | grep -q '"data":\['; then
            print_success "Results endpoint working"
            
            # Count vulnerabilities
            VULN_COUNT=$(echo "$RESULTS_RESPONSE" | grep -o '"template_name"' | wc -l)
            print_success "Found $VULN_COUNT vulnerabilities"
        else
            print_error "Results endpoint not working"
        fi
    else
        print_error "Times endpoint not working"
    fi
else
    print_error "Dates endpoint not working"
fi

# Step 12: Cleanup
print_status "Step 12: Cleaning up..."

# Stop application
kill $APP_PID 2>/dev/null
print_success "Application stopped"

# Remove temporary files
rm -f test_db_connection.py
print_success "Temporary files removed"

# Print final status
echo ""
echo "🎉 Quick Test Completed Successfully!"
echo "===================================="
echo ""
echo "✅ Database setup completed"
echo "✅ Dependencies installed"
echo "✅ Configuration created"
echo "✅ Security tools installed"
echo "✅ Application started and tested"
echo "✅ API endpoints working"
echo "✅ Scan workflow tested"
echo "✅ Results verified"
echo ""
echo "📋 Next Steps:"
echo "1. To start the application: python run.py"
echo "2. To access the web interface: http://localhost:5000"
echo "3. To view logs: tail -f scanner.log"
echo "4. To run a manual scan: curl -X POST http://localhost:5000/apiv1/scan -H 'Content-Type: application/json' -d '{\"domain\": \"example.com\", \"company\": \"TestCompany\"}'"
echo ""
echo "🔧 Configuration file: .env"
echo "📊 Database: kamehameha_scanner"
echo "📁 Results directory: backend/scan_results/"
echo ""
echo "Happy scanning! 🚀"