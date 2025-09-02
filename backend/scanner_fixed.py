import subprocess
import os
import sys
import time
from datetime import datetime
import json
from typing import Dict, List
from db import get_db_connection

# Import active_scans from app module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import active_scans

def update_scan_status(scan_id: int, status: str, progress: int = None):
    """Update the status of an active scan."""
    if scan_id in active_scans:
        active_scans[scan_id]['status'] = status
        if progress is not None:
            active_scans[scan_id]['progress'] = progress

def run_command_safely(command_parts: List[str]) -> str:
    """Execute a shell command safely without shell=True."""
    try:
        print(f"Running command: {' '.join(command_parts)}")
        process = subprocess.Popen(
            command_parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"Command failed: {stderr}")
        return stdout
    except Exception as e:
        raise Exception(f"Error running command {' '.join(command_parts)}: {str(e)}")

def run_command_safely_with_shell(command: str) -> str:
    """Execute a shell command with shell=True for complex pipelines."""
    try:
        print(f"Running command: {command}")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"Command failed: {stderr}")
        return stdout
    except Exception as e:
        raise Exception(f"Error running command {command}: {str(e)}")

def insert_company(cursor, company_name: str) -> int:
    """Insert or get existing company."""
    cursor.execute("SELECT id FROM companies WHERE name = %s", (company_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO companies (name) VALUES (%s)", (company_name,))
    return cursor.lastrowid

def insert_scan(cursor, company_id: int, target_domain: str, domain_file: str) -> int:
    """Insert a new scan record."""
    cursor.execute(
        """INSERT INTO scans (company_id, target_domain, status, domain_file) 
           VALUES (%s, %s, 'initializing', %s)""",
        (company_id, target_domain, domain_file)
    )
    return cursor.lastrowid

def update_scan_status_db(cursor, scan_id: int, status: str):
    """Update scan status in database."""
    cursor.execute(
        "UPDATE scans SET status = %s WHERE id = %s",
        (status, scan_id)
    )

def insert_scan_result(cursor, scan_id: int, result: Dict):
    """Insert a scan result into the database."""
    cursor.execute(
        """
        INSERT INTO scan_results
        (scan_id, template_name, severity, protocol, target, details, cvss_score, recommendation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            scan_id,
            result.get('template_name', ''),
            result.get('severity', 'Unknown'),
            result.get('protocol', 'http'),
            result.get('target', ''),
            result.get('details', ''),
            result.get('cvss_score', 0.0),
            result.get('recommendation', '')
        )
    )

def run_and_process_scan(target_domain: str, company_name: str, scan_id: int):
    """
    Perform a complete vulnerability scan using subfinder, httpx, and nuclei.
    Updates scan status and saves results to database.
    
    Args:
        target_domain: The domain to scan
        company_name: Name of the company being scanned
        scan_id: The unique scan ID for tracking
    """
    try:
        print(f"\nStarting comprehensive scan for {target_domain} (Scan ID: {scan_id})")
        
        # Update scan status to running
        update_scan_status(scan_id, 'running', 10)
        
        # Create timestamp for directory structure
        now = datetime.now()
        date_str = now.strftime('%Y%m%d')
        time_str = now.strftime('%H%M')
        
        # Create directory structure
        base_dir = os.path.dirname(os.path.abspath(__file__))
        company_dir = os.path.join(base_dir, 'scan_results', company_name)
        date_dir = os.path.join(company_dir, date_str)
        time_dir = os.path.join(date_dir, time_str)
        os.makedirs(time_dir, exist_ok=True)
        
        # Create domain output file path
        domain_file = os.path.join(company_dir, f'{target_domain}.txt')
        
        # Step 1: Run subfinder and pipe to httpx
        print("\n[1/3] Running subfinder and httpx...")
        update_scan_status(scan_id, 'running', 20)
        
        subfinder_httpx_cmd = f"subfinder -d {target_domain} -all | httpx"
        subfinder_httpx_output = run_command_safely_with_shell(subfinder_httpx_cmd)
        
        # Save subfinder and httpx output to domain_file
        with open(domain_file, 'w') as f:
            f.write(subfinder_httpx_output)
        
        # Step 2: Run additional tools sequentially and collect their outputs
        print("\n[2/3] Running additional URL collection tools...")
        update_scan_status(scan_id, 'running', 40)
        
        validated_urls_file = os.path.join(company_dir, f'{target_domain}_validated_urls.txt')
        
        # Define excluded extensions for gauplus
        excluded_extensions = "jpg,jpeg,png,gif,svg,css,js,woff,woff2,ttf,eot,ico,pdf,txt,zip,rar,7z,tar,gz,bz2,mp4,mp3,mov,avi,mkv"
        
        # Clear or create validated_urls_file
        with open(validated_urls_file, 'w') as f:
            pass
        
        # Define commands for the 4 tools
        tool_commands = [
            f"echo {target_domain} | waybackurls",
            f"echo {target_domain} | gauplus -subs -b {excluded_extensions}",
            f"echo {target_domain} | hakrawler -d 3 -subs -u",
            f"echo {target_domain} | katana -d 3 -silent -rl 10"
        ]
        
        for i, cmd in enumerate(tool_commands):
            try:
                print(f"Running command: {cmd}")
                progress = 40 + (i + 1) * 10
                update_scan_status(scan_id, 'running', progress)
                
                output = run_command_safely_with_shell(cmd)
                with open(validated_urls_file, 'a') as f:
                    f.write(output)
            except Exception as e:
                print(f"Error running command '{cmd}': {str(e)}")
        
        # Step 3: Run nuclei scan on validated URLs
        print("\n[3/3] Running nuclei for vulnerability scanning...")
        update_scan_status(scan_id, 'running', 80)
        
        result_file = os.path.join(time_dir, 'result.json')
        nuclei_cmd = f"nuclei -l {validated_urls_file} -silent -rl 50 -json-export {result_file}"
        run_command_safely_with_shell(nuclei_cmd)
        
        # Read and parse results
        results = []
        try:
            with open(result_file, 'r') as f:
                content = f.read().strip()
                if content:
                    results = json.loads(content)
                    if not isinstance(results, list):
                        results = [results]
        except Exception as e:
            print(f"Error reading results: {str(e)}")
        
        # Save results to MySQL
        update_scan_status(scan_id, 'running', 90)
        connection = get_db_connection()
        db_scan_id = None
        
        if connection is None:
            print("Failed to connect to database. Results not saved to DB.")
        else:
            try:
                cursor = connection.cursor()
                company_id = insert_company(cursor, company_name)
                db_scan_id = insert_scan(cursor, company_id, target_domain, validated_urls_file)
                
                # Update scan status to running in DB
                update_scan_status_db(cursor, db_scan_id, 'running')
                
                for result in results:
                    # Format result dict to match DB columns
                    formatted_result = {
                        'template_name': result.get('template-id', ''),
                        'severity': result.get('info', {}).get('severity', 'Unknown').title(),
                        'protocol': result.get('protocol', 'http'),
                        'target': result.get('matched-at', ''),
                        'details': result.get('info', {}).get('description', ''),
                        'cvss_score': result.get('info', {}).get('classification', {}).get('cvss-score', 0.0),
                        'recommendation': result.get('info', {}).get('remediation', '')
                    }
                    insert_scan_result(cursor, db_scan_id, formatted_result)
                
                # Update scan status to completed
                update_scan_status_db(cursor, db_scan_id, 'completed')
                connection.commit()
                cursor.close()
                connection.close()
                print("Results saved to database successfully.")
                
            except Exception as e:
                print(f"Error saving results to database: {str(e)}")
                if connection:
                    connection.rollback()
                if 'cursor' in locals():
                    cursor.close()
                if connection:
                    connection.close()
        
        # Update final status
        update_scan_status(scan_id, 'completed', 100)
        print(f"\nScan completed. Results saved in: {result_file}")
        
        # Keep scan in active_scans for a while before removing
        time.sleep(30)  # Keep for 30 seconds after completion
        if scan_id in active_scans:
            del active_scans[scan_id]
        
    except Exception as e:
        print(f"Error during scan: {str(e)}")
        update_scan_status(scan_id, 'failed', 0)
        
        # Keep failed scan in active_scans for a while
        time.sleep(60)  # Keep for 60 seconds after failure
        if scan_id in active_scans:
            del active_scans[scan_id]

def scan_target(target_domain: str, company_name: str) -> Dict:
    """
    Legacy function for backward compatibility.
    Perform a complete vulnerability scan using subfinder, httpx, and nuclei.
    Saves results in the proper directory structure and stores results in MySQL.
    
    Args:
        target_domain: The domain to scan
        company_name: Name of the company being scanned
    
    Returns:
        Dict containing scan information
    """
    print(f"\nStarting comprehensive scan for {target_domain}")
    
    # Create timestamp for directory structure
    now = datetime.now()
    date_str = now.strftime('%Y%m%d')
    time_str = now.strftime('%H%M')
    
    # Create directory structure
    company_dir = os.path.join('scan_results', company_name)
    date_dir = os.path.join(company_dir, date_str)
    time_dir = os.path.join(date_dir, time_str)
    os.makedirs(time_dir, exist_ok=True)
    
    # Create domain output file path
    domain_file = os.path.join(company_dir, f'{target_domain}.txt')
    
    # Step 1: Run subfinder and pipe to httpx
    print("\n[1/3] Running subfinder and httpx...")
    subfinder_httpx_cmd = f"subfinder -d {target_domain} -all | httpx"
    subfinder_httpx_output = run_command_safely_with_shell(subfinder_httpx_cmd)
    
    # Save subfinder and httpx output to domain_file
    with open(domain_file, 'w') as f:
        f.write(subfinder_httpx_output)
    
    # Step 2: Run additional tools sequentially and collect their outputs
    validated_urls_file = os.path.join(company_dir, f'{target_domain}_validated_urls.txt')
    
    # Define excluded extensions for gauplus
    excluded_extensions = "jpg,jpeg,png,gif,svg,css,js,woff,woff2,ttf,eot,ico,pdf,txt,zip,rar,7z,tar,gz,bz2,mp4,mp3,mov,avi,mkv"
    
    # Clear or create validated_urls_file
    with open(validated_urls_file, 'w') as f:
        pass
    
    # Define commands for the 4 tools
    tool_commands = [
        f"echo {target_domain} | waybackurls",
        f"echo {target_domain} | gauplus -subs -b {excluded_extensions}",
        f"echo {target_domain} | hakrawler -d 3 -subs -u",
        f"echo {target_domain} | katana -d 3 -silent -rl 10"
    ]
    
    print("\n[2/3] Running additional URL collection tools (waybackurls, gauplus, hakrawler, katana)...")
    for cmd in tool_commands:
        try:
            print(f"Running command: {cmd}")
            output = run_command_safely_with_shell(cmd)
            with open(validated_urls_file, 'a') as f:
                f.write(output)
        except Exception as e:
            print(f"Error running command '{cmd}': {str(e)}")
    
    # Step 3: Run nuclei scan on validated URLs
    print("\n[3/3] Running nuclei for vulnerability scanning on validated URLs...")
    result_file = os.path.join(time_dir, 'result.json')
    nuclei_cmd = f"nuclei -l {validated_urls_file} -silent -rl 50 -json-export {result_file}"
    run_command_safely_with_shell(nuclei_cmd)
    
    # Read and parse results
    results = []
    try:
        with open(result_file, 'r') as f:
            results = json.load(f)
            if not isinstance(results, list):
                results = [results]
    except Exception as e:
        print(f"Error reading results: {str(e)}")
    
    # Save results to MySQL
    connection = get_db_connection()
    if connection is None:
        print("Failed to connect to database. Results not saved to DB.")
    else:
        try:
            cursor = connection.cursor()
            company_id = insert_company(cursor, company_name)
            scan_id = insert_scan(cursor, company_id, target_domain, validated_urls_file)
            for result in results:
                # Format result dict to match DB columns
                formatted_result = {
                    'template_name': result.get('template-id', ''),
                    'severity': result.get('info', {}).get('severity', 'Unknown').title(),
                    'protocol': result.get('protocol', 'http'),
                    'target': result.get('matched-at', ''),
                    'details': result.get('info', {}).get('description', ''),
                    'cvss_score': result.get('info', {}).get('classification', {}).get('cvss-score', 0.0),
                    'recommendation': result.get('info', {}).get('remediation', '')
                }
                insert_scan_result(cursor, scan_id, formatted_result)
            connection.commit()
            cursor.close()
            connection.close()
            print("Results saved to database successfully.")
        except Exception as e:
            print(f"Error saving results to database: {str(e)}")
    
    print(f"\nScan completed. Results saved in: {result_file}")
    
    return {
        'company_name': company_name,
        'target_domain': target_domain,
        'date': date_str,
        'time': time_str,
        'domain_file': domain_file,
        'result_file': result_file
    }

def get_scan_results(result_file: str) -> list:
    """
    Read and parse the nuclei scan results.
    
    Args:
        result_file: Path to the nuclei result JSON file
    
    Returns:
        List of vulnerability findings
    """
    try:
        with open(result_file, 'r') as f:
            try:
                # With json-export, nuclei outputs a JSON array
                results = json.load(f)
                if not isinstance(results, list):
                    results = [results]
                
                formatted_results = []
                for result in results:
                    finding = {
                        'template_name': result.get('template-id', ''),
                        'severity': result.get('info', {}).get('severity', 'Unknown').title(),
                        'protocol': result.get('protocol', 'http'),
                        'target': result.get('matched-at', ''),
                        'details': result.get('info', {}).get('description', ''),
                        'cvss_score': result.get('info', {}).get('classification', {}).get('cvss-score', 0.0),
                        'recommendation': result.get('info', {}).get('remediation', '')
                    }
                    formatted_results.append(finding)
                return formatted_results
            except json.JSONDecodeError:
                print("Error decoding JSON file")
                return []
    except Exception as e:
        print(f"Error reading results: {str(e)}")
        return []