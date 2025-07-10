import logging
from datetime import datetime
from typing import Dict, List, Any
from database.connection import get_db_session
from database.models import Employee, SystemAccess, OffboardingChecklist
from modules.onboarding.system_Access import SystemAccessManager
from modules.email.email_Sender import EmailSender
from config import config
from datetime import date

logger = logging.getLogger(__name__)

class AccessRevocationManager:
    """Manage system access revocation during offboarding"""
    
    def __init__(self):
        self.system_access_manager = SystemAccessManager()
        self.email_sender = EmailSender()
    
    def revoke_all_access(self, employee_id: int, revoked_by: str) -> Dict[str, Any]:
        """Revoke all system access for an offboarding employee"""
        try:
            with get_db_session() as session:
                # Verify employee is in offboarding status
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Get offboarding checklist
                checklist = session.query(OffboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if not checklist:
                    return {
                        'success': False,
                        'message': 'Employee is not in offboarding process'
                    }
                
                # Check prerequisites
                if not checklist.manager_approval:
                    return {
                        'success': False,
                        'message': 'Manager approval required before revoking access'
                    }
                
                if not checklist.knowledge_transfer:
                    return {
                        'success': False,
                        'message': 'Knowledge transfer must be completed before revoking access'
                    }
                
                # Revoke all access using SystemAccessManager
                result = self.system_access_manager.revoke_all_access(employee_id, revoked_by)
                
                if result['success']:
                    # Update offboarding checklist
                    checklist.access_revoked = True
                    checklist.access_revoked_date = datetime.utcnow()
                    session.commit()
                    
                    # Send confirmation email
                    self._send_access_revocation_confirmation(employee, result['results'])
                    
                    logger.info(f"All access revoked for employee {employee.employee_id}")
                
                return result
                
        except Exception as e:
            logger.error(f"Error revoking all access: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def revoke_specific_access(self, employee_id: int, system_name: str, 
                             revoked_by: str) -> Dict[str, Any]:
        """Revoke access to a specific system"""
        try:
            # Use SystemAccessManager to revoke specific access
            result = self.system_access_manager.revoke_system_access(
                employee_id, system_name, revoked_by
            )
            
            if result['success']:
                # Check if all systems are revoked
                with get_db_session() as session:
                    self._check_all_access_revoked(session, employee_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Error revoking specific access: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def get_access_revocation_status(self, employee_id: int) -> Dict[str, Any]:
        """Get current access revocation status"""
        try:
            with get_db_session() as session:
                # Get all system access records
                system_access_list = session.query(SystemAccess).filter_by(
                    employee_id=employee_id
                ).all()
                
                if not system_access_list:
                    return {
                        'success': False,
                        'message': 'No system access records found',
                        'data': None
                    }
                
                # Categorize access
                active_access = []
                revoked_access = []
                
                for access in system_access_list:
                    access_info = {
                        'system_name': access.system_name,
                        'username': access.username,
                        'granted_at': access.granted_at,
                        'granted_by': access.granted_by,
                        'revoked_at': access.revoked_at,
                        'revoked_by': access.revoked_by,
                        'notes': access.notes
                    }
                    
                    if access.access_granted and not access.revoked_at:
                        active_access.append(access_info)
                    else:
                        revoked_access.append(access_info)
                
                return {
                    'success': True,
                    'data': {
                        'total_systems': len(system_access_list),
                        'active_count': len(active_access),
                        'revoked_count': len(revoked_access),
                        'active_access': active_access,
                        'revoked_access': revoked_access,
                        'all_revoked': len(active_access) == 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting revocation status: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }
    
    def schedule_access_revocation(self, employee_id: int, revocation_date: date, 
                                 scheduled_by: str) -> Dict[str, Any]:
        """Schedule access revocation for a future date (typically last working day)"""
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
                
                # Store scheduling information in notes
                existing_notes = checklist.notes or ""
                schedule_note = f"\n\nAccess Revocation Scheduled:\n"
                schedule_note += f"Date: {revocation_date}\n"
                schedule_note += f"Scheduled by: {scheduled_by}\n"
                schedule_note += f"Scheduled on: {datetime.now()}\n"
                
                checklist.notes = existing_notes + schedule_note
                session.commit()
                
                # In production, this would integrate with a task scheduler
                logger.info(f"Access revocation scheduled for {revocation_date} for employee {employee_id}")
                
                return {
                    'success': True,
                    'message': f'Access revocation scheduled for {revocation_date}'
                }
                
        except Exception as e:
            logger.error(f"Error scheduling revocation: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def generate_access_report(self, employee_id: int) -> Dict[str, Any]:
        """Generate a report of all system access for an employee"""
        try:
            # Get access status
            status_result = self.get_access_revocation_status(employee_id)
            
            if not status_result['success']:
                return status_result
            
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Generate report HTML
                report_html = self._generate_access_report_html(employee, status_result['data'])
                
                return {
                    'success': True,
                    'report_html': report_html,
                    'data': status_result['data']
                }
                
        except Exception as e:
            logger.error(f"Error generating access report: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def _check_all_access_revoked(self, session, employee_id: int):
        """Check if all access is revoked and update offboarding checklist"""
        try:
            # Get all system access
            active_access = session.query(SystemAccess).filter_by(
                employee_id=employee_id,
                access_granted=True
            ).filter(
                SystemAccess.revoked_at.is_(None)
            ).count()
            
            if active_access == 0:
                # Update offboarding checklist
                checklist = session.query(OffboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if checklist and not checklist.access_revoked:
                    checklist.access_revoked = True
                    checklist.access_revoked_date = datetime.utcnow()
                    session.commit()
                    
                    logger.info(f"All access revoked for employee ID {employee_id}")
                    
        except Exception as e:
            logger.error(f"Error checking access revocation: {str(e)}")
    
    def _send_access_revocation_confirmation(self, employee: Employee, 
                                           revocation_results: Dict[str, Any]):
        """Send confirmation email about access revocation"""
        try:
            subject = "System Access Revoked - Action Required"
            
            # Build revocation details
            revoked_systems = []
            failed_systems = []
            
            for detail in revocation_results.get('details', []):
                if detail['success']:
                    revoked_systems.append(detail['system'])
                else:
                    failed_systems.append(f"{detail['system']} - {detail['message']}")
            
            body_html = f"""
            <p>Dear {employee.full_name},</p>
            
            <p>This is to inform you that your access to company systems has been revoked as part 
            of your exit process.</p>
            """
            
            if revoked_systems:
                body_html += f"""
                <p><b>Systems Revoked:</b></p>
                <ul>
                    {''.join(f'<li>{system}</li>' for system in revoked_systems)}
                </ul>
                """
            
            if failed_systems:
                body_html += f"""
                <p><b>Manual Revocation Required:</b></p>
                <ul>
                    {''.join(f'<li>{system}</li>' for system in failed_systems)}
                </ul>
                <p>Please contact IT support for these systems.</p>
                """
            
            body_html += f"""
            <p><b>Important Actions Required:</b></p>
            <ol>
                <li>Please ensure you have downloaded any personal files from company systems</li>
                <li>Remove any company data from your personal devices</li>
                <li>Return any authentication devices (tokens, smart cards) if applicable</li>
                <li>Update any personal accounts that use company email for recovery</li>
            </ol>
            
            <p>If you need to access any data for knowledge transfer purposes, please contact 
            your manager immediately.</p>
            
            <p>Best regards,<br>
            Team HR<br>
            Rapid Innovation</p>
            """
            
            email_data = {
                'to_email': employee.email_personal,
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
                        'email_type': 'access_revocation_confirmation',
                        'to_email': employee.email_personal,
                        'subject': subject
                    }
                )
            
        except Exception as e:
            logger.error(f"Error sending revocation confirmation: {str(e)}")
    
    def _generate_access_report_html(self, employee: Employee, access_data: Dict[str, Any]) -> str:
        """Generate HTML report for system access"""
        from utils.helpers import format_date
        
        report_html = f"""
        <h3>System Access Report</h3>
        
        <p><b>Employee Details:</b><br>
        Name: {employee.full_name}<br>
        Employee ID: {employee.employee_id}<br>
        Department: {employee.department}<br>
        Report Generated: {format_date(datetime.now())}</p>
        
        <p><b>Summary:</b><br>
        Total Systems: {access_data['total_systems']}<br>
        Active Access: {access_data['active_count']}<br>
        Revoked Access: {access_data['revoked_count']}</p>
        """
        
        if access_data['active_access']:
            report_html += """
            <h4>Active System Access:</h4>
            <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
                <tr style="background-color: #f0f0f0;">
                    <th>System</th>
                    <th>Username</th>
                    <th>Granted Date</th>
                    <th>Granted By</th>
                </tr>
            """
            
            for access in access_data['active_access']:
                report_html += f"""
                <tr>
                    <td>{access['system_name']}</td>
                    <td>{access['username'] or '-'}</td>
                    <td>{format_date(access['granted_at']) if access['granted_at'] else '-'}</td>
                    <td>{access['granted_by'] or '-'}</td>
                </tr>
                """
            
            report_html += "</table>"
        
        if access_data['revoked_access']:
            report_html += """
            <h4>Revoked System Access:</h4>
            <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
                <tr style="background-color: #f0f0f0;">
                    <th>System</th>
                    <th>Username</th>
                    <th>Revoked Date</th>
                    <th>Revoked By</th>
                </tr>
            """
            
            for access in access_data['revoked_access']:
                report_html += f"""
                <tr>
                    <td>{access['system_name']}</td>
                    <td>{access['username'] or '-'}</td>
                    <td>{format_date(access['revoked_at']) if access['revoked_at'] else '-'}</td>
                    <td>{access['revoked_by'] or '-'}</td>
                </tr>
                """
            
            report_html += "</table>"
        
        return report_html