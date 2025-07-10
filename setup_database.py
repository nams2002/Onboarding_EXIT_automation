#!/usr/bin/env python3
"""
Database setup script for HR Automation System
This script initializes the SQLite database and creates all necessary tables.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import init_database, test_connection, seed_initial_data
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to set up the database"""
    print("🚀 Setting up HR Automation Database...")
    print("=" * 50)
    
    # Test database connection
    print("1. Testing database connection...")
    if test_connection():
        print("   ✅ Database connection successful")
    else:
        print("   ❌ Database connection failed")
        return False
    
    # Initialize database tables
    print("\n2. Creating database tables...")
    if init_database():
        print("   ✅ Database tables created successfully")
    else:
        print("   ❌ Failed to create database tables")
        return False
    
    # Seed initial data
    print("\n3. Seeding initial data...")
    if seed_initial_data():
        print("   ✅ Initial data seeded successfully")
    else:
        print("   ❌ Failed to seed initial data")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Database setup completed successfully!")
    print("\nYou can now run the application with:")
    print("   streamlit run app.py")
    print("\nDefault login credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
