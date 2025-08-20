import os
import json
from datetime import datetime
from typing import Dict, List, Optional

def ensure_scan_directory(base_dir: str, company_name: str, date_str: Optional[str] = None, time_str: Optional[str] = None) -> str:
    """Ensures the scan directory structure exists."""
    company_dir = os.path.join(base_dir, company_name)
    os.makedirs(company_dir, exist_ok=True)
    
    if date_str:
        date_dir = os.path.join(company_dir, date_str)
        os.makedirs(date_dir, exist_ok=True)
        
        if time_str:
            time_dir = os.path.join(date_dir, time_str)
            os.makedirs(time_dir, exist_ok=True)
            return time_dir
        return date_dir
    
    return company_dir

def read_json_file(file_path: str) -> List[Dict]:
    """Read JSON/JSONL file with flexible format handling."""
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            if not content:
                return []

            # Try parsing as JSON array first
            try:
                json_content = json.loads(content)
                return json_content if isinstance(json_content, list) else [json_content]
            except json.JSONDecodeError:
                # If JSON array parsing fails, try line by line
                results = []
                for line in content.splitlines():
                    if line.strip():
                        try:
                            results.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                return results
    except Exception:
        return []

def process_nuclei_result(result: Dict) -> Optional[Dict]:
    """Process a nuclei result into a standardized format."""
    try:
        if not isinstance(result, dict):
            return None

        info = result.get('info', {})
        return {
            'template_name': result.get('template-id', ''),
            'severity': info.get('severity', 'Unknown').title(),
            'protocol': result.get('protocol', 'http'),
            'target': result.get('matched-at', ''),
            'details': info.get('description', ''),
            'cvss_score': info.get('classification', {}).get('cvss-score', 0.0),
            'recommendation': info.get('remediation', '')
        }
    except Exception:
        return None

def get_vulnerability_statistics(results: List[Dict]) -> Dict[str, int]:
    """Calculate vulnerability statistics."""
    stats = {
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0,
        'info': 0
    }
    
    for result in results:
        if isinstance(result, dict):
            severity = result.get('severity', '').lower()
            if severity in stats:
                stats[severity] += 1
    
    return stats

def format_scan_time(time_str: str) -> str:
    """Format time string from HHMM to HH:MM."""
    return f"{time_str[:2]}:{time_str[2:]}"

def format_scan_date(date_str: str) -> str:
    """Format date string from YYYYMMDD to DD/MM/YYYY."""
    return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[:4]}"

def get_company_scan_summary(base_dir: str, company_name: str) -> Dict:
    """Get summary of all scans for a company."""
    company_dir = os.path.join(base_dir, company_name)
    if not os.path.exists(company_dir):
        return {
            'name': company_name,
            'total_scans': 0,
            'last_scan': None,
            'total_vulnerabilities': {
                'info': 0,
                'low': 0,
                'medium': 0,
                'high': 0,
                'critical': 0
            }
        }
    
    total_vulnerabilities = {
        'info': 0,
        'low': 0,
        'medium': 0,
        'high': 0,
        'critical': 0
    }
    
    total_scans = 0
    last_scan = None
    domain_file = None
    
    # Find domain file
    for file in os.listdir(company_dir):
        if file.endswith('.txt'):
            domain_file = os.path.join(company_dir, file)
            break
    
    # Process scan results
    for date_dir in sorted(os.listdir(company_dir), reverse=True):
        date_path = os.path.join(company_dir, date_dir)
        if not os.path.isdir(date_path) or len(date_dir) != 8:
            continue
        
        for time_dir in sorted(os.listdir(date_path), reverse=True):
            time_path = os.path.join(date_path, time_dir)
            if not os.path.isdir(time_path) or len(time_dir) != 4:
                continue
            
            result_file = os.path.join(time_path, 'result.json')
            if not os.path.exists(result_file):
                continue
            
            total_scans += 1
            
            # Process results
            results = read_json_file(result_file)
            processed_results = []
            for result in results:
                processed = process_nuclei_result(result)
                if processed:
                    processed_results.append(processed)
            
            # Update statistics
            stats = get_vulnerability_statistics(processed_results)
            for severity, count in stats.items():
                total_vulnerabilities[severity] += count
            
            # Update last scan info
            if last_scan is None:
                last_scan = {
                    'date': format_scan_date(date_dir),
                    'time': format_scan_time(time_dir)
                }
    
    # Count active domains
    active_domains = 0
    if domain_file and os.path.exists(domain_file):
        with open(domain_file, 'r') as f:
            active_domains = sum(1 for line in f if line.strip())
    
    return {
        'name': company_name,
        'total_scans': total_scans,
        'last_scan': last_scan,
        'active_domains': active_domains,
        'total_vulnerabilities': total_vulnerabilities
    }
