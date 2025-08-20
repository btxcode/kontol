import subprocess
import os
from datetime import datetime
import json
from typing import Dict
from db import get_db_connection

def run_command(command: str) -> str:
    """Execute a shell command and return its output."""
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
    cursor.execute("SELECT id FROM companies WHERE name = %s", (company_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO companies (name) VALUES (%s)", (company_name,))
    return cursor.lastrowid

def insert_scan(cursor, company_id: int, target_domain: str, scan_date: str, scan_time: str, domain_file: str) -> int:
    cursor.execute(
        "INSERT INTO scans (company_id, target_domain, scan_date, scan_time, domain_file) VALUES (%s, %s, %s, %s, %s)",
        (company_id, target_domain, scan_date, scan_time, domain_file)
    )
    return cursor.lastrowid

def insert_scan_result(cursor, scan_id: int, result: Dict):
    cursor.execute(
        """
        INSERT INTO scan_results
        (scan_id, template_name, severity, protocol, target, details, cvss_score, recommendation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            scan_id,
            result.get('template_name'),
            result.get('severity'),
            result.get('protocol'),
            result.get('target'),
            result.get('details'),
            result.get('cvss_score'),
            result.get('recommendation')
        )
    )

def scan_target(target_domain: str, company_name: str) -> Dict:
    """
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
    subfinder_httpx_output = run_command(subfinder_httpx_cmd)
    
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
            output = run_command(cmd)
            with open(validated_urls_file, 'a') as f:
                f.write(output)
        except Exception as e:
            print(f"Error running command '{cmd}': {str(e)}")
    
    # Step 3: Run nuclei scan on validated URLs
    print("\n[3/3] Running nuclei for vulnerability scanning on validated URLs...")
    result_file = os.path.join(time_dir, 'result.json')
    nuclei_cmd = f"nuclei -l {validated_urls_file} -silent -rl 50 -json-export {result_file}"
    run_command(nuclei_cmd)
    
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
            scan_id = insert_scan(cursor, company_id, target_domain, now.date(), now.time(), validated_urls_file)
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
