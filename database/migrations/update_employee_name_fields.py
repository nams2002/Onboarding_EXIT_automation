"""
Database migration to update Employee model from full_name to first_name and last_name
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from database.connection import engine
import logging

logger = logging.getLogger(__name__)

def migrate_employee_name_fields():
    """
    Migrate the employee table to use first_name and last_name instead of full_name
    """
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                # Check if the table exists and has the old structure
                result = conn.execute(text("PRAGMA table_info(employees)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'full_name' in columns:
                    logger.info("Migrating employee table from full_name to first_name and last_name...")
                    
                    # Add new columns
                    conn.execute(text("ALTER TABLE employees ADD COLUMN first_name VARCHAR(100)"))
                    conn.execute(text("ALTER TABLE employees ADD COLUMN last_name VARCHAR(100)"))
                    
                    # Update existing records by splitting full_name
                    # Get all existing employees
                    employees = conn.execute(text("SELECT id, full_name FROM employees")).fetchall()
                    
                    for emp_id, full_name in employees:
                        if full_name:
                            # Split the full name
                            name_parts = full_name.strip().split()
                            if len(name_parts) >= 2:
                                first_name = name_parts[0]
                                last_name = ' '.join(name_parts[1:])
                            elif len(name_parts) == 1:
                                first_name = name_parts[0]
                                last_name = ''
                            else:
                                first_name = 'Unknown'
                                last_name = ''
                            
                            # Update the record
                            conn.execute(text(
                                "UPDATE employees SET first_name = :first_name, last_name = :last_name WHERE id = :id"
                            ), {
                                'first_name': first_name,
                                'last_name': last_name,
                                'id': emp_id
                            })
                    
                    # Make first_name NOT NULL after populating data
                    # Note: SQLite doesn't support ALTER COLUMN, so we'll handle this in the application
                    
                    logger.info(f"Successfully migrated {len(employees)} employee records")
                    
                    # Note: We're keeping the full_name column for now to avoid breaking existing code
                    # It can be removed in a future migration after all code is updated
                    
                else:
                    logger.info("Employee table already has the new structure (first_name, last_name)")
                
                # Commit the transaction
                trans.commit()
                logger.info("Migration completed successfully")
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Error during migration: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Failed to migrate employee name fields: {str(e)}")
        return False

def rollback_employee_name_fields():
    """
    Rollback the migration (remove first_name and last_name columns)
    """
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Check if new columns exist
                result = conn.execute(text("PRAGMA table_info(employees)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'first_name' in columns and 'last_name' in columns:
                    logger.info("Rolling back employee name field migration...")
                    
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
        logger.error(f"Failed to rollback employee name fields: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the migration
    success = migrate_employee_name_fields()
    if success:
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed")
        exit(1)
