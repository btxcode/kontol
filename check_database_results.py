#!/usr/bin/env python3
"""
Script untuk melihat hasil scan di database
"""

import sys
import os
sys.path.append('backend')

from dotenv import load_dotenv
load_dotenv()

from db import get_db_connection

def print_header(title):
    """Print formatted header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_companies(cursor):
    """Print companies data."""
    print("🏢 COMPANIES")
    print("-" * 30)
    cursor.execute("SELECT * FROM companies ORDER BY name")
    companies = cursor.fetchall()
    
    if not companies:
        print("  No companies found")
        return
    
    for company in companies:
        print(f"  ID: {company['id']:<3} | Name: {company['name']:<20} | Created: {company['created_at']}")

def print_scans(cursor):
    """Print scans data."""
    print("\n📊 SCANS")
    print("-" * 80)
    cursor.execute("""
        SELECT s.id, c.name as company_name, s.target_domain, s.status, s.scan_datetime
        FROM scans s
        JOIN companies c ON s.company_id = c.id
        ORDER BY s.scan_datetime DESC
    """)
    scans = cursor.fetchall()
    
    if not scans:
        print("  No scans found")
        return
    
    for scan in scans:
        status_color = {
            'completed': '✅',
            'running': '🔄',
            'failed': '❌',
            'initializing': '⏳'
        }.get(scan['status'], '❓')
        
        print(f"  ID: {scan['id']:<3} | {status_color} {scan['status']:<12} | "
              f"Company: {scan['company_name']:<15} | Domain: {scan['target_domain']:<25} | "
              f"Time: {scan['scan_datetime']}")

def print_scan_results(cursor):
    """Print scan results data."""
    print("\n🔍 SCAN RESULTS")
    print("-" * 100)
    cursor.execute("""
        SELECT sr.id, sr.template_name, sr.severity, sr.target, sr.cvss_score,
               c.name as company_name, s.target_domain, s.scan_datetime
        FROM scan_results sr
        JOIN scans s ON sr.scan_id = s.id
        JOIN companies c ON s.company_id = c.id
        ORDER BY sr.cvss_score DESC, sr.severity DESC
        LIMIT 20
    """)
    results = cursor.fetchall()
    
    if not results:
        print("  No scan results found")
        return
    
    for result in results:
        severity_color = {
            'Critical': '🔴',
            'High': '🟠',
            'Medium': '🟡',
            'Low': '🟢',
            'Info': '🔵'
        }.get(result['severity'], '⚪')
        
        cvss_badge = ""
        if result['cvss_score'] >= 9.0:
            cvss_badge = "🔥"
        elif result['cvss_score'] >= 7.0:
            cvss_badge = "⚠️"
        elif result['cvss_score'] >= 4.0:
            cvss_badge = "⚡"
        
        print(f"  ID: {result['id']:<3} | {severity_color} {result['severity']:<9} | "
              f"CVSS: {result['cvss_score']:.1f}{cvss_badge:<2} | "
              f"Template: {result['template_name']:<35} | "
              f"Target: {result['target']:<40}")
        
        # Print additional details for first 5 results
        if result['id'] <= 5:
            print(f"    Company: {result['company_name']}")
            print(f"    Domain: {result['target_domain']}")
            print(f"    Scan Time: {result['scan_datetime']}")
            print("    " + "-" * 50)

def print_statistics(cursor):
    """Print statistics."""
    print("\n📈 STATISTICS")
    print("-" * 50)
    
    # Total scans per company
    cursor.execute("""
        SELECT c.name, COUNT(s.id) as scan_count
        FROM companies c
        LEFT JOIN scans s ON c.id = s.company_id
        GROUP BY c.id, c.name
        ORDER BY scan_count DESC
    """)
    scan_stats = cursor.fetchall()
    
    print("📊 Total Scans per Company:")
    for stat in scan_stats:
        print(f"  {stat['name']:<20} : {stat['scan_count']} scans")
    
    # Vulnerability statistics
    cursor.execute("""
        SELECT severity, COUNT(*) as count
        FROM scan_results
        GROUP BY severity
        ORDER BY 
            CASE severity
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                WHEN 'Low' THEN 4
                WHEN 'Info' THEN 5
                ELSE 6
            END
    """)
    vuln_stats = cursor.fetchall()
    
    print("\n🚨 Vulnerability Statistics:")
    severity_emoji = {
        'Critical': '🔴',
        'High': '🟠',
        'Medium': '🟡',
        'Low': '🟢',
        'Info': '🔵'
    }
    
    for stat in vuln_stats:
        emoji = severity_emoji.get(stat['severity'], '⚪')
        print(f"  {emoji} {stat['severity']:<9} : {stat['count']} vulnerabilities")
    
    # Top vulnerabilities
    cursor.execute("""
        SELECT sr.template_name, sr.severity, COUNT(*) as count, AVG(sr.cvss_score) as avg_cvss
        FROM scan_results sr
        GROUP BY sr.template_name, sr.severity
        ORDER BY count DESC, avg_cvss DESC
        LIMIT 10
    """)
    top_vulns = cursor.fetchall()
    
    print("\n🔥 Top 10 Most Common Vulnerabilities:")
    for i, vuln in enumerate(top_vulns, 1):
        emoji = severity_emoji.get(vuln['severity'], '⚪')
        print(f"  {i:2d}. {emoji} {vuln['template_name']:<40} "
              f"({vuln['severity']}) - Count: {vuln['count']}, Avg CVSS: {vuln['avg_cvss']:.1f}")

def print_recent_activity(cursor):
    """Print recent scan activity."""
    print("\n🕐 RECENT ACTIVITY")
    print("-" * 60)
    
    cursor.execute("""
        SELECT c.name as company_name, s.target_domain, s.status, s.scan_datetime,
               COUNT(sr.id) as vuln_count
        FROM scans s
        JOIN companies c ON s.company_id = c.id
        LEFT JOIN scan_results sr ON s.id = sr.scan_id
        GROUP BY s.id, c.name, s.target_domain, s.status, s.scan_datetime
        ORDER BY s.scan_datetime DESC
        LIMIT 10
    """)
    recent = cursor.fetchall()
    
    for activity in recent:
        status_icon = {
            'completed': '✅',
            'running': '🔄',
            'failed': '❌',
            'initializing': '⏳'
        }.get(activity['status'], '❓')
        
        print(f"  {activity['scan_datetime']} | {status_icon} {activity['status']:<12} | "
              f"{activity['company_name']:<15} | {activity['target_domain']:<25} | "
              f"Vulns: {activity['vuln_count']}")

def print_database_info(cursor):
    """Print database information."""
    print("\n🗄️ DATABASE INFORMATION")
    print("-" * 50)
    
    # Table counts
    tables = ['companies', 'scans', 'scan_results']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        count = cursor.fetchone()['count']
        print(f"  {table:<15} : {count} records")
    
    # Database size (if available)
    try:
        cursor.execute("SELECT table_name, ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'MB' 
                       FROM information_schema.tables 
                       WHERE table_schema = 'kamehameha_scanner' 
                       ORDER BY (data_length + index_length) DESC")
        sizes = cursor.fetchall()
        
        print("\n💾 Table Sizes:")
        for size in sizes:
            if size['MB'] > 0:
                print(f"  {size['table_name']:<20} : {size['MB']} MB")
    except:
        pass

def main():
    """Main function."""
    print("🔍 Kamehameha Vulnerability Scanner - Database Results Viewer")
    print("=" * 65)
    
    connection = get_db_connection()
    if not connection:
        print("❌ Failed to connect to database")
        print("   Make sure MySQL is running and credentials are correct")
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Print database info
        print_database_info(cursor)
        
        # Print companies
        print_companies(cursor)
        
        # Print scans
        print_scans(cursor)
        
        # Print scan results (limited)
        print_scan_results(cursor)
        
        # Print statistics
        print_statistics(cursor)
        
        # Print recent activity
        print_recent_activity(cursor)
        
        print_header("QUERIES FOR MANUAL EXECUTION")
        print("You can run these queries manually in MySQL:")
        print()
        print("-- View all scan results:")
        print("SELECT * FROM scan_results;")
        print()
        print("-- View results by severity:")
        print("SELECT severity, COUNT(*) FROM scan_results GROUP BY severity;")
        print()
        print("-- View top critical vulnerabilities:")
        print("SELECT * FROM scan_results WHERE severity = 'Critical' ORDER BY cvss_score DESC;")
        print()
        print("-- View scan history:")
        print("SELECT c.name, s.target_domain, s.scan_datetime, s.status FROM scans s JOIN companies c ON s.company_id = c.id;")
        
        cursor.close()
        connection.close()
        
        print_header("✅ SUCCESS")
        print("Database results loaded successfully!")
        print("You can now analyze the vulnerability scan results.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if connection:
            connection.close()

if __name__ == "__main__":
    main()
