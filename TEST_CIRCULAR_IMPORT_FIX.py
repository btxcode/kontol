#!/usr/bin/env python3
"""
Test script to verify circular import fix
"""

import sys
import os

def test_circular_import_fix():
    """Test that the circular import issue has been resolved."""
    print("🔍 Testing circular import fix...")
    
    # Change to backend directory
    original_dir = os.getcwd()
    backend_dir = os.path.join(original_dir, 'backend')
    
    if not os.path.exists(backend_dir):
        print(f"❌ Backend directory not found: {backend_dir}")
        return False
    
    os.chdir(backend_dir)
    
    try:
        print("📁 Changed to backend directory")
        
        # Test 1: Import scanner module
        print("\n1️⃣ Testing scanner module import...")
        try:
            import scanner
            print("✅ Scanner module imported successfully")
            
            # Test scanner functions
            if hasattr(scanner, 'run_and_process_scan'):
                print("✅ run_and_process_scan function available")
            else:
                print("❌ run_and_process_scan function not found")
                return False
                
            if hasattr(scanner, 'get_active_scans'):
                print("✅ get_active_scans function available")
            else:
                print("❌ get_active_scans function not found")
                return False
                
            if hasattr(scanner, 'active_scans'):
                print("✅ active_scans variable available")
            else:
                print("❌ active_scans variable not found")
                return False
                
        except Exception as e:
            print(f"❌ Failed to import scanner module: {e}")
            return False
        
        # Test 2: Import app module
        print("\n2️⃣ Testing app module import...")
        try:
            import app
            print("✅ App module imported successfully")
            
            # Test app functions
            if hasattr(app, 'start_scan'):
                print("✅ start_scan function available")
            else:
                print("❌ start_scan function not found")
                return False
                
            if hasattr(app, 'get_companies'):
                print("✅ get_companies function available")
            else:
                print("❌ get_companies function not found")
                return False
                
        except Exception as e:
            print(f"❌ Failed to import app module: {e}")
            return False
        
        # Test 3: Test shared active_scans
        print("\n3️⃣ Testing shared active_scans...")
        try:
            # Get active_scans from scanner
            scanner_active_scans = scanner.get_active_scans()
            print(f"✅ Got active_scans from scanner: {type(scanner_active_scans)}")
            
            # Get active_scans from app
            app_active_scans = app.active_scans
            print(f"✅ Got active_scans from app: {type(app_active_scans)}")
            
            # They should be the same object
            if scanner_active_scans is app_active_scans:
                print("✅ Both modules share the same active_scans object")
            else:
                print("❌ Modules have different active_scans objects")
                return False
                
        except Exception as e:
            print(f"❌ Failed to test shared active_scans: {e}")
            return False
        
        # Test 4: Test Flask app creation
        print("\n4️⃣ Testing Flask app creation...")
        try:
            if hasattr(app, 'app'):
                flask_app = app.app
                print(f"✅ Flask app created: {flask_app}")
                print(f"✅ Flask app name: {flask_app.import_name}")
            else:
                print("❌ Flask app not found")
                return False
                
        except Exception as e:
            print(f"❌ Failed to test Flask app: {e}")
            return False
        
        # Test 5: Test database connection
        print("\n5️⃣ Testing database connection...")
        try:
            from db import get_db_connection
            connection = get_db_connection()
            if connection:
                print("✅ Database connection successful")
                connection.close()
            else:
                print("⚠️  Database connection failed (this might be expected if DB is not running)")
                
        except Exception as e:
            print(f"❌ Failed to test database connection: {e}")
            return False
        
        # Test 6: Test configuration
        print("\n6️⃣ Testing configuration...")
        try:
            from config import get_config
            config = get_config()
            print(f"✅ Configuration loaded: {config.__class__.__name__}")
            print(f"✅ Database host: {config.DB_HOST}")
            print(f"✅ Database name: {config.DB_NAME}")
            
        except Exception as e:
            print(f"❌ Failed to test configuration: {e}")
            return False
        
        print("\n🎉 All circular import tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        return False
        
    finally:
        # Change back to original directory
        os.chdir(original_dir)

def test_flask_app_startup():
    """Test that the Flask app can start without errors."""
    print("\n🚀 Testing Flask app startup...")
    
    # Change to backend directory
    original_dir = os.getcwd()
    backend_dir = os.path.join(original_dir, 'backend')
    os.chdir(backend_dir)
    
    try:
        # Import and create app
        import app
        
        # Test app routes
        routes = []
        for rule in app.app.url_map.iter_rules():
            routes.append(f"{rule.methods} {rule.rule}")
        
        print(f"✅ Flask app has {len(routes)} routes:")
        for route in routes[:5]:  # Show first 5 routes
            print(f"   {route}")
        if len(routes) > 5:
            print(f"   ... and {len(routes) - 5} more routes")
        
        # Test health endpoint
        with app.app.test_client() as client:
            response = client.get('/apiv1/health')
            if response.status_code == 200:
                print("✅ Health endpoint responding")
                health_data = response.get_json()
                print(f"   Status: {health_data.get('status')}")
                print(f"   Active scans: {health_data.get('active_scans')}")
            else:
                print(f"❌ Health endpoint returned status {response.status_code}")
                return False
        
        print("✅ Flask app startup test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Flask app startup test failed: {e}")
        return False
        
    finally:
        os.chdir(original_dir)

def main():
    """Main test function."""
    print("🧪 Kamehameha Vulnerability Scanner - Circular Import Fix Test")
    print("=" * 60)
    
    # Test circular import fix
    circular_import_ok = test_circular_import_fix()
    
    if circular_import_ok:
        # Test Flask app startup
        flask_startup_ok = test_flask_app_startup()
        
        if flask_startup_ok:
            print("\n🎉 ALL TESTS PASSED!")
            print("\n📋 Summary:")
            print("✅ Circular import issue resolved")
            print("✅ Scanner module working correctly")
            print("✅ App module working correctly")
            print("✅ Shared active_scans working")
            print("✅ Flask app starting correctly")
            print("✅ API endpoints responding")
            
            print("\n🚀 Ready to run the application!")
            print("   Use: cd backend && python app.py")
            
            return True
        else:
            print("\n❌ Flask app startup test failed")
            return False
    else:
        print("\n❌ Circular import fix test failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)