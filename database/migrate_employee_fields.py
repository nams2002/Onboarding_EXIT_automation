#!/usr/bin/env python3
"""
Migration script to add new fields to Employee table for comprehensive onboarding
"""

import sqlite3
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_employee_table():
    """Add new fields to Employee table"""
    
    # Database path
    db_path = Path(__file__).parent / "hr_system.db"
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # List of new columns to add
        new_columns = [
            ("email_personal", "VARCHAR(200)"),
            ("phone", "VARCHAR(20)"),
            ("address", "TEXT"),
            ("designation", "VARCHAR(100)"),
            ("date_of_joining", "DATE"),
            ("work_location", "VARCHAR(50)"),
            ("notice_period", "INTEGER"),
            ("ctc", "FLOAT"),
            ("stipend", "FLOAT"),
            ("hourly_rate", "FLOAT"),
            ("probation_period", "INTEGER"),
            ("internship_duration", "INTEGER"),
            ("contract_duration", "INTEGER"),
            ("benefits", "TEXT"),
            ("emergency_contact_name", "VARCHAR(100)"),
            ("emergency_contact_phone", "VARCHAR(20)"),
            ("blood_group", "VARCHAR(10)"),
            ("special_requirements", "TEXT")
        ]
        
        # Check which columns already exist
        cursor.execute("PRAGMA table_info(employees)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # Add new columns that don't exist
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE employees ADD COLUMN {column_name} {column_type}"
                    cursor.execute(alter_sql)
                    logger.info(f"Added column: {column_name}")
                except sqlite3.Error as e:
                    logger.warning(f"Could not add column {column_name}: {e}")
            else:
                logger.info(f"Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_employee_table()
