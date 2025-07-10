"""
Google Sheets Integration Module
Handles reading and syncing employee data from Google Sheets
"""

import pandas as pd
import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import streamlit as st
from config import config

# Configure logging
logger = logging.getLogger(__name__)

class GoogleSheetsIntegration:
    """Google Sheets integration for employee data"""
    
    def __init__(self):
        """Initialize Google Sheets integration"""
        # Public CSV URL for your Google Sheets
        self.csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSXui5gr-rgxjtDTFeNSPe9i-OkyRoAUATO2hqp90ObBqaLMWNzpnA9QTwU3pASkv5TlTym_NfRqsDO/pub?output=csv"
        
        # Column mapping based on your actual Google Sheets structure
        self.column_mapping = {
            'Employee ID': 'employee_id',
            'First Name': 'first_name',
            'Last Name': 'last_name',
            'Email ID': 'email',  # Map to database field name
            'Reporting Manager': 'reporting_manager',
            'Manager Mail ID': 'manager_email',
            'Department': 'department',
            'Categories': 'employee_type'
        }
    
    def fetch_employee_data(self) -> Optional[pd.DataFrame]:
        """
        Fetch employee data from Google Sheets
        
        Returns:
            DataFrame with employee data or None if failed
        """
        try:
            logger.info(f"Fetching data from Google Sheets: {self.csv_url}")

            # Read CSV data from Google Sheets
            df = pd.read_csv(self.csv_url)

            logger.info(f"Successfully fetched {len(df)} rows from Google Sheets")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data from Google Sheets: {str(e)}")
            return None
    
    def process_employee_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Process and clean employee data from Google Sheets
        
        Args:
            df: Raw DataFrame from Google Sheets
            
        Returns:
            List of processed employee records
        """
        processed_employees = []
        
        try:
            # Clean column names (remove extra spaces, etc.)
            df.columns = df.columns.str.strip()
            
            for index, row in df.iterrows():
                try:
                    # Skip empty rows
                    first_name = row.get('First Name', '')
                    last_name = row.get('Last Name', '')
                    if pd.isna(first_name) or str(first_name).strip() == '':
                        continue

                    # Process each employee record
                    employee_data = {}

                    # Map columns to our database fields
                    for sheet_col, db_field in self.column_mapping.items():
                        if sheet_col in df.columns:
                            value = row.get(sheet_col, '')

                            # Clean and process the value
                            if pd.isna(value):
                                value = None
                            elif isinstance(value, str):
                                value = value.strip()
                                if value == '':
                                    value = None

                            employee_data[db_field] = value

                    # Ensure first_name and last_name are properly set
                    # Handle missing last names naturally - leave empty if not provided
                    if not employee_data.get('last_name') or employee_data.get('last_name') in [None, '', 'None']:
                        employee_data['last_name'] = ''

                    # Process specific fields
                    employee_data = self._process_special_fields(employee_data)

                    # Create full_name field
                    first_name = employee_data.get('first_name', '').strip()
                    last_name = employee_data.get('last_name', '').strip()
                    if first_name and last_name:
                        employee_data['full_name'] = f"{first_name} {last_name}"
                    elif first_name:
                        employee_data['full_name'] = first_name
                    else:
                        employee_data['full_name'] = 'Unknown'

                    # Add metadata
                    employee_data['data_source'] = 'google_sheets'
                    employee_data['last_synced'] = datetime.now()

                    processed_employees.append(employee_data)
                    
                except Exception as e:
                    logger.warning(f"Error processing row {index}: {str(e)}")
                    continue
            
            logger.info(f"Successfully processed {len(processed_employees)} employee records")
            return processed_employees
            
        except Exception as e:
            logger.error(f"Error processing employee data: {str(e)}")
            return []
    
    def _process_special_fields(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process special fields that need formatting or conversion
        
        Args:
            employee_data: Raw employee data dictionary
            
        Returns:
            Processed employee data dictionary
        """
        # Process date of joining
        if employee_data.get('date_of_joining'):
            try:
                # Try different date formats
                date_str = str(employee_data['date_of_joining'])
                for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                    try:
                        employee_data['date_of_joining'] = datetime.strptime(date_str, date_format).date()
                        break
                    except ValueError:
                        continue
                else:
                    # If no format matches, set to None
                    employee_data['date_of_joining'] = None
                    logger.warning(f"Could not parse date: {date_str}")
            except Exception as e:
                employee_data['date_of_joining'] = None
                logger.warning(f"Error processing date of joining: {str(e)}")
        
        # Process CTC (remove currency symbols, commas)
        if employee_data.get('ctc'):
            try:
                ctc_str = str(employee_data['ctc'])
                # Remove currency symbols and commas
                ctc_str = ctc_str.replace('₹', '').replace(',', '').replace('$', '').strip()
                if ctc_str and ctc_str.replace('.', '').isdigit():
                    employee_data['ctc'] = float(ctc_str)
                else:
                    employee_data['ctc'] = None
            except Exception as e:
                employee_data['ctc'] = None
                logger.warning(f"Error processing CTC: {str(e)}")
        
        # Process employee type from Categories column
        if employee_data.get('employee_type'):
            emp_type = str(employee_data['employee_type']).lower().strip()
            if 'intern' in emp_type:
                employee_data['employee_type'] = 'intern'
            elif 'contract' in emp_type:
                employee_data['employee_type'] = 'contractor'
            elif 'full' in emp_type or 'permanent' in emp_type:
                employee_data['employee_type'] = 'full_time'
            else:
                employee_data['employee_type'] = 'full_time'  # Default
        else:
            employee_data['employee_type'] = 'full_time'  # Default

        # Set default status as active (since no status column in your sheet)
        employee_data['status'] = 'active'
        
        # Generate employee ID if not present
        if not employee_data.get('employee_id'):
            # Generate a simple ID based on name
            first_name = employee_data.get('first_name', '')
            last_name = employee_data.get('last_name', '')
            if first_name and last_name:
                # Take first letter of first name and last name
                initials = first_name[0] + last_name[0]
                employee_data['employee_id'] = f"RI{initials.upper()}{datetime.now().strftime('%m%d')}"
            elif first_name:
                employee_data['employee_id'] = f"RI{first_name[:2].upper()}{datetime.now().strftime('%m%d')}"
            else:
                employee_data['employee_id'] = f"RIUNK{datetime.now().strftime('%m%d')}"
        
        return employee_data
    
    def sync_to_database(self, employee_records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Sync employee records to the database
        
        Args:
            employee_records: List of processed employee records
            
        Returns:
            Dictionary with sync statistics
        """
        from database.connection import get_db_session
        from database.models import Employee
        
        stats = {
            'total_records': len(employee_records),
            'created': 0,
            'updated': 0,
            'errors': 0
        }
        
        try:
            with get_db_session() as session:
                for record in employee_records:
                    try:
                        # Check if employee already exists
                        existing_employee = None
                        
                        # Try to find by employee_id first
                        if record.get('employee_id'):
                            existing_employee = session.query(Employee).filter_by(
                                employee_id=record['employee_id']
                            ).first()
                        
                        # If not found, try by email
                        if not existing_employee and record.get('email'):
                            existing_employee = session.query(Employee).filter_by(
                                email=record['email']
                            ).first()

                        # If still not found, try by first_name and last_name combination
                        if not existing_employee and record.get('first_name') and record.get('last_name'):
                            existing_employee = session.query(Employee).filter_by(
                                first_name=record['first_name'],
                                last_name=record['last_name']
                            ).first()
                        
                        # Filter record to only include fields that exist in the Employee model
                        excluded_fields = ['data_source', 'last_synced', 'full_name']
                        valid_fields = {}
                        for key, value in record.items():
                            if hasattr(Employee, key) and key not in excluded_fields:
                                valid_fields[key] = value

                        # Ensure required fields are not None
                        if not valid_fields.get('first_name'):
                            valid_fields['first_name'] = 'Unknown'
                        # Allow empty last_name - set to empty string if None
                        if valid_fields.get('last_name') is None:
                            valid_fields['last_name'] = ''
                        if not valid_fields.get('email'):
                            stats['errors'] += 1
                            logger.error(f"Skipping employee {valid_fields.get('first_name')} - no email provided")
                            continue

                        if existing_employee:
                            # Update existing employee
                            for key, value in valid_fields.items():
                                if value is not None:
                                    setattr(existing_employee, key, value)
                            stats['updated'] += 1
                            logger.info(f"Updated employee: {record.get('first_name')} {record.get('last_name')}")
                        else:
                            # Create new employee
                            new_employee = Employee(**valid_fields)
                            session.add(new_employee)
                            stats['created'] += 1
                            logger.info(f"Created employee: {record.get('first_name')} {record.get('last_name')}")
                        
                    except Exception as e:
                        stats['errors'] += 1
                        logger.error(f"Error syncing employee {record.get('full_name')}: {str(e)}")
                        continue
                
                session.commit()
                logger.info(f"Sync completed: {stats}")
                
        except Exception as e:
            logger.error(f"Error during database sync: {str(e)}")
            stats['errors'] = stats['total_records']
        
        return stats
    
    def full_sync(self) -> Dict[str, Any]:
        """
        Perform a full sync from Google Sheets to database
        
        Returns:
            Dictionary with sync results
        """
        result = {
            'success': False,
            'message': '',
            'stats': {},
            'data_preview': []
        }
        
        try:
            # Step 1: Fetch data from Google Sheets
            df = self.fetch_employee_data()
            if df is None:
                result['message'] = "Failed to fetch data from Google Sheets"
                return result
            
            # Step 2: Process the data
            employee_records = self.process_employee_data(df)
            if not employee_records:
                result['message'] = "No valid employee records found"
                return result
            
            # Step 3: Sync to database
            stats = self.sync_to_database(employee_records)
            
            # Step 4: Prepare result
            result['success'] = True
            result['message'] = f"Sync completed successfully. Created: {stats['created']}, Updated: {stats['updated']}, Errors: {stats['errors']}"
            result['stats'] = stats
            result['data_preview'] = employee_records[:5]  # First 5 records for preview
            
        except Exception as e:
            result['message'] = f"Sync failed: {str(e)}"
            logger.error(f"Full sync failed: {str(e)}")
        
        return result

    def prepare_employee_for_sheets(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare employee data for Google Sheets format

        Args:
            employee_data: Employee data from onboarding form

        Returns:
            Dictionary formatted for Google Sheets columns
        """
        # Get first and last name from employee data
        first_name = employee_data.get('first_name', '')
        last_name = employee_data.get('last_name', '')

        # Generate employee ID if not provided
        employee_id = employee_data.get('employee_id')
        if not employee_id:
            if first_name and last_name:
                initials = first_name[0] + last_name[0]
                employee_id = f"RI{initials.upper()}{datetime.now().strftime('%m%d')}"
            elif first_name:
                employee_id = f"RI{first_name[:2].upper()}{datetime.now().strftime('%m%d')}"
            else:
                employee_id = f"RIUNK{datetime.now().strftime('%m%d')}"

        # Map to Google Sheets column format
        sheets_data = {
            'Employee ID': employee_id,
            'First Name': first_name,
            'Last Name': last_name,
            'Email ID': employee_data.get('email_personal', ''),
            'Reporting Manager': employee_data.get('reporting_manager', ''),
            'Manager Mail ID': self._get_manager_email(employee_data.get('reporting_manager', '')),
            'Department': employee_data.get('department', ''),
            'Categories': employee_data.get('employee_type', 'full_time')
        }

        return sheets_data

    def add_employee_to_sheets(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add employee to Google Sheets automatically

        Note: This is a placeholder implementation since we're using a public CSV URL.
        In a real implementation, you would use Google Sheets API with write permissions.

        Args:
            employee_data: Employee data to add to sheets

        Returns:
            Dictionary with success status and message
        """
        try:
            # Prepare data for Google Sheets format
            sheets_data = self.prepare_employee_for_sheets(employee_data)

            # Since we're using a public CSV URL (read-only), we can't actually write to the sheet
            # In a real implementation, you would:
            # 1. Use Google Sheets API with service account credentials
            # 2. Append the row to the sheet
            # 3. Return success/failure status

            logger.info(f"Employee data prepared for Google Sheets: {sheets_data}")
            logger.warning("Automatic Google Sheets update not implemented - using read-only CSV URL")

            # For now, we'll return success but log that manual addition is needed
            return {
                'success': True,
                'message': 'Employee data prepared for Google Sheets. Manual addition required.',
                'sheets_data': sheets_data
            }

        except Exception as e:
            logger.error(f"Error preparing employee for Google Sheets: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }

    def _get_manager_email(self, manager_name: str) -> str:
        """
        Generate manager email from manager name
        This is a simple implementation - in production you might have a lookup table
        """
        if not manager_name:
            return ''

        # Convert "John Doe" to "john.doe@rapidinnovation.com"
        email_name = manager_name.lower().replace(' ', '.')
        return f"{email_name}@rapidinnovation.com"

    def get_sheets_add_instructions(self, sheets_data: Dict[str, Any]) -> str:
        """
        Generate instructions for manually adding employee to Google Sheets

        Args:
            sheets_data: Formatted data for Google Sheets

        Returns:
            Formatted instructions string
        """
        instructions = f"""
**📋 Instructions to Add Employee to Google Sheets:**

1. **Open your Google Sheets** employee database
2. **Add a new row** with the following data:

**Column Values:**
"""

        for column, value in sheets_data.items():
            instructions += f"   • **{column}:** {value}\n"

        instructions += f"""
3. **Save the sheet** - changes will be automatically synced
4. **Refresh the HR system** to see the new employee in the system

**📊 Google Sheets URL:** {self.csv_url.replace('/pub?output=csv', '/edit')}

**Note:** Once added to Google Sheets, the employee will appear in the HR system within 5 minutes (cache refresh time).
"""

        return instructions

# Global instance
google_sheets_integration = GoogleSheetsIntegration()
