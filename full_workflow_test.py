#!/usr/bin/env python3
import requests
import time
import json
import sys

BASE_URL = "http://localhost:5000"

def test_full_workflow():
    print("🚀 Starting full workflow test...")
    
    # Test 1: Health check
    print("\n1️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/apiv1/health")
        if response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Get companies
    print("\n2️⃣ Testing get companies...")
    try:
        response = requests.get(f"{BASE_URL}/apiv1/companies")
        if response.status_code == 200:
            companies = response.json()
            print(f"✅ Companies retrieved: {len(companies['data'])} companies")
        else:
            print(f"❌ Get companies failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get companies error: {e}")
        return False
    
    # Test 3: Start scan
    print("\n3️⃣ Testing scan initiation...")
    scan_data = {
        "domain": "testphp.vulnweb.com",
        "company": "TestCompany"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/apiv1/scan",
            headers={"Content-Type": "application/json"},
            json=scan_data
        )
        
        if response.status_code == 202:
            scan_result = response.json()
            scan_id = scan_result['scan_id']
            print(f"✅ Scan initiated: ID {scan_id}")
        else:
            print(f"❌ Scan initiation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Scan initiation error: {e}")
        return False
    
    # Test 4: Monitor scan progress
    print("\n4️⃣ Monitoring scan progress...")
    max_wait_time = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{BASE_URL}/apiv1/scans/{scan_id}/status")
            if response.status_code == 200:
                status_data = response.json()
                status = status_data['status']
                progress = status_data['progress']
                
                print(f"📊 Status: {status}, Progress: {progress}%")
                
                if status == 'completed':
                    print("✅ Scan completed successfully!")
                    break
                elif status == 'failed':
                    print("❌ Scan failed!")
                    return False
                else:
                    time.sleep(10)  # Wait 10 seconds before checking again
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return False
    
    if time.time() - start_time >= max_wait_time:
        print("❌ Scan timed out!")
        return False
    
    # Test 5: Verify results
    print("\n5️⃣ Verifying scan results...")
    
    # Wait a bit for results to be processed
    time.sleep(5)
    
    # Get companies again to check scan count
    try:
        response = requests.get(f"{BASE_URL}/apiv1/companies")
        if response.status_code == 200:
            companies = response.json()
            test_company = None
            
            for company in companies['data']:
                if company['name'] == 'TestCompany':
                    test_company = company
                    break
            
            if test_company and test_company['total_scans'] > 0:
                print(f"✅ Scan count updated: {test_company['total_scans']} scans")
            else:
                print("❌ Scan count not updated")
                return False
        else:
            print(f"❌ Get companies failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get companies error: {e}")
        return False
    
    # Test 6: Check dates and times
    print("\n6️⃣ Testing dates and times...")
    try:
        # Get dates
        response = requests.get(f"{BASE_URL}/apiv1/TestCompany/dates")
        if response.status_code == 200:
            dates = response.json()
            if len(dates['data']) > 0:
                print(f"✅ Dates found: {len(dates['data'])} dates")
                latest_date = dates['data'][0]
                
                # Get times
                response = requests.get(f"{BASE_URL}/apiv1/TestCompany/{latest_date}/times")
                if response.status_code == 200:
                    times = response.json()
                    if len(times['data']) > 0:
                        print(f"✅ Times found: {len(times['data'])} times")
                        latest_time = times['data'][0]
                        
                        # Get results
                        response = requests.get(f"{BASE_URL}/apiv1/TestCompany/{latest_date}/{latest_time}/results")
                        if response.status_code == 200:
                            results = response.json()
                            print(f"✅ Results found: {len(results['data'])} vulnerabilities")
                            print(f"📊 Statistics: {results['statistics']}")
                        else:
                            print(f"❌ Get results failed: {response.status_code}")
                            return False
                    else:
                        print("❌ No times found")
                        return False
                else:
                    print(f"❌ Get times failed: {response.status_code}")
                    return False
            else:
                print("❌ No dates found")
                return False
        else:
            print(f"❌ Get dates failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dates/Times error: {e}")
        return False
    
    print("\n🎉 Full workflow test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_full_workflow()
    sys.exit(0 if success else 1)
