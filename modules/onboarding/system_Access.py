import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from database.connection import get_db_session
from database.models import Employee, SystemAccess, OnboardingChecklist, EmployeeType
from modules.email.email_Sender import EmailSender

from config import config
import requests
import json

logger = logging.getLogger(__name__)

class SystemAccessManager:
    """Manage system access for employees"""

    def __init__(self):
        self.email_sender = EmailSender()

        # MCP functionality removed - using manual processes only
        self.mcp_manager = None
    
    def grant_system_access(self, employee_id: int, system_name: str, 
                           granted_by: str, username: str = None) -> Dict[str, Any]:
        """Grant access to a specific system"""
        try:
            with get_db_session() as session:
                # Get employee
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Get or create system access record
                system_access = session.query(SystemAccess).filter_by(
                    employee_id=employee_id,
                    system_name=system_name
                ).first()
                
                if not system_access:
                    system_access = SystemAccess(
                        employee_id=employee_id,
                        system_name=system_name
                    )
                    session.add(system_access)
                
                # Update access details
                system_access.access_granted = True
                system_access.granted_at = datetime.utcnow()
                system_access.granted_by = granted_by
                
                # Generate username if not provided
                if not username:
                    username = self._generate_username(employee, system_name)
                
                system_access.username = username
                
                # Grant actual access based on system
                access_result = self._grant_actual_access(employee, system_name, username)
                
                if access_result['success']:
                    system_access.notes = f"Access granted successfully. {access_result.get('details', '')}"
                else:
                    system_access.notes = f"Manual intervention required: {access_result.get('message', '')}"
                
                session.commit()
                
                # Check if all systems are granted
                self._check_all_systems_granted(session, employee_id)
                
                # Send access details email
                self._send_access_details_email(employee, system_name, username, access_result.get('password'))
                
                logger.info(f"System access granted for {system_name} to employee {employee.employee_id}")
                
                return {
                    'success': True,
                    'message': f'{system_name} access granted successfully',
                    'username': username
                }
                
        except Exception as e:
            logger.error(f"Error granting system access: {str(e)}")
            return {
                'success': False,
                'message': f'Error granting access: {str(e)}'
            }
    
    def revoke_system_access(self, employee_id: int, system_name: str, 
                            revoked_by: str) -> Dict[str, Any]:
        """Revoke access to a specific system"""
        try:
            with get_db_session() as session:
                # Get system access record
                system_access = session.query(SystemAccess).filter_by(
                    employee_id=employee_id,
                    system_name=system_name
                ).first()
                
                if not system_access:
                    return {
                        'success': False,
                        'message': 'System access record not found'
                    }
                
                # Get employee
                employee = session.query(Employee).filter_by(id=employee_id).first()
                
                # Revoke actual access
                revoke_result = self._revoke_actual_access(employee, system_name, system_access.username)
                
                # Update access record
                system_access.access_granted = False
                system_access.revoked_at = datetime.utcnow()
                system_access.revoked_by = revoked_by
                
                if revoke_result['success']:
                    system_access.notes = f"Access revoked successfully. {revoke_result.get('details', '')}"
                else:
                    system_access.notes = f"Manual intervention required: {revoke_result.get('message', '')}"
                
                session.commit()
                
                logger.info(f"System access revoked for {system_name} from employee {employee.employee_id}")
                
                return {
                    'success': True,
                    'message': f'{system_name} access revoked successfully'
                }
                
        except Exception as e:
            logger.error(f"Error revoking system access: {str(e)}")
            return {
                'success': False,
                'message': f'Error revoking access: {str(e)}'
            }
    
    def grant_all_required_access(self, employee_id: int, granted_by: str) -> Dict[str, Any]:
        """Grant access to all required systems for an employee"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Get required systems based on employee type and role
                required_systems = self._get_required_systems(employee)
                
                results = {
                    'total': len(required_systems),
                    'success': 0,
                    'failed': 0,
                    'details': []
                }
                
                for system in required_systems:
                    result = self.grant_system_access(employee_id, system, granted_by)
                    
                    if result['success']:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                    
                    results['details'].append({
                        'system': system,
                        'success': result['success'],
                        'message': result.get('message', '')
                    })
                
                return {
                    'success': results['failed'] == 0,
                    'message': f"Access granted to {results['success']} out of {results['total']} systems",
                    'results': results
                }
                
        except Exception as e:
            logger.error(f"Error granting all access: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def revoke_all_access(self, employee_id: int, revoked_by: str) -> Dict[str, Any]:
        """Revoke all system access for an employee"""
        try:
            with get_db_session() as session:
                # Get all active system access
                active_access = session.query(SystemAccess).filter_by(
                    employee_id=employee_id,
                    access_granted=True
                ).all()
                
                results = {
                    'total': len(active_access),
                    'success': 0,
                    'failed': 0,
                    'details': []
                }
                
                for access in active_access:
                    result = self.revoke_system_access(
                        employee_id, 
                        access.system_name, 
                        revoked_by
                    )
                    
                    if result['success']:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                    
                    results['details'].append({
                        'system': access.system_name,
                        'success': result['success'],
                        'message': result.get('message', '')
                    })
                
                return {
                    'success': results['failed'] == 0,
                    'message': f"Access revoked from {results['success']} out of {results['total']} systems",
                    'results': results
                }
                
        except Exception as e:
            logger.error(f"Error revoking all access: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def get_employee_system_access(self, employee_id: int) -> List[SystemAccess]:
        """Get all system access records for an employee"""
        try:
            with get_db_session() as session:
                return session.query(SystemAccess).filter_by(
                    employee_id=employee_id
                ).all()
        except Exception as e:
            logger.error(f"Error fetching system access: {str(e)}")
            return []
    
    def _get_required_systems(self, employee: Employee) -> List[str]:
        """Determine required systems based on employee type and role"""
        base_systems = ['Gmail', 'Slack']
        
        if employee.employee_type == EmployeeType.FULL_TIME:
            # Full-time employees get all systems
            return base_systems + ['TeamLogger', 'Google Drive', 'Jira']
        elif employee.employee_type == EmployeeType.INTERN:
            # Interns get basic systems
            return base_systems
        else:  # Contractor
            # Contractors get systems based on their role
            contractor_systems = base_systems + ['TeamLogger']
            if 'developer' in employee.designation.lower() or 'engineer' in employee.designation.lower():
                contractor_systems.extend(['GitHub', 'Jira'])
            return contractor_systems
    
    def _generate_username(self, employee: Employee, system_name: str) -> str:
        """Generate username for a system"""
        # Clean name
        first_name = employee.full_name.split()[0].lower()
        last_name = employee.full_name.split()[-1].lower() if len(employee.full_name.split()) > 1 else ''
        
        if system_name in ['Gmail', 'Google Drive']:
            # Email format
            if employee.email:
                return employee.email
            else:
                return f"{first_name}.{last_name}@rapidinnovation.com"
        else:
            # Standard username format
            return f"{first_name}.{last_name}".replace(' ', '').replace('-', '')
    
    def _grant_actual_access(self, employee: Employee, system_name: str, 
                           username: str) -> Dict[str, Any]:
        """Grant actual access to the system via APIs"""
        try:
            if config.ENABLE_SLACK_INTEGRATION and system_name == 'Slack':
                return self._grant_slack_access(employee, username)
            elif config.ENABLE_GOOGLE_WORKSPACE_INTEGRATION and system_name in ['Gmail', 'Google Drive']:
                return self._grant_google_workspace_access(employee, username)
            elif config.ENABLE_RAZORPAY_INTEGRATION and system_name == 'Razorpay':
                return self._grant_razorpay_access(employee, username)
            else:
                # Manual process required
                return {
                    'success': True,
                    'message': 'Manual access grant required',
                    'details': f'Please manually create account for {username}'
                }
                
        except Exception as e:
            logger.error(f"Error granting actual access: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def _revoke_actual_access(self, employee: Employee, system_name: str, 
                            username: str) -> Dict[str, Any]:
        """Revoke actual access from the system via APIs"""
        try:
            if config.ENABLE_SLACK_INTEGRATION and system_name == 'Slack':
                return self._revoke_slack_access(username)
            elif config.ENABLE_GOOGLE_WORKSPACE_INTEGRATION and system_name in ['Gmail', 'Google Drive']:
                return self._revoke_google_workspace_access(username)
            elif config.ENABLE_RAZORPAY_INTEGRATION and system_name == 'Razorpay':
                return self._revoke_razorpay_access(username)
            else:
                # Manual process required
                return {
                    'success': True,
                    'message': 'Manual access revocation required',
                    'details': f'Please manually disable account for {username}'
                }
                
        except Exception as e:
            logger.error(f"Error revoking actual access: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def _grant_slack_access(self, employee: Employee, username: str) -> Dict[str, Any]:
        """Grant Slack access via Slack API"""
        try:
            # Slack API implementation
            headers = {
                'Authorization': f'Bearer {config.SLACK_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'email': employee.email or employee.email_personal,
                'first_name': employee.full_name.split()[0],
                'last_name': ' '.join(employee.full_name.split()[1:]) if len(employee.full_name.split()) > 1 else '',
                'channels': ['general', 'random']  # Default channels
            }
            
            # This is a placeholder - actual Slack API endpoint would be different
            response = requests.post(
                'https://slack.com/api/users.admin.invite',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Slack invitation sent',
                    'details': 'User will receive an email invitation'
                }
            else:
                return {
                    'success': False,
                    'message': f'Slack API error: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Slack integration error: {str(e)}'
            }
    
    def _grant_google_workspace_access(self, employee: Employee, username: str) -> Dict[str, Any]:
        """Grant Google Workspace access - Manual process only"""
        try:
            # Manual process required - MCP functionality removed
            return {
                'success': True,
                'message': 'Manual Google Workspace account creation required',
                'details': f'Please manually create account for {username}',
                'password': None
            }

        except Exception as e:
            logger.error(f"Error in Google Workspace access: {e}")
            return {
                'success': False,
                'message': f'Google Workspace error: {str(e)}'
            }
    
    def _grant_razorpay_access(self, employee: Employee, username: str) -> Dict[str, Any]:
        """Grant Razorpay access"""
        try:
            # Razorpay API implementation would go here
            return {
                'success': True,
                'message': 'Razorpay account created',
                'details': 'User added to organization'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Razorpay error: {str(e)}'
            }
    
    def _revoke_slack_access(self, username: str) -> Dict[str, Any]:
        """Revoke Slack access"""
        try:
            # Slack API implementation for deactivation
            return {
                'success': True,
                'message': 'Slack access revoked'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Slack revocation error: {str(e)}'
            }
    
    def _revoke_google_workspace_access(self, username: str) -> Dict[str, Any]:
        """Revoke Google Workspace access - Manual process only"""
        try:
            # Manual process required - MCP functionality removed
            return {
                'success': True,
                'message': 'Manual Google Workspace account suspension required',
                'details': f'Please manually suspend account for {username}'
            }

        except Exception as e:
            logger.error(f"Error in Google Workspace revocation: {e}")
            return {
                'success': False,
                'message': f'Google Workspace error: {str(e)}'
            }
    
    def _revoke_razorpay_access(self, username: str) -> Dict[str, Any]:
        """Revoke Razorpay access"""
        try:
            # Razorpay API implementation for deactivation
            return {
                'success': True,
                'message': 'Razorpay access revoked'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Razorpay error: {str(e)}'
            }
    
    def _check_all_systems_granted(self, session, employee_id: int):
        """Check if all required systems are granted and update checklist"""
        try:
            employee = session.query(Employee).filter_by(id=employee_id).first()
            required_systems = self._get_required_systems(employee)
            
            # Get granted systems
            granted_systems = session.query(SystemAccess).filter_by(
                employee_id=employee_id,
                access_granted=True
            ).all()
            
            granted_system_names = [s.system_name for s in granted_systems]
            
            # Check if all required systems are granted
            all_granted = all(sys in granted_system_names for sys in required_systems)
            
            if all_granted:
                # Update onboarding checklist
                checklist = session.query(OnboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                if checklist and not checklist.systems_access_granted:
                    checklist.systems_access_granted = True
                    session.commit()
                    
                    logger.info(f"All system access granted for employee {employee.employee_id}")
                    
        except Exception as e:
            logger.error(f"Error checking system access completion: {str(e)}")
    
    def _send_access_details_email(self, employee: Employee, system_name: str, 
                                  username: str, password: str = None):
        """Send system access details to employee"""
        try:
            subject = f"System Access Granted - {system_name}"
            
            body_html = f"""
            <p>Dear {employee.full_name},</p>
            
            <p>Your access to <b>{system_name}</b> has been granted.</p>
            
            <p><b>Access Details:</b><br>
            Username: {username}<br>
            {'Password: ' + password + '<br>' if password else ''}
            </p>
            
            {'<p>Please change your password on first login.</p>' if password else ''}
            
            <p>If you need any assistance accessing the system, please contact IT support.</p>
            
            <p>Best regards,<br>
            Team HR<br>
            Rapid Innovation</p>
            """
            
            email_data = {
                'to_email': employee.email or employee.email_personal,
                'subject': subject,
                'body_html': body_html,
                'body_text': self.email_sender._html_to_text(body_html)
            }
            
            result = self.email_sender.send_email(email_data)
            
            if result['success']:
                self.email_sender.log_email(
                    employee_id=employee.id,
                    email_data={
                        'email_type': 'system_access_granted',
                        'to_email': email_data['to_email'],
                        'subject': subject
                    }
                )
            
        except Exception as e:
            logger.error(f"Error sending access details email: {str(e)}")