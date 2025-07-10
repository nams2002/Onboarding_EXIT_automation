import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database.connection import get_db_session, get_next_employee_id
from database.models import (
    Employee, OnboardingChecklist, OffboardingChecklist,
    Document, SystemAccess, Asset, EmailLog,
    EmployeeStatus, EmployeeType
)
from modules.email.email_Sender import EmailSender
from config import config

logger = logging.getLogger(__name__)

class EmployeeManager:
    """Manager class for employee-related operations"""
    
    def __init__(self):
        self.email_sender = EmailSender()
    
    def create_employee(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new employee and initiate onboarding"""
        try:
            with get_db_session() as session:
                # Generate employee ID
                employee_id = get_next_employee_id()
                if not employee_id:
                    return {
                        'success': False,
                        'message': 'Failed to generate employee ID'
                    }
                
                # Create employee record with all available fields
                employee_fields = {
                    'employee_id': employee_data.get('employee_id'),
                    'first_name': employee_data['first_name'],
                    'last_name': employee_data.get('last_name', ''),
                    'email': employee_data.get('email'),
                    'email_personal': employee_data.get('email_personal'),
                    'phone': employee_data.get('phone'),
                    'address': employee_data.get('address'),
                    'employee_type': employee_data['employee_type'],
                    'designation': employee_data.get('designation'),
                    'department': employee_data.get('department'),
                    'reporting_manager': employee_data.get('reporting_manager'),
                    'manager_email': employee_data.get('manager_email'),
                    'date_of_joining': employee_data.get('date_of_joining'),
                    'work_location': employee_data.get('work_location'),
                    'notice_period': employee_data.get('notice_period'),
                    'emergency_contact_name': employee_data.get('emergency_contact_name'),
                    'emergency_contact_phone': employee_data.get('emergency_contact_phone'),
                    'blood_group': employee_data.get('blood_group'),
                    'special_requirements': employee_data.get('special_requirements'),
                    'status': 'onboarding'
                }

                # Remove None values, but ensure required fields are present
                employee_fields = {k: v for k, v in employee_fields.items() if v is not None}

                # Ensure required email field is present
                if 'email' not in employee_fields or not employee_fields.get('email'):
                    # If email is missing, use email_personal as fallback
                    if employee_data.get('email_personal'):
                        employee_fields['email'] = employee_data.get('email_personal')
                    else:
                        # If both are missing, this is an error
                        return {
                            'success': False,
                            'message': 'Email is required but not provided'
                        }

                employee = Employee(**employee_fields)
                
                # Set compensation based on employee type
                if employee_data['employee_type'] == 'full_time':
                    employee.ctc = employee_data.get('ctc', 0)
                    employee.probation_period = employee_data.get('probation_period', 6)
                    employee.benefits = employee_data.get('benefits', '')
                elif employee_data['employee_type'] == 'intern':
                    employee.stipend = employee_data.get('stipend', 0)
                    employee.internship_duration = employee_data.get('internship_duration', 3)
                else:  # contractor
                    employee.hourly_rate = employee_data.get('hourly_rate', 0)
                    employee.contract_duration = employee_data.get('contract_duration', 6)
                
                session.add(employee)
                session.flush()  # Get the employee ID
                
                # Create onboarding checklist
                onboarding_checklist = OnboardingChecklist(
                    employee_id=employee.id
                )
                session.add(onboarding_checklist)
                
                # Create system access records
                for system in config.SYSTEM_PLATFORMS:
                    system_access = SystemAccess(
                        employee_id=employee.id,
                        system_name=system,
                        access_granted=False
                    )
                    session.add(system_access)
                
                session.commit()

                # Send initial document collection email automatically
                self._send_document_collection_email(employee)

                # Automatically add employee to Google Sheets
                self._add_employee_to_google_sheets(employee)

                logger.info(f"Employee created successfully: {employee.employee_id}")

                return {
                    'success': True,
                    'message': 'Employee created successfully and added to Google Sheets',
                    'employee_id': employee.employee_id,
                    'id': employee.id
                }
                
        except IntegrityError as e:
            logger.error(f"Integrity error creating employee: {str(e)}")
            return {
                'success': False,
                'message': 'Employee with this email already exists'
            }
        except Exception as e:
            logger.error(f"Error creating employee: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating employee: {str(e)}'
            }
    
    def get_employee(self, employee_id: int) -> Optional[Employee]:
        """Get employee by ID"""
        try:
            with get_db_session() as session:
                return session.query(Employee).filter_by(id=employee_id).first()
        except Exception as e:
            logger.error(f"Error fetching employee: {str(e)}")
            return None
    
    def get_employee_by_employee_id(self, employee_id: str) -> Optional[Employee]:
        """Get employee by employee ID (not database ID)"""
        try:
            with get_db_session() as session:
                return session.query(Employee).filter_by(employee_id=employee_id).first()
        except Exception as e:
            logger.error(f"Error fetching employee: {str(e)}")
            return None
    
    def update_employee(self, employee_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update employee information"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Update allowed fields
                allowed_fields = [
                    'first_name', 'last_name', 'phone', 'address', 'designation',
                    'department', 'reporting_manager', 'manager_email', 'ctc', 'stipend',
                    'hourly_rate', 'email', 'email_personal', 'work_location',
                    'notice_period', 'emergency_contact_name', 'emergency_contact_phone',
                    'blood_group', 'special_requirements', 'benefits'
                ]
                
                for field in allowed_fields:
                    if field in update_data:
                        setattr(employee, field, update_data[field])
                
                employee.updated_at = datetime.utcnow()
                session.commit()
                
                logger.info(f"Employee updated successfully: {employee.employee_id}")
                
                return {
                    'success': True,
                    'message': 'Employee updated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error updating employee: {str(e)}")
            return {
                'success': False,
                'message': f'Error updating employee: {str(e)}'
            }
    
    def get_employees_by_status(self, status: str) -> List[Employee]:
        """Get all employees by status"""
        try:
            with get_db_session() as session:
                return session.query(Employee).filter_by(
                    status=status
                ).all()
        except Exception as e:
            logger.error(f"Error fetching employees by status: {str(e)}")
            return []
    
    def search_employees(self, search_term: str, filters: Dict[str, Any] = None) -> List[Employee]:
        """Search employees with optional filters"""
        try:
            with get_db_session() as session:
                query = session.query(Employee)
                
                # Apply search term
                if search_term:
                    query = query.filter(
                        (Employee.first_name.ilike(f'%{search_term}%')) |
                        (Employee.last_name.ilike(f'%{search_term}%')) |
                        (Employee.email.ilike(f'%{search_term}%')) |
                        (Employee.email_personal.ilike(f'%{search_term}%')) |
                        (Employee.employee_id.ilike(f'%{search_term}%'))
                    )
                
                # Apply filters
                if filters:
                    if 'employee_type' in filters and filters['employee_type']:
                        query = query.filter_by(employee_type=filters['employee_type'])

                    if 'department' in filters and filters['department']:
                        query = query.filter_by(department=filters['department'])

                    if 'status' in filters and filters['status']:
                        query = query.filter_by(status=filters['status'])
                
                return query.all()
                
        except Exception as e:
            logger.error(f"Error searching employees: {str(e)}")
            return []
    
    def update_employee_status(self, employee_id: int, new_status: str) -> Dict[str, Any]:
        """Update employee status"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                old_status = employee.status
                employee.status = new_status

                # Handle status-specific actions
                if new_status == 'active' and old_status == 'onboarding':
                    # Mark onboarding as complete
                    checklist = session.query(OnboardingChecklist).filter_by(
                        employee_id=employee_id
                    ).first()
                    if checklist:
                        checklist.onboarding_completed = True
                        checklist.completed_at = datetime.utcnow()

                elif new_status == 'exited' and old_status == 'offboarding':
                    # Mark offboarding as complete
                    checklist = session.query(OffboardingChecklist).filter_by(
                        employee_id=employee_id
                    ).first()
                    if checklist:
                        checklist.offboarding_completed = True
                        checklist.completed_at = datetime.utcnow()
                
                session.commit()
                
                logger.info(f"Employee status updated: {employee.employee_id} - {new_status}")
                
                return {
                    'success': True,
                    'message': 'Employee status updated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error updating employee status: {str(e)}")
            return {
                'success': False,
                'message': f'Error updating status: {str(e)}'
            }
    
    def get_employee_documents(self, employee_id: int) -> List[Document]:
        """Get all documents for an employee"""
        try:
            with get_db_session() as session:
                return session.query(Document).filter_by(
                    employee_id=employee_id
                ).order_by(Document.uploaded_at.desc()).all()
        except Exception as e:
            logger.error(f"Error fetching employee documents: {str(e)}")
            return []
    
    def get_employee_assets(self, employee_id: int) -> List[Asset]:
        """Get all assets assigned to an employee"""
        try:
            with get_db_session() as session:
                return session.query(Asset).filter_by(
                    employee_id=employee_id
                ).all()
        except Exception as e:
            logger.error(f"Error fetching employee assets: {str(e)}")
            return []
    
    def get_employee_system_access(self, employee_id: int) -> List[SystemAccess]:
        """Get system access status for an employee"""
        try:
            with get_db_session() as session:
                return session.query(SystemAccess).filter_by(
                    employee_id=employee_id
                ).all()
        except Exception as e:
            logger.error(f"Error fetching employee system access: {str(e)}")
            return []
    
    def get_onboarding_checklist(self, employee_id: int) -> Optional[OnboardingChecklist]:
        """Get onboarding checklist for an employee"""
        try:
            with get_db_session() as session:
                return session.query(OnboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
        except Exception as e:
            logger.error(f"Error fetching onboarding checklist: {str(e)}")
            return None
    
    def get_offboarding_checklist(self, employee_id: int) -> Optional[OffboardingChecklist]:
        """Get offboarding checklist for an employee"""
        try:
            with get_db_session() as session:
                return session.query(OffboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
        except Exception as e:
            logger.error(f"Error fetching offboarding checklist: {str(e)}")
            return None
    
    def _send_document_collection_email(self, employee: Employee) -> bool:
        """Send initial document collection email"""
        try:
            # Create personalized email content with actual employee data
            if employee.employee_type == 'intern':
                subject = f"Important Documents Required - {employee.designation}"
                greeting = f"Hi {employee.first_name},"
                position_text = f"your joining for the '{employee.designation}' position at Rapid Innovation"
            else:
                subject = f"Important Documents Required - {employee.designation}"
                greeting = f"Hi {employee.first_name},"
                position_text = f"your joining for the '{employee.designation}' position at Rapid Innovation"

            # Create detailed email body with actual employee data
            body_html = f"""
            <p>{greeting}</p>

            <p>Greetings from Rapid Innovation!!</p>

            <p>This is regarding {position_text}.</p>

            <p>As a part of our Employment Joining process, we would require soft copies of the below-mentioned documents:</p>

            <ol>
                <li><strong>Educational Docs</strong> (10th, 12th, Graduation & Post Graduation Certificates)</li>
                <li><strong>ID proofs</strong> (Aadhaar card, Passport, Driving license, PAN card)</li>
                <li><strong>Resignation/relieving letters</strong>, the Last three Months of salary slips, Appointment letters, and offer letters from previous organizations</li>
                <li><strong>Passport-size photograph</strong></li>
            </ol>

            <p>Also, please share your full name and address as per your documents.</p>

            <p>Feel free to get in touch with me in case of any queries or questions.</p>

            <p>Thanks & Regards,<br>
            <strong>Team HR</strong><br>
            Rapid Innovation</p>
            """

            # Prepare email data with direct HTML content
            email_data = {
                'to_email': employee.email_personal,
                'cc_emails': [config.DEFAULT_SENDER_EMAIL],
                'subject': subject,
                'body_html': body_html,
                'body_text': self.email_sender._html_to_text(body_html)
            }
            
            # Send email using direct email method
            result = self.email_sender.send_email(email_data)

            if result['success']:
                # Log email
                self.email_sender.log_email(
                    employee_id=employee.id,
                    email_data={
                        'email_type': 'document_request',
                        'to_email': employee.email_personal,
                        'subject': subject
                    }
                )

                logger.info(f"Document collection email sent to {employee.email_personal}")
                return True
            else:
                logger.error(f"Failed to send document collection email: {result['message']}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending document collection email: {str(e)}")
            return False

    def _add_employee_to_google_sheets(self, employee: Employee) -> bool:
        """Automatically add employee to Google Sheets"""
        try:
            from modules.integrations.google_sheets import google_sheets_integration

            # Prepare employee data for Google Sheets
            sheets_data = {
                'employee_id': employee.employee_id,
                'first_name': employee.first_name,
                'last_name': employee.last_name or '',
                'email': employee.email_personal,
                'phone': employee.phone or '',
                'designation': employee.designation,
                'department': employee.department,
                'employee_type': employee.employee_type.value if hasattr(employee.employee_type, 'value') else str(employee.employee_type),
                'reporting_manager': employee.reporting_manager or '',
                'date_of_joining': employee.date_of_joining.strftime('%Y-%m-%d') if employee.date_of_joining else '',
                'status': employee.status,
                'created_date': datetime.now().strftime('%Y-%m-%d')
            }

            # Add to Google Sheets
            result = google_sheets_integration.add_employee_to_sheets(sheets_data)

            if result.get('success'):
                logger.info(f"Employee {employee.employee_id} added to Google Sheets successfully")
                return True
            else:
                logger.warning(f"Failed to add employee to Google Sheets: {result.get('message', 'Unknown error')}")
                return False

        except Exception as e:
            logger.error(f"Error adding employee to Google Sheets: {str(e)}")
            return False

    def get_dashboard_statistics(self) -> Dict[str, Any]:
        """Get statistics for dashboard"""
        try:
            with get_db_session() as session:
                # Total employees by status
                total_active = session.query(Employee).filter_by(
                    status='active'
                ).count()

                total_onboarding = session.query(Employee).filter_by(
                    status='onboarding'
                ).count()

                total_offboarding = session.query(Employee).filter_by(
                    status='offboarding'
                ).count()

                # Employees by type
                full_time_count = session.query(Employee).filter_by(
                    employee_type='full_time',
                    status='active'
                ).count()

                intern_count = session.query(Employee).filter_by(
                    employee_type='intern',
                    status='active'
                ).count()

                contractor_count = session.query(Employee).filter_by(
                    employee_type='contractor',
                    status='active'
                ).count()

                # Recent activities
                recent_joins = session.query(Employee).filter(
                    Employee.status == 'onboarding'
                ).order_by(Employee.created_at.desc()).limit(5).all()

                recent_exits = session.query(Employee).filter(
                    Employee.status == 'offboarding'
                ).order_by(Employee.updated_at.desc()).limit(5).all()
                
                return {
                    'total_active': total_active,
                    'total_onboarding': total_onboarding,
                    'total_offboarding': total_offboarding,
                    'employee_types': {
                        'full_time': full_time_count,
                        'intern': intern_count,
                        'contractor': contractor_count
                    },
                    'recent_joins': recent_joins,
                    'recent_exits': recent_exits
                }
                
        except Exception as e:
            logger.error(f"Error getting dashboard statistics: {str(e)}")
            return {
                'total_active': 0,
                'total_onboarding': 0,
                'total_offboarding': 0,
                'employee_types': {
                    'full_time': 0,
                    'intern': 0,
                    'contractor': 0
                },
                'recent_joins': [],
                'recent_exits': []
            }