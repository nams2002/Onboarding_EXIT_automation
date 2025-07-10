#!/usr/bin/env python3
"""
Check what's actually in the database
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_session
from database.models import Employee

def check_database():
    """Check what employees are actually in the database"""
    try:
        with get_db_session() as session:
            # Count total employees
            total_count = session.query(Employee).count()
            print(f"📊 Total employees in database: {total_count}")
            
            if total_count > 0:
                # Show first 10 employees
                employees = session.query(Employee).limit(10).all()
                print(f"\n📋 First 10 employees:")
                for emp in employees:
                    print(f"   - {emp.full_name} ({emp.email}) - {emp.department} - {emp.employee_type}")
                
                # Count by employee type
                full_time = session.query(Employee).filter_by(employee_type='full_time').count()
                intern = session.query(Employee).filter_by(employee_type='intern').count()
                contractor = session.query(Employee).filter_by(employee_type='contractor').count()
                
                print(f"\n📊 Employee Type Distribution:")
                print(f"   Full-time: {full_time}")
                print(f"   Interns: {intern}")
                print(f"   Contractors: {contractor}")
                
                # Count by department
                departments = session.query(Employee.department).distinct().all()
                print(f"\n🏢 Departments:")
                for dept in departments:
                    if dept[0]:
                        count = session.query(Employee).filter_by(department=dept[0]).count()
                        print(f"   {dept[0]}: {count}")
                
                # Check for employees with missing last names
                missing_last_name = session.query(Employee).filter(
                    (Employee.last_name == None) | (Employee.last_name == '')
                ).count()
                print(f"\n⚠️ Employees with missing last names: {missing_last_name}")
                
                if missing_last_name > 0:
                    missing_employees = session.query(Employee).filter(
                        (Employee.last_name == None) | (Employee.last_name == '')
                    ).all()
                    print("   Missing last name employees:")
                    for emp in missing_employees:
                        print(f"     - {emp.first_name} ({emp.email})")
            
            return True
            
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Checking Database Contents...")
    print("=" * 50)
    success = check_database()
    print("=" * 50)
    if success:
        print("✅ Database check completed")
    else:
        print("❌ Database check failed")
