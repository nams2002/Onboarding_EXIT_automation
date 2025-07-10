"""
Internal Notifications Module for Exit Process
Handles notifications to IT team, HR team, and other internal stakeholders
"""

import logging
from typing import Dict, Any
from datetime import datetime, date
from database.connection import get_db_session
from database.models import Employee, OffboardingChecklist
from modules.email.email_Sender import EmailSender
from config import config

logger = logging.getLogger(__name__)

class InternalNotificationManager:
    """Manages internal notifications for exit process"""
    
    def __init__(self):
        self.email_sender = EmailSender()
    
    def send_it_access_revocation_notification(self, employee_id: int) -> Dict[str, Any]:
        """Send notification to IT team about upcoming access revocation"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                checklist = session.query(OffboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if not checklist:
                    return {
                        'success': False,
                        'message': 'Offboarding checklist not found'
                    }
                
                subject = f"IT Action Required - Access Revocation for {employee.full_name} - LWD: {checklist.last_working_day}"
                
                body_html = f"""
                <p>Dear IT Team,</p>
                
                <p>This is to inform you that <b>{employee.full_name}</b> (Employee ID: {employee.employee_id}) 
                has initiated the exit process.</p>
                
                <p><b>Employee Details:</b></p>
                <ul>
                    <li><b>Name:</b> {employee.full_name}</li>
                    <li><b>Employee ID:</b> {employee.employee_id}</li>
                    <li><b>Designation:</b> {employee.designation}</li>
                    <li><b>Department:</b> {employee.department}</li>
                    <li><b>Reporting Manager:</b> {employee.reporting_manager}</li>
                    <li><b>Resignation Date:</b> {checklist.resignation_date}</li>
                    <li><b>Last Working Day:</b> {checklist.last_working_day}</li>
                </ul>
                
                <p><b>Action Required:</b></p>
                <ol>
                    <li>Prepare for system access revocation on the last working day</li>
                    <li>Coordinate with the manager for knowledge transfer completion</li>
                    <li>Plan for email data backup/transfer if required</li>
                    <li>Schedule deactivation of the following accounts:
                        <ul>
                            <li>Official email account</li>
                            <li>Slack/Teams access</li>
                            <li>GitHub/Development tools</li>
                            <li>VPN access</li>
                            <li>Any other system access</li>
                        </ul>
                    </li>
                </ol>
                
                <p><b>Important Notes:</b></p>
                <ul>
                    <li>Access should only be revoked AFTER knowledge transfer is completed</li>
                    <li>Coordinate with the reporting manager before final revocation</li>
                    <li>Ensure any critical data is backed up before account deactivation</li>
                </ul>
                
                <p>Please confirm receipt of this notification and update the HR team once 
                the access revocation is completed.</p>
                
                <p>Best regards,<br>
                Team HR<br>
                Rapid Innovation</p>
                """
                
                # Send to IT team (you can configure IT team emails in config)
                it_emails = getattr(config, 'IT_TEAM_EMAILS', ['it@rapidinnovation.com'])
                
                email_data = {
                    'to_email': it_emails[0] if it_emails else 'it@rapidinnovation.com',
                    'cc_emails': it_emails[1:] + [config.DEFAULT_SENDER_EMAIL] if len(it_emails) > 1 else [config.DEFAULT_SENDER_EMAIL],
                    'subject': subject,
                    'body_html': body_html,
                    'body_text': self.email_sender._html_to_text(body_html)
                }
                
                result = self.email_sender.send_email(email_data)
                
                if result['success']:
                    self.email_sender.log_email(
                        employee_id=employee.id,
                        email_data={
                            'email_type': 'it_access_revocation_notification',
                            'to_email': email_data['to_email'],
                            'subject': subject
                        }
                    )
                
                return result
                
        except Exception as e:
            logger.error(f"Error sending IT notification: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending IT notification: {str(e)}'
            }
    
    def send_hr_final_settlement_notification(self, employee_id: int) -> Dict[str, Any]:
        """Send notification to HR team about final settlement preparation"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                checklist = session.query(OffboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if not checklist:
                    return {
                        'success': False,
                        'message': 'Offboarding checklist not found'
                    }
                
                subject = f"HR Action Required - Final Settlement for {employee.full_name} - LWD: {checklist.last_working_day}"
                
                body_html = f"""
                <p>Dear HR Team,</p>
                
                <p>This is to inform you that <b>{employee.full_name}</b> (Employee ID: {employee.employee_id}) 
                has initiated the exit process and final settlement preparation is required.</p>
                
                <p><b>Employee Details:</b></p>
                <ul>
                    <li><b>Name:</b> {employee.full_name}</li>
                    <li><b>Employee ID:</b> {employee.employee_id}</li>
                    <li><b>Designation:</b> {employee.designation}</li>
                    <li><b>Department:</b> {employee.department}</li>
                    <li><b>Employee Type:</b> {employee.employee_type.value}</li>
                    <li><b>Resignation Date:</b> {checklist.resignation_date}</li>
                    <li><b>Last Working Day:</b> {checklist.last_working_day}</li>
                    <li><b>Exit Reason:</b> {checklist.exit_reason or 'Not specified'}</li>
                </ul>
                
                <p><b>Action Required:</b></p>
                <ol>
                    <li>Prepare final settlement calculation including:
                        <ul>
                            <li>Salary for the notice period</li>
                            <li>Unused leave encashment</li>
                            <li>Bonus/incentives (if applicable)</li>
                            <li>Gratuity calculation (if applicable)</li>
                            <li>Any recoveries (notice period shortfall, advances, etc.)</li>
                        </ul>
                    </li>
                    <li>Verify all assets are returned before final settlement</li>
                    <li>Ensure all company property is accounted for</li>
                    <li>Process final settlement within 30-45 days of last working day</li>
                    <li>Generate and send FNF statement to employee</li>
                </ol>
                
                <p><b>Timeline:</b> Final settlement should be processed within 30-45 days from the last working day 
                as per company policy.</p>
                
                <p>Please update the system once the final settlement is processed.</p>
                
                <p>Best regards,<br>
                HR Automation System<br>
                Rapid Innovation</p>
                """
                
                # Send to HR team
                hr_emails = getattr(config, 'HR_TEAM_EMAILS', [config.DEFAULT_SENDER_EMAIL])
                
                email_data = {
                    'to_email': hr_emails[0],
                    'cc_emails': hr_emails[1:] if len(hr_emails) > 1 else [],
                    'subject': subject,
                    'body_html': body_html,
                    'body_text': self.email_sender._html_to_text(body_html)
                }
                
                result = self.email_sender.send_email(email_data)
                
                if result['success']:
                    self.email_sender.log_email(
                        employee_id=employee.id,
                        email_data={
                            'email_type': 'hr_final_settlement_notification',
                            'to_email': email_data['to_email'],
                            'subject': subject
                        }
                    )
                
                return result
                
        except Exception as e:
            logger.error(f"Error sending HR final settlement notification: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending HR notification: {str(e)}'
            }
    
    def send_hr_experience_letter_notification(self, employee_id: int) -> Dict[str, Any]:
        """Send notification to HR team about experience letter preparation"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                checklist = session.query(OffboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if not checklist:
                    return {
                        'success': False,
                        'message': 'Offboarding checklist not found'
                    }
                
                subject = f"HR Action Required - Experience Letter for {employee.full_name} - LWD: {checklist.last_working_day}"
                
                # Determine document type based on employee type
                doc_type = "Experience Certificate" if employee.employee_type.value != 'intern' else "Internship Completion Certificate"
                
                body_html = f"""
                <p>Dear HR Team,</p>
                
                <p>This is to inform you that <b>{employee.full_name}</b> (Employee ID: {employee.employee_id}) 
                has initiated the exit process and {doc_type.lower()} preparation is required.</p>
                
                <p><b>Employee Details:</b></p>
                <ul>
                    <li><b>Name:</b> {employee.full_name}</li>
                    <li><b>Employee ID:</b> {employee.employee_id}</li>
                    <li><b>Designation:</b> {employee.designation}</li>
                    <li><b>Department:</b> {employee.department}</li>
                    <li><b>Employee Type:</b> {employee.employee_type.value}</li>
                    <li><b>Date of Joining:</b> {employee.date_of_joining}</li>
                    <li><b>Last Working Day:</b> {checklist.last_working_day}</li>
                </ul>
                
                <p><b>Document Required:</b> {doc_type}</p>
                
                <p><b>Action Required:</b></p>
                <ol>
                    <li>Prepare {doc_type.lower()} with the following details:
                        <ul>
                            <li>Employee's full name and designation</li>
                            <li>Employment/internship period</li>
                            <li>Department and reporting structure</li>
                            <li>Performance summary (if applicable)</li>
                            <li>Dues settlement status</li>
                        </ul>
                    </li>
                    <li>Ensure all formalities are completed before issuing the certificate</li>
                    <li>Generate the document using the HR system</li>
                    <li>Send the certificate to employee's personal email</li>
                </ol>
                
                <p><b>Timeline:</b> The {doc_type.lower()} should be prepared and sent within 7-10 days 
                after the last working day.</p>
                
                <p>Please update the system once the {doc_type.lower()} is generated and sent.</p>
                
                <p>Best regards,<br>
                HR Automation System<br>
                Rapid Innovation</p>
                """
                
                # Send to HR team
                hr_emails = getattr(config, 'HR_TEAM_EMAILS', [config.DEFAULT_SENDER_EMAIL])
                
                email_data = {
                    'to_email': hr_emails[0],
                    'cc_emails': hr_emails[1:] if len(hr_emails) > 1 else [],
                    'subject': subject,
                    'body_html': body_html,
                    'body_text': self.email_sender._html_to_text(body_html)
                }
                
                result = self.email_sender.send_email(email_data)
                
                if result['success']:
                    self.email_sender.log_email(
                        employee_id=employee.id,
                        email_data={
                            'email_type': 'hr_experience_letter_notification',
                            'to_email': email_data['to_email'],
                            'subject': subject
                        }
                    )
                
                return result
                
        except Exception as e:
            logger.error(f"Error sending HR experience letter notification: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending HR notification: {str(e)}'
            }
