#!/usr/bin/env python3
import os
import sys
import subprocess
from typing import List, Tuple

def check_tool(tool: str) -> Tuple[bool, str]:
    """Check if a required tool is installed and available."""
    try:
        process = subprocess.Popen(
            [tool, '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        output = stdout.decode() if stdout else stderr.decode()
        return True, output.strip()
    except FileNotFoundError:
        return False, f"{tool} not found"

def check_dependencies() -> bool:
    """Check all required security tools are installed."""
    required_tools = ['subfinder', 'httpx', 'nuclei']
    missing_tools = []
    
    print("Checking required security tools...")
    for tool in required_tools:
        installed, version = check_tool(tool)
        if installed:
            print(f"✓ {tool}: {version}")
        else:
            print(f"✗ {tool}: Not found")
            missing_tools.append(tool)
    
    if missing_tools:
        print("\nMissing required tools. Please install:")
        for tool in missing_tools:
            print(f"\n{tool}:")
            if tool == 'subfinder':
                print("    GO111MODULE=on go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")
            elif tool == 'httpx':
                print("    GO111MODULE=on go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest")
            elif tool == 'nuclei':
                print("    GO111MODULE=on go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest")
        return False
    
    return True

def setup_environment():
    """Set up the application environment."""
    # Ensure results directory exists
    results_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'backend',
        'scan_results'
    )
    os.makedirs(results_dir, exist_ok=True)
    
    # Set environment variables
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_APP', 'backend.app')

def main():
    """Main entry point for the application."""
    # Check security tools are installed
    if not check_dependencies():
        sys.exit(1)
    
    # Set up environment
    setup_environment()
    
    try:
        # Import Flask app
        from backend.app import app
        
        # Start the server
        print("\nStarting Vulnerability Scanner...")
        print("Access the web interface at: http://localhost:5000")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
        
    except Exception as e:
        print(f"\nError starting server: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
