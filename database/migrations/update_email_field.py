"""
Database migration to update Employee model from email_personal to email
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from database.connection import engine
import logging

logger = logging.getLogger(__name__)

def migrate_email_field():
    """
    Migrate the employee table to use email instead of email_personal
    """
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                # Check if the table exists and has the old structure
                result = conn.execute(text("PRAGMA table_info(employees)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'email_personal' in columns and 'email' not in columns:
                    logger.info("Migrating employee table from email_personal to email...")
                    
                    # Add new email column
                    conn.execute(text("ALTER TABLE employees ADD COLUMN email VARCHAR(200)"))
                    
                    # Copy data from email_personal to email
                    conn.execute(text("UPDATE employees SET email = email_personal WHERE email_personal IS NOT NULL"))
                    
                    # Note: SQLite doesn't support dropping columns easily
                    # We'll keep email_personal for now and remove it in a future migration
                    
                    logger.info("Successfully migrated email field")
                    
                elif 'email' in columns:
                    logger.info("Employee table already has the email field")
                    
                else:
                    logger.info("Creating email field in employee table...")
                    conn.execute(text("ALTER TABLE employees ADD COLUMN email VARCHAR(200)"))
                
                # Commit the transaction
                trans.commit()
                logger.info("Email field migration completed successfully")
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Error during migration: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Failed to migrate email field: {str(e)}")
        return False

def rollback_email_field():
    """
    Rollback the migration (remove email column)
    """
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Check if email column exists
                result = conn.execute(text("PRAGMA table_info(employees)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'email' in columns:
                    logger.info("Rolling back email field migration...")
                    
                    # SQLite doesn't support DROP COLUMN, so we'd need to recreate the table
                    # For now, we'll just log that rollback is not fully supported
                    logger.warning("SQLite doesn't support DROP COLUMN. Manual intervention required for full rollback.")
                    
                trans.commit()
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Error during rollback: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Failed to rollback email field: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the migration
    success = migrate_email_field()
    if success:
        print("✅ Email field migration completed successfully")
    else:
        print("❌ Email field migration failed")
        exit(1)
