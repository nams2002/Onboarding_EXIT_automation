import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
from database.connection import get_db_session
from database.models import Employee, OffboardingChecklist
from modules.email.email_Sender import EmailSender
from config import config
from utils.helpers import calculate_days_between, format_date

logger = logging.getLogger(__name__)

class ExitManager:
    """Manage employee exit/offboarding process"""
    
    def __init__(self):
        self.email_sender = EmailSender()
    
    def initiate_exit(self, exit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate exit process for an employee"""
        try:
            with get_db_session() as session:
                # Get employee
                employee = session.query(Employee).filter_by(id=exit_data['employee_id']).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Check if employee is already in exit process
                existing_checklist = session.query(OffboardingChecklist).filter_by(
                    employee_id=employee.id
                ).first()
                
                if existing_checklist:
                    return {
                        'success': False,
                        'message': 'Exit process already initiated for this employee'
                    }
                
                # Validate dates
                resignation_date = exit_data['resignation_date']
                last_working_day = exit_data['last_working_day']
                
                if last_working_day < resignation_date:
                    return {
                        'success': False,
                        'message': 'Last working day cannot be before resignation date'
                    }
                
                # Check notice period
                notice_period_days = calculate_days_between(resignation_date, last_working_day)
                required_notice = self._get_required_notice_period(employee)
                
                short_notice = notice_period_days < required_notice
                
                # Create offboarding checklist
                offboarding_checklist = OffboardingChecklist(
                    employee_id=employee.id,
                    resignation_date=resignation_date,
                    last_working_day=last_working_day,
                    exit_type=exit_data.get('exit_type', 'resignation'),
                    exit_reason=exit_data.get('exit_reason', ''),
                    manager_approval=exit_data.get('manager_informed', False),
                    notes=f"Notice period: {notice_period_days} days (Required: {required_notice} days)"
                )
                
                if exit_data.get('manager_informed'):
                    offboarding_checklist.manager_approval_date = datetime.utcnow()
                
                session.add(offboarding_checklist)
                
                # Update employee status
                employee.status = 'offboarding'
                
                session.commit()
                
                # Send exit confirmation emails
                self._send_exit_confirmation_email(employee, exit_data, short_notice)
                
                # Send manager notification if not already informed
                if not exit_data.get('manager_informed'):
                    self._send_manager_notification(employee, exit_data)
                
                logger.info(f"Exit process initiated for employee {employee.employee_id}")
                
                return {
                    'success': True,
                    'message': 'Exit process initiated successfully',
                    'short_notice': short_notice,
                    'notice_period_days': notice_period_days,
                    'required_notice': required_notice
                }
                
        except Exception as e:
            logger.error(f"Error initiating exit: {str(e)}")
            return {
                'success': False,
                'message': f'Error initiating exit: {str(e)}'
            }
    
    def approve_manager_confirmation(self, employee_id: int, approved_by: str, 
                                   knowledge_transfer_plan: str = None) -> Dict[str, Any]:
        """Manager approval for exit and knowledge transfer"""
        try:
            with get_db_session() as session:
                checklist = session.query(OffboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if not checklist:
                    return {
                        'success': False,
                        'message': 'Offboarding checklist not found'
                    }
                
                # Update manager approval
                checklist.manager_approval = True
                checklist.manager_approval_date = datetime.utcnow()
                
                if knowledge_transfer_plan:
                    existing_notes = checklist.notes or ""
                    checklist.notes = existing_notes + f"\n\nKnowledge Transfer Plan:\n{knowledge_transfer_plan}"
                
                session.commit()
                
                # Send confirmation to HR
                employee = session.query(Employee).filter_by(id=employee_id).first()
                self._send_manager_approval_notification(employee, approved_by)
                
                return {
                    'success': True,
                    'message': 'Manager approval recorded successfully'
                }
                
        except Exception as e:
            logger.error(f"Error recording manager approval: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def update_knowledge_transfer_status(self, employee_id: int, completed: bool, 
                                       details: str = None) -> Dict[str, Any]:
        """Update knowledge transfer completion status"""
        try:
            with get_db_session() as session:
                checklist = session.query(OffboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if not checklist:
                    return {
                        'success': False,
                        'message': 'Offboarding checklist not found'
                    }
                
                checklist.knowledge_transfer = completed
                if completed:
                    checklist.knowledge_transfer_date = datetime.utcnow()
                
                if details:
                    existing_notes = checklist.notes or ""
                    checklist.notes = existing_notes + f"\n\nKnowledge Transfer Details:\n{details}"
                
                session.commit()
                
                return {
                    'success': True,
                    'message': 'Knowledge transfer status updated'
                }
                
        except Exception as e:
            logger.error(f"Error updating knowledge transfer: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def get_exit_status(self, employee_id: int) -> Dict[str, Any]:
        """Get current exit status for an employee"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found',
                        'data': None
                    }
                
                checklist = session.query(OffboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if not checklist:
                    return {
                        'success': False,
                        'message': 'Exit process not initiated',
                        'data': None
                    }
                
                # Calculate progress
                tasks = [
                    checklist.manager_approval,
                    checklist.knowledge_transfer,
                    checklist.assets_returned,
                    checklist.access_revoked,
                    checklist.fnf_processed,
                    checklist.experience_letter_issued
                ]
                completed_tasks = sum(1 for task in tasks if task)
                progress_percentage = (completed_tasks / len(tasks)) * 100
                
                # Days remaining
                days_remaining = (checklist.last_working_day - date.today()).days
                
                exit_data = {
                    'employee': {
                        'name': employee.full_name,
                        'employee_id': employee.employee_id,
                        'designation': employee.designation,
                        'department': employee.department
                    },
                    'exit_details': {
                        'resignation_date': checklist.resignation_date,
                        'last_working_day': checklist.last_working_day,
                        'exit_type': checklist.exit_type,
                        'exit_reason': checklist.exit_reason,
                        'days_remaining': days_remaining
                    },
                    'checklist_status': {
                        'manager_approval': checklist.manager_approval,
                        'knowledge_transfer': checklist.knowledge_transfer,
                        'assets_returned': checklist.assets_returned,
                        'access_revoked': checklist.access_revoked,
                        'fnf_processed': checklist.fnf_processed,
                        'experience_letter_issued': checklist.experience_letter_issued,
                        'completed': checklist.offboarding_completed
                    },
                    'progress': {
                        'percentage': progress_percentage,
                        'completed_tasks': completed_tasks,
                        'total_tasks': len(tasks)
                    }
                }
                
                return {
                    'success': True,
                    'data': exit_data
                }
                
        except Exception as e:
            logger.error(f"Error getting exit status: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }
    
    def _get_required_notice_period(self, employee: Employee) -> int:
        """Get required notice period in days based on employee type and status"""
        employee_type = employee.employee_type
        
        if employee_type == 'full_time':
            # Check if employee is confirmed (past probation)
            if employee.date_of_joining:
                months_worked = (date.today() - employee.date_of_joining).days / 30
                probation_months = employee.probation_period or config.PROBATION_PERIOD['full_time']
                
                if months_worked > probation_months:
                    return config.NOTICE_PERIOD['full_time']['confirmed']
                else:
                    return config.NOTICE_PERIOD['full_time']['probation']
            else:
                return config.NOTICE_PERIOD['full_time']['confirmed']
        
        elif employee_type == 'intern':
            return config.NOTICE_PERIOD['intern']
        
        else:  # contractor
            return config.NOTICE_PERIOD['contractor']
    
    def _send_exit_confirmation_email(self, employee: Employee, exit_data: Dict[str, Any], 
                                    short_notice: bool):
        """Send exit confirmation email to employee"""
        try:
            subject = f"Exit Formalities - {employee.full_name} - LWD"
            
            # Determine employee type for email content
            if employee.employee_type == 'intern':
                payslip_info = "Your invoices will be considered as payslips."
                settlement_timeline = "Your full and final settlement will be processed within 30-45 days from your last working day."
            else:
                payslip_info = "All your payslips are available on Razorpay; we expect you to download them and take them with you."
                settlement_timeline = "Your full and final settlement will be processed within 30-45 days from your last working day."
                
            body_html = f"""
            <p>Hi {employee.full_name},</p>
            
            <p>This is to confirm that your last working day at Rapid Innovation is <b>{format_date(exit_data['last_working_day'])}</b>.</p>
            
            <p>You are requested to please look into the following points:</p>
            
            <ol>
                <li>Please change all the communication addresses, if any are provided as the company's address.</li>
                <li>{payslip_info}</li>
            """
            
            if employee.employee_type == 'full_time':
                body_html += """
                <li>Please ensure to submit all company belongings to the people concerned on the last working day, 
                like a laptop, bag, mouse, headphones, and dongle (if any).</li>
                <li>If you wish to withdraw your PF amount, you can do that on the online PF portal. 
                (People having less than 6 months of experience with us will not be eligible to withdraw the PF amount)</li>
                """
            
            body_html += f"""
                <li>Please refer to the following Link to the exit feedback form and submit your valuable feedback 
                on or before your last working day.</li>
                <li>Also, refer to the {'Internship' if employee.employee_type == 'intern' else 'Appointment'}
                Letter signed by you at the time of Joining Rapid Innovation so that you can adhere to all the 
                clauses mentioned in it.</li>
                <li>Kindly move all the files to a folder in the drive and provide ownership to {employee.reporting_manager}'s mail ID</li>
            </ol>
            
            <p>{settlement_timeline} HR will be sending the FNF statement to your email ID.</p>
            """
            
            if short_notice:
                body_html += f"""
                <p><b>Note:</b> As per company policy, the required notice period is {self._get_required_notice_period(employee)} days. 
                Since you have served a shorter notice period, appropriate recovery may be applicable as per your appointment letter.</p>
                """
            
            body_html += """
            <p>Regards<br>
            Team HR<br>
            Rapid Innovation</p>
            """
            
            email_data = {
                'to_email': employee.email or employee.email_personal,
                'cc_emails': [config.DEFAULT_SENDER_EMAIL],
                'subject': subject,
                'body_html': body_html,
                'body_text': self.email_sender._html_to_text(body_html)
            }
            
            result = self.email_sender.send_email(email_data)
            
            if result['success']:
                self.email_sender.log_email(
                    employee_id=employee.id,
                    email_data={
                        'email_type': 'exit_confirmation',
                        'to_email': email_data['to_email'],
                        'subject': subject
                    }
                )
            
        except Exception as e:
            logger.error(f"Error sending exit confirmation email: {str(e)}")
    
    def _send_manager_notification(self, employee: Employee, exit_data: Dict[str, Any]):
        """Send notification to manager about employee exit"""
        try:
            subject = f"Confirmation for proceeding with the Exit formalities - {employee.full_name}"
            
            body_html = f"""
            <p>Hi {employee.reporting_manager},</p>
            
            <p>I hope you are doing well !!</p>
            
            <p>As you know, the LWD is <b>{format_date(exit_data['last_working_day'])}</b> as the last working day of 
            <b>{employee.full_name}</b>.</p>
            
            <p>Kindly let me know once all his knowledge transfer is done so that I can proceed with his exit formalities. 
            These formalities include deactivating his official email ID (once deactivated cannot be restored) and removing 
            him from Slack. Kindly let us know if the official mail data has to be transferred to any other account.</p>
            
            <p>Also please take care of any software he is using like the GitHub account, also please remove him from 
            project groups.</p>
            
            <p>Please let me know in case of any queries.</p>
            
            <p>Regards,<br>
            Team HR<br>
            Rapid Innovation</p>
            """
            
            # In production, get manager's email from database
            manager_email = f"{employee.reporting_manager.lower().replace(' ', '.')}@rapidinnovation.com"
            
            email_data = {
                'to_email': manager_email,
                'cc_emails': [config.DEFAULT_SENDER_EMAIL],
                'subject': subject,
                'body_html': body_html,
                'body_text': self.email_sender._html_to_text(body_html)
            }
            
            result = self.email_sender.send_email(email_data)
            
            if result['success']:
                self.email_sender.log_email(
                    employee_id=employee.id,
                    email_data={
                        'email_type': 'manager_exit_notification',
                        'to_email': manager_email,
                        'subject': subject
                    }
                )
            
        except Exception as e:
            logger.error(f"Error sending manager notification: {str(e)}")
    
    def _send_manager_approval_notification(self, employee: Employee, approved_by: str):
        """Send notification to HR about manager approval"""
        try:
            subject = f"Manager Approval Received - Exit Process - {employee.full_name}"
            
            body_html = f"""
            <p>Dear HR Team,</p>
            
            <p>This is to inform you that {approved_by} has approved the exit process for 
            <b>{employee.full_name}</b> ({employee.employee_id}).</p>
            
            <p>Knowledge transfer arrangements have been confirmed. You may proceed with the 
            remaining exit formalities.</p>
            
            <p>Employee Details:<br>
            Name: {employee.full_name}<br>
            Employee ID: {employee.employee_id}<br>
            Designation: {employee.designation}<br>
            Department: {employee.department}</p>
            
            <p>Best regards,<br>
            HR System</p>
            """
            
            email_data = {
                'to_email': config.DEFAULT_SENDER_EMAIL,
                'subject': subject,
                'body_html': body_html,
                'body_text': self.email_sender._html_to_text(body_html)
            }
            
            self.email_sender.send_email(email_data)
            
        except Exception as e:
            logger.error(f"Error sending manager approval notification: {str(e)}")