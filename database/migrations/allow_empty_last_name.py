"""
Database migration to allow empty last names in Employee table
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from database.connection import engine
import logging

logger = logging.getLogger(__name__)

def allow_empty_last_name():
    """
    Update the employee table to allow NULL/empty last names
    """
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                logger.info("Updating employee table to allow empty last names...")
                
                # SQLite doesn't support ALTER COLUMN directly, so we need to recreate the table
                # First, create a new table with the updated schema
                create_new_table_sql = """
                CREATE TABLE employees_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id VARCHAR(50),
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100),
                    email VARCHAR(200) NOT NULL,
                    reporting_manager VARCHAR(100),
                    manager_email VARCHAR(200),
                    department VARCHAR(100),
                    employee_type VARCHAR(50),
                    status VARCHAR(50) DEFAULT 'active',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
                
                conn.execute(text(create_new_table_sql))
                
                # Copy existing data from old table to new table
                try:
                    # Check if old table exists and has data
                    result = conn.execute(text("SELECT COUNT(*) FROM employees"))
                    count = result.fetchone()[0]
                    
                    if count > 0:
                        logger.info(f"Copying {count} existing records...")
                        
                        copy_sql = """
                        INSERT INTO employees_temp (
                            id, employee_id, first_name, last_name, email, 
                            reporting_manager, manager_email, department, employee_type, status,
                            created_at, updated_at
                        )
                        SELECT 
                            id, employee_id, first_name, 
                            CASE 
                                WHEN last_name IS NULL OR last_name = '' THEN NULL
                                ELSE last_name 
                            END as last_name,
                            email, reporting_manager, manager_email, department, employee_type, status,
                            created_at, updated_at
                        FROM employees
                        """
                        
                        conn.execute(text(copy_sql))
                        logger.info("Data copied successfully")
                    else:
                        logger.info("No existing data to copy")
                        
                except Exception as e:
                    logger.warning(f"Could not copy data from old table: {str(e)}")
                
                # Drop old table and rename new table
                conn.execute(text("DROP TABLE IF EXISTS employees"))
                conn.execute(text("ALTER TABLE employees_temp RENAME TO employees"))
                
                # Recreate indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_employee_id ON employees(employee_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_email ON employees(email)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_department ON employees(department)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_employee_type ON employees(employee_type)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_status ON employees(status)"))
                
                # Commit the transaction
                trans.commit()
                logger.info("Employee table updated successfully to allow empty last names")
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Error during migration: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Failed to update employee table: {str(e)}")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the migration
    success = allow_empty_last_name()
    if success:
        print("✅ Employee table updated successfully to allow empty last names")
    else:
        print("❌ Employee table update failed")
        exit(1)
