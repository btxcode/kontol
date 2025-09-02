import os
import threading
import logging
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from scanner import run_and_process_scan
from config import get_config
from db import get_db_connection

app = Flask(__name__, static_folder='../frontend')
CORS(app)

config = get_config()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global dictionary to track active scans
active_scans = {}

# Serve frontend files
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/apiv1/scan', methods=['POST'])
def start_scan():
    data = request.json
    target_domain = data.get('domain')
    company_name = data.get('company')
    
    if not target_domain or not company_name:
        return jsonify({'error': 'Domain and company fields are required'}), 400
    
    # Generate a unique scan ID
    scan_id = int(time.time() * 1000)  # Use timestamp as scan ID
    
    # Add to active scans
    active_scans[scan_id] = {
        'company_name': company_name,
        'target_domain': target_domain,
        'status': 'initializing',
        'progress': 0,
        'start_time': datetime.now()
    }
    
    # Run the scan in a background thread
    thread = threading.Thread(
        target=run_and_process_scan,
        args=(target_domain, company_name, scan_id)
    )
    thread.start()
    
    return jsonify({
        'scan_id': scan_id,
        'message': 'Scan initiated successfully'
    }), 202

@app.route('/apiv1/scans/<int:scan_id>/status', methods=['GET'])
def get_scan_status(scan_id):
    if scan_id not in active_scans:
        return jsonify({'error': 'Scan not found'}), 404
    
    scan_info = active_scans[scan_id]
    return jsonify({
        'scan_id': scan_id,
        'status': scan_info['status'],
        'progress': scan_info.get('progress', 0),
        'company_name': scan_info['company_name'],
        'target_domain': scan_info['target_domain'],
        'start_time': scan_info['start_time'].isoformat()
    })

@app.route('/apiv1/companies', methods=['GET'])
def get_companies():
    connection = get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get all companies
        cursor.execute("SELECT id, name, created_at FROM companies ORDER BY name")
        companies_data = cursor.fetchall()
        
        companies = []
        for company in companies_data:
            company_id = company['id']
            company_name = company['name']
            
            # Get scan summary for this company
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_scans,
                    MAX(scan_datetime) as last_scan_date,
                    MAX(scan_datetime) as last_scan_time
                FROM scans 
                WHERE company_id = %s
            """, (company_id,))
            scan_summary = cursor.fetchone()
            
            # Get total vulnerabilities count by severity
            cursor.execute("""
                SELECT severity, COUNT(*) AS count
                FROM scan_results sr
                JOIN scans s ON sr.scan_id = s.id
                WHERE s.company_id = %s
                GROUP BY severity
            """, (company_id,))
            vuln_counts = cursor.fetchall()
            
            total_vulnerabilities = {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0
            }
            
            for vuln in vuln_counts:
                severity = vuln['severity'].lower()
                if severity in total_vulnerabilities:
                    total_vulnerabilities[severity] = vuln['count']
            
            # Add scan progress info from active_scans
            progress_info = {
                'status': 'idle',
                'progress': None
            }
            
            for scan_id, scan_data in active_scans.items():
                if scan_data.get('company_name') == company_name and scan_data.get('status') != 'completed':
                    progress_info['status'] = scan_data.get('status')
                    progress_info['progress'] = scan_data.get('progress')
                    break
            
            companies.append({
                'id': company_id,
                'name': company_name,
                'total_scans': scan_summary['total_scans'] or 0,
                'last_scan': {
                    'date': scan_summary['last_scan_date'].strftime('%d/%m/%Y') if scan_summary['last_scan_date'] else None,
                    'time': scan_summary['last_scan_time'].strftime('%H:%M') if scan_summary['last_scan_time'] else None
                },
                'total_vulnerabilities': total_vulnerabilities,
                'scan_progress': progress_info
            })
        
        cursor.close()
        connection.close()
        return jsonify({'data': companies})
    
    except Exception as e:
        logger.error(f"Error in get_companies: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/apiv1/<company>/dates', methods=['GET'])
def get_dates(company):
    connection = get_db_connection()
    if connection is None:
        return jsonify({'data': []})
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id FROM companies WHERE name = %s", (company,))
        company_row = cursor.fetchone()
        
        if not company_row:
            return jsonify({'error': 'Company not found'}), 404
        
        company_id = company_row['id']
        cursor.execute("""
            SELECT DISTINCT DATE(scan_datetime) as scan_date 
            FROM scans
            WHERE company_id = %s
            ORDER BY scan_date DESC
        """, (company_id,))
        
        dates = []
        for row in cursor.fetchall():
            if row['scan_date']:
                dates.append(row['scan_date'].strftime('%Y%m%d'))
        
        cursor.close()
        connection.close()
        return jsonify({'data': dates})
    
    except Exception as e:
        logger.error(f"Error in get_dates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/apiv1/<company>/<date>/times', methods=['GET'])
def get_times(company, date):
    connection = get_db_connection()
    if connection is None:
        return jsonify({'data': []})
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id FROM companies WHERE name = %s", (company,))
        company_row = cursor.fetchone()
        
        if not company_row:
            return jsonify({'error': 'Company not found'}), 404
        
        company_id = company_row['id']
        
        # Convert date string YYYYMMDD to date object
        try:
            scan_date = datetime.strptime(date, '%Y%m%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        cursor.execute("""
            SELECT DISTINCT TIME(scan_datetime) as scan_time
            FROM scans
            WHERE company_id = %s AND DATE(scan_datetime) = %s
            ORDER BY scan_time DESC
        """, (company_id, scan_date))
        
        times = []
        for row in cursor.fetchall():
            if row['scan_time']:
                scan_time_str = row['scan_time'].strftime('%H%M')
                times.append(scan_time_str)
        
        cursor.close()
        connection.close()
        return jsonify({'data': times})
    
    except Exception as e:
        logger.error(f"Error in get_times: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/apiv1/<company>/<date>/<time>/results', methods=['GET'])
def get_results(company, date, time):
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            'data': [], 
            'statistics': { 
                'critical': 0, 
                'high': 0, 
                'medium': 0, 
                'low': 0, 
                'info': 0 
            }
        })
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id FROM companies WHERE name = %s", (company,))
        company_row = cursor.fetchone()
        
        if not company_row:
            return jsonify({'error': 'Company not found'}), 404
        
        company_id = company_row['id']
        
        # Parse date and time
        try:
            scan_date = datetime.strptime(date, '%Y%m%d').date()
            scan_time = datetime.strptime(time, '%H%M').time()
        except ValueError:
            return jsonify({'error': 'Invalid date or time format'}), 400
        
        # Find the scan
        cursor.execute("""
            SELECT id FROM scans
            WHERE company_id = %s 
            AND DATE(scan_datetime) = %s 
            AND TIME(scan_datetime) = %s
        """, (company_id, scan_date, scan_time))
        
        scan_row = cursor.fetchone()
        if not scan_row:
            return jsonify({'error': 'Scan not found'}), 404
        
        scan_id = scan_row['id']
        
        # Get scan results
        cursor.execute("""
            SELECT template_name, severity, protocol, target, details, cvss_score, recommendation
            FROM scan_results
            WHERE scan_id = %s
        """, (scan_id,))
        
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        
        processed_results = []
        statistics = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        for result in results:
            processed_results.append({
                'template_name': result['template_name'],
                'severity': result['severity'],
                'protocol': result['protocol'],
                'target': result['target'],
                'details': result['details'],
                'cvss_score': result['cvss_score'],
                'recommendation': result['recommendation']
            })
            
            severity = result['severity'].lower()
            if severity in statistics:
                statistics[severity] += 1
        
        return jsonify({
            'data': processed_results,
            'statistics': statistics
        })
    
    except Exception as e:
        logger.error(f"Error in get_results: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/apiv1/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'active_scans': len(active_scans)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)