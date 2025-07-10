"""
Database migration to recreate Employee table to match Google Sheets structure exactly
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text, create_engine
from database.connection import engine
import logging

logger = logging.getLogger(__name__)

def recreate_employee_table():
    """
    Recreate the employee table to match Google Sheets structure exactly
    """
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                logger.info("Recreating employee table to match Google Sheets structure...")
                
                # Drop existing table if it exists
                conn.execute(text("DROP TABLE IF EXISTS employees_new"))
                
                # Create new table with exact Google Sheets structure
                create_table_sql = """
                CREATE TABLE employees_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id VARCHAR(50),
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100) NOT NULL,
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
                
                conn.execute(text(create_table_sql))
                
                # Copy existing data if old table exists
                try:
                    # Check if old table exists
                    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'"))
                    if result.fetchone():
                        logger.info("Copying existing data from old employees table...")
                        
                        # Copy data from old table to new table
                        copy_sql = """
                        INSERT INTO employees_new (
                            employee_id, first_name, last_name, email, 
                            reporting_manager, department, employee_type, status
                        )
                        SELECT 
                            employee_id, 
                            COALESCE(first_name, SUBSTR(full_name, 1, INSTR(full_name || ' ', ' ') - 1)) as first_name,
                            COALESCE(last_name, SUBSTR(full_name, INSTR(full_name || ' ', ' ') + 1)) as last_name,
                            COALESCE(email, email_personal) as email,
                            reporting_manager,
                            department,
                            CASE 
                                WHEN employee_type = 'FULL_TIME' THEN 'full_time'
                                WHEN employee_type = 'INTERN' THEN 'intern'
                                WHEN employee_type = 'CONTRACTOR' THEN 'contractor'
                                ELSE 'full_time'
                            END as employee_type,
                            CASE 
                                WHEN status = 'ACTIVE' THEN 'active'
                                WHEN status = 'ONBOARDING' THEN 'onboarding'
                                WHEN status = 'OFFBOARDING' THEN 'offboarding'
                                WHEN status = 'INACTIVE' THEN 'inactive'
                                ELSE 'active'
                            END as status
                        FROM employees
                        WHERE first_name IS NOT NULL OR full_name IS NOT NULL
                        """
                        
                        conn.execute(text(copy_sql))
                        logger.info("Data copied successfully")
                        
                        # Drop old table and rename new table
                        conn.execute(text("DROP TABLE employees"))
                        
                except Exception as e:
                    logger.warning(f"Could not copy data from old table: {str(e)}")
                
                # Rename new table to employees
                conn.execute(text("ALTER TABLE employees_new RENAME TO employees"))
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_employee_id ON employees(employee_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_email ON employees(email)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_department ON employees(department)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_employee_type ON employees(employee_type)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_status ON employees(status)"))
                
                # Commit the transaction
                trans.commit()
                logger.info("Employee table recreated successfully")
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Error during table recreation: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Failed to recreate employee table: {str(e)}")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the migration
    success = recreate_employee_table()
    if success:
        print("✅ Employee table recreated successfully")
    else:
        print("❌ Employee table recreation failed")
        exit(1)
