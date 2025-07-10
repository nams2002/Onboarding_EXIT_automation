import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from database.connection import get_db_session
from database.models import Employee, OnboardingChecklist, Document, EmailLog, EmployeeType
from modules.email.email_Sender import EmailSender
from config import config

logger = logging.getLogger(__name__)

class BGVProcessor:
    """Handle background verification process for employees"""
    
    def __init__(self):
        self.email_sender = EmailSender()
    
    def initiate_bgv(self, employee_id: int, previous_employers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Initiate background verification process"""
        try:
            with get_db_session() as session:
                # Get employee
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # BGV is only for experienced full-time employees
                if employee.employee_type != EmployeeType.FULL_TIME:
                    return {
                        'success': False,
                        'message': 'BGV is only applicable for full-time employees'
                    }
                
                # Check if documents are verified
                checklist = session.query(OnboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if not checklist or not checklist.documents_verified:
                    return {
                        'success': False,
                        'message': 'All documents must be verified before initiating BGV'
                    }
                
                # Send BGV emails to previous employers
                bgv_results = []
                for employer in previous_employers:
                    result = self._send_bgv_email(employee, employer)
                    bgv_results.append({
                        'company': employer['company_name'],
                        'email_sent': result['success'],
                        'message': result.get('message', '')
                    })
                
                # Update checklist
                checklist.bgv_initiated = True
                checklist.bgv_initiated_date = datetime.utcnow()
                session.commit()
                
                # Send notification to employee
                self._send_bgv_notification_to_employee(employee)
                
                logger.info(f"BGV initiated for employee {employee.employee_id}")
                
                return {
                    'success': True,
                    'message': 'Background verification initiated',
                    'results': bgv_results
                }
                
        except Exception as e:
            logger.error(f"Error initiating BGV: {str(e)}")
            return {
                'success': False,
                'message': f'Error initiating BGV: {str(e)}'
            }
    
    def update_bgv_status(self, employee_id: int, company_name: str, 
                         verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update BGV status for a specific company"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Store BGV response (in production, this would be in a separate BGV table)
                checklist = session.query(OnboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                # Update notes with BGV status
                existing_notes = checklist.notes or ""
                bgv_note = f"\n\nBGV Response from {company_name} ({date.today()}):\n"
                bgv_note += f"Verification Status: {verification_data.get('status', 'Pending')}\n"
                bgv_note += f"Comments: {verification_data.get('comments', 'N/A')}\n"
                
                checklist.notes = existing_notes + bgv_note
                
                # Check if all BGV is complete
                if verification_data.get('all_complete', False):
                    checklist.bgv_completed = True
                    checklist.bgv_completed_date = datetime.utcnow()
                
                session.commit()
                
                return {
                    'success': True,
                    'message': 'BGV status updated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error updating BGV status: {str(e)}")
            return {
                'success': False,
                'message': f'Error updating BGV status: {str(e)}'
            }
    
    def get_bgv_status(self, employee_id: int) -> Dict[str, Any]:
        """Get current BGV status for an employee"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found',
                        'data': None
                    }
                
                checklist = session.query(OnboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if not checklist:
                    return {
                        'success': False,
                        'message': 'Onboarding checklist not found',
                        'data': None
                    }
                
                bgv_data = {
                    'initiated': checklist.bgv_initiated,
                    'initiated_date': checklist.bgv_initiated_date,
                    'completed': checklist.bgv_completed,
                    'completed_date': checklist.bgv_completed_date,
                    'notes': checklist.notes,
                    'status': 'Completed' if checklist.bgv_completed else 'In Progress' if checklist.bgv_initiated else 'Not Started'
                }
                
                return {
                    'success': True,
                    'data': bgv_data
                }
                
        except Exception as e:
            logger.error(f"Error getting BGV status: {str(e)}")
            return {
                'success': False,
                'message': f'Error getting BGV status: {str(e)}',
                'data': None
            }
    
    def _send_bgv_email(self, employee: Employee, employer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send BGV email to previous employer"""
        try:
            # Prepare BGV form data
            bgv_form_data = self._prepare_bgv_form(employee, employer_data)
            
            subject = f"Employee Background Verification - {employee.full_name} - Rapid Innovation"
            
            body_html = f"""
            <p>Dear HR,</p>
            
            <p>I hope you are doing great !!</p>
            
            <p>This is about the Background Verification of <b>"{employee.full_name}"</b> who worked in your esteemed organization.</p>
            
            <p>Please find below, the form for Background verification. It would be very kind if you could spare a few minutes 
            and verify the information provided by {employee.full_name}.</p>
            
            {bgv_form_data}
            
            <p>Feel free to get in touch if you have any questions.</p>
            
            <p>Regards<br>
            Team HR<br>
            Rapid Innovation</p>
            """
            
            email_data = {
                'to_email': employer_data.get('hr_email'),
                'cc_emails': [config.DEFAULT_SENDER_EMAIL],
                'subject': subject,
                'body_html': body_html,
                'body_text': self.email_sender._html_to_text(body_html)
            }
            
            # Add attachments if any (employment documents)
            if employer_data.get('documents'):
                email_data['attachments'] = employer_data['documents']
            
            result = self.email_sender.send_email(email_data)
            
            if result['success']:
                # Log email
                self.email_sender.log_email(
                    employee_id=employee.id,
                    email_data={
                        'email_type': 'bgv_request',
                        'to_email': employer_data.get('hr_email'),
                        'subject': subject
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending BGV email: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending BGV email: {str(e)}'
            }
    
    def _prepare_bgv_form(self, employee: Employee, employer_data: Dict[str, Any]) -> str:
        """Prepare BGV form HTML"""
        form_html = """
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr>
                <th style="background-color: #f0f0f0;">Particulars</th>
                <th style="background-color: #f0f0f0;">Details provided by Candidate</th>
                <th style="background-color: #f0f0f0;">Details as per company records</th>
            </tr>
        """
        
        form_fields = [
            ('Employee Name', employee.full_name, ''),
            ('Employee ID', employer_data.get('employee_id', 'Please specify'), 'Please specify'),
            ('Designation', employer_data.get('designation', ''), '<small>(In case of a mismatch, please clarify with reason)</small>'),
            ('Period of Employment', f"{employer_data.get('from_date', '')} to {employer_data.get('to_date', '')}", ''),
            ('Remuneration', employer_data.get('last_salary', ''), ''),
            ('Reporting to', employer_data.get('reporting_manager', 'Please specify'), '<small>(Please confirm if the employee ever reported to the stated supervisor)</small>'),
            ('Character & Conduct', '', 'Please specify'),
            ('Ownership', '', 'Please specify'),
            ('Reason for Leaving', employer_data.get('reason_for_leaving', ''), 'Please specify'),
            ('Eligible for rehire', '', 'Please specify (If No, kindly specify the reason)'),
            ('Status of Exit Formalities', '', '<small>(In case of pending; please specify from whose side)</small>'),
            ('Are the Attached Documents Genuine?', 'Attached', 'Yes/No <small>(If No, kindly specify the reason)</small>'),
            ('Additional Comments', '', 'Please specify')
        ]
        
        for field, candidate_value, company_field in form_fields:
            form_html += f"""
            <tr>
                <td><b>{field}</b></td>
                <td>{candidate_value}</td>
                <td>{company_field}</td>
            </tr>
            """
        
        form_html += """
            <tr>
                <td colspan="3" style="background-color: #f0f0f0;"><b>Name and Job title of the verifying Authority</b></td>
            </tr>
            <tr>
                <td colspan="3">Please specify</td>
            </tr>
        </table>
        """
        
        return form_html
    
    def _send_bgv_notification_to_employee(self, employee: Employee):
        """Send notification to employee about BGV initiation"""
        try:
            subject = "Background Verification Process Initiated"
            
            body_html = f"""
            <p>Dear {employee.full_name},</p>
            
            <p>This is to inform you that we have initiated the background verification process for your employment.</p>
            
            <p>We have reached out to your previous employer(s) for verification of the information provided by you. 
            This is a standard process for all new employees.</p>
            
            <p>The verification process typically takes 7-10 business days. We will keep you updated on the progress.</p>
            
            <p>If you have any questions or concerns, please feel free to reach out to the HR team.</p>
            
            <p>Best regards,<br>
            Team HR<br>
            Rapid Innovation</p>
            """
            
            email_data = {
                'to_email': employee.email_personal,
                'subject': subject,
                'body_html': body_html,
                'body_text': self.email_sender._html_to_text(body_html)
            }
            
            result = self.email_sender.send_email(email_data)
            
            if result['success']:
                self.email_sender.log_email(
                    employee_id=employee.id,
                    email_data={
                        'email_type': 'bgv_notification',
                        'to_email': employee.email_personal,
                        'subject': subject
                    }
                )
            
        except Exception as e:
            logger.error(f"Error sending BGV notification: {str(e)}")