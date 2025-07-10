#!/usr/bin/env python3
"""
Test script to verify Google Sheets integration
"""

import pandas as pd
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.integrations.google_sheets import google_sheets_integration

def test_google_sheets_connection():
    """Test the Google Sheets connection and data fetching"""
    print("🔗 Testing Google Sheets Integration...")
    print("=" * 50)
    
    try:
        # Test 1: Fetch raw data
        print("1. Fetching raw data from Google Sheets...")
        df = google_sheets_integration.fetch_employee_data()
        
        if df is not None:
            print(f"   ✅ Successfully fetched {len(df)} rows")
            print(f"   📊 Columns: {list(df.columns)}")
            print("\n   📋 First few rows:")
            print(df.head().to_string())
        else:
            print("   ❌ Failed to fetch data")
            return False
        
        # Test 2: Process the data
        print("\n2. Processing employee data...")
        processed_data = google_sheets_integration.process_employee_data(df)
        
        if processed_data:
            print(f"   ✅ Successfully processed {len(processed_data)} employee records")
            
            # Show sample processed record
            if processed_data:
                print("\n   📋 Sample processed record:")
                sample = processed_data[0]
                for key, value in sample.items():
                    print(f"      {key}: {value}")
                
                # Show employee type distribution
                type_counts = {}
                for emp in processed_data:
                    emp_type = emp.get('employee_type', 'unknown')
                    type_counts[emp_type] = type_counts.get(emp_type, 0) + 1
                
                print(f"\n   📊 Employee Type Distribution:")
                for emp_type, count in type_counts.items():
                    print(f"      {emp_type}: {count}")
                
                # Show status distribution
                status_counts = {}
                for emp in processed_data:
                    status = emp.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                print(f"\n   📊 Status Distribution:")
                for status, count in status_counts.items():
                    print(f"      {status}: {count}")
        else:
            print("   ❌ Failed to process data")
            return False
        
        # Test 3: Full sync test (without database)
        print("\n3. Testing full sync process...")
        result = google_sheets_integration.full_sync()
        
        if result['success']:
            print(f"   ✅ Full sync successful: {result['message']}")
            print(f"   📊 Stats: {result['stats']}")
        else:
            print(f"   ⚠️ Full sync completed with issues: {result['message']}")
        
        print("\n" + "=" * 50)
        print("🎉 Google Sheets integration test completed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_google_sheets_connection()
    sys.exit(0 if success else 1)
