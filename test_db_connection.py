#!/usr/bin/env python3
import sys
import os
sys.path.append('backend')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from db import get_db_connection
from config import get_config

def test_database_connection():
    print("🔍 Testing database connection...")
    
    try:
        # Test configuration
        config = get_config()
        print(f"✅ Configuration loaded: {config.__class__.__name__}")
        print(f"📊 Database: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
        
        # Test database connection
        connection = get_db_connection()
        if connection is None:
            print("❌ Failed to connect to database")
            return False
        
        print("✅ Database connection successful")
        
        # Test basic operations
        cursor = connection.cursor(dictionary=True)
        
        # Test companies table
        cursor.execute("SELECT COUNT(*) as count FROM companies")
        companies_count = cursor.fetchone()['count']
        print(f"📈 Companies in database: {companies_count}")
        
        # Test scans table
        cursor.execute("SELECT COUNT(*) as count FROM scans")
        scans_count = cursor.fetchone()['count']
        print(f"📈 Scans in database: {scans_count}")
        
        # Test scan_results table
        cursor.execute("SELECT COUNT(*) as count FROM scan_results")
        results_count = cursor.fetchone()['count']
        print(f"📈 Scan results in database: {results_count}")
        
        cursor.close()
        connection.close()
        
        print("✅ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
