import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from database.connection import get_db_session
from database.models import Employee, Asset, OffboardingChecklist, AssetStatus
from modules.email.email_Sender import EmailSender
from config import config
from utils.helpers import format_date

logger = logging.getLogger(__name__)

class AssetManager:
    """Manage company assets assigned to employees"""
    
    def __init__(self):
        self.email_sender = EmailSender()
    
    def assign_asset(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assign an asset to an employee"""
        try:
            with get_db_session() as session:
                # Verify employee exists
                employee = session.query(Employee).filter_by(id=asset_data['employee_id']).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Create asset record
                asset = Asset(
                    employee_id=asset_data['employee_id'],
                    asset_type=asset_data['asset_type'],
                    asset_description=asset_data.get('asset_description', ''),
                    asset_tag=asset_data.get('asset_tag', ''),
                    serial_number=asset_data.get('serial_number', ''),
                    issued_date=asset_data.get('issued_date', date.today()),
                    issued_by=asset_data['issued_by'],
                    return_status=AssetStatus.ISSUED,
                    notes=asset_data.get('notes', '')
                )
                
                session.add(asset)
                session.commit()
                
                logger.info(f"Asset {asset.asset_type} assigned to employee {employee.employee_id}")
                
                return {
                    'success': True,
                    'message': 'Asset assigned successfully',
                    'asset_id': asset.id
                }
                
        except Exception as e:
            logger.error(f"Error assigning asset: {str(e)}")
            return {
                'success': False,
                'message': f'Error assigning asset: {str(e)}'
            }
    
    def return_asset(self, asset_id: int, return_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mark an asset as returned"""
        try:
            with get_db_session() as session:
                asset = session.query(Asset).filter_by(id=asset_id).first()
                if not asset:
                    return {
                        'success': False,
                        'message': 'Asset not found'
                    }
                
                # Update asset return details
                asset.return_date = return_data.get('return_date', date.today())
                asset.returned_to = return_data['returned_to']
                asset.return_status = AssetStatus(return_data.get('return_status', 'returned'))
                asset.condition_on_return = return_data.get('condition_on_return', '')
                
                # Add notes if provided
                if return_data.get('notes'):
                    existing_notes = asset.notes or ""
                    asset.notes = existing_notes + f"\n\nReturn Notes: {return_data['notes']}"
                
                session.commit()
                
                # Check if all assets are returned for the employee
                self._check_all_assets_returned(session, asset.employee_id)
                
                logger.info(f"Asset {asset.id} marked as {asset.return_status.value}")
                
                return {
                    'success': True,
                    'message': f'Asset marked as {asset.return_status.value}'
                }
                
        except Exception as e:
            logger.error(f"Error returning asset: {str(e)}")
            return {
                'success': False,
                'message': f'Error returning asset: {str(e)}'
            }
    
    def get_employee_assets(self, employee_id: int) -> Dict[str, Any]:
        """Get all assets assigned to an employee"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found',
                        'data': None
                    }
                
                # Get all assets
                assets = session.query(Asset).filter_by(employee_id=employee_id).all()
                
                # Categorize assets
                issued_assets = [a for a in assets if a.return_status == AssetStatus.ISSUED]
                returned_assets = [a for a in assets if a.return_status == AssetStatus.RETURNED]
                other_assets = [a for a in assets if a.return_status not in [AssetStatus.ISSUED, AssetStatus.RETURNED]]
                
                asset_data = {
                    'employee': {
                        'name': employee.full_name,
                        'employee_id': employee.employee_id,
                        'designation': employee.designation
                    },
                    'summary': {
                        'total_assets': len(assets),
                        'issued': len(issued_assets),
                        'returned': len(returned_assets),
                        'damaged': len([a for a in assets if a.return_status == AssetStatus.DAMAGED]),
                        'lost': len([a for a in assets if a.return_status == AssetStatus.LOST])
                    },
                    'assets': {
                        'issued': self._serialize_assets(issued_assets),
                        'returned': self._serialize_assets(returned_assets),
                        'other': self._serialize_assets(other_assets)
                    }
                }
                
                return {
                    'success': True,
                    'data': asset_data
                }
                
        except Exception as e:
            logger.error(f"Error getting employee assets: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'data': None
            }
    
    def send_asset_return_reminder(self, employee_id: int) -> Dict[str, Any]:
        """Send reminder to return assets"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Get pending assets
                pending_assets = session.query(Asset).filter_by(
                    employee_id=employee_id,
                    return_status=AssetStatus.ISSUED
                ).all()
                
                if not pending_assets:
                    return {
                        'success': False,
                        'message': 'No pending assets to return'
                    }
                
                # Get offboarding details
                checklist = session.query(OffboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                # Send reminder email
                result = self._send_asset_reminder_email(employee, pending_assets, checklist)
                
                return result
                
        except Exception as e:
            logger.error(f"Error sending asset reminder: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def generate_asset_handover_form(self, employee_id: int) -> Dict[str, Any]:
        """Generate asset handover form for an employee"""
        try:
            with get_db_session() as session:
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Get all assets
                assets = session.query(Asset).filter_by(employee_id=employee_id).all()
                
                if not assets:
                    return {
                        'success': False,
                        'message': 'No assets found for this employee'
                    }
                
                # Generate form HTML
                form_html = self._generate_handover_form_html(employee, assets)
                
                return {
                    'success': True,
                    'form_html': form_html,
                    'asset_count': len(assets)
                }
                
        except Exception as e:
            logger.error(f"Error generating handover form: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def bulk_asset_assignment(self, employee_id: int, asset_list: List[Dict[str, Any]], 
                            issued_by: str) -> Dict[str, Any]:
        """Assign multiple assets to an employee"""
        try:
            results = {
                'total': len(asset_list),
                'success': 0,
                'failed': 0,
                'details': []
            }
            
            for asset_info in asset_list:
                asset_data = {
                    'employee_id': employee_id,
                    'issued_by': issued_by,
                    **asset_info
                }
                
                result = self.assign_asset(asset_data)
                
                if result['success']:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                
                results['details'].append({
                    'asset_type': asset_info.get('asset_type', 'Unknown'),
                    'success': result['success'],
                    'message': result.get('message', '')
                })
            
            return {
                'success': results['failed'] == 0,
                'message': f"Assigned {results['success']} out of {results['total']} assets",
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in bulk assignment: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    def _check_all_assets_returned(self, session, employee_id: int):
        """Check if all assets are returned and update offboarding checklist"""
        try:
            # Get all assets for employee
            assets = session.query(Asset).filter_by(employee_id=employee_id).all()
            
            # Check if all assets are returned
            all_returned = all(
                asset.return_status in [AssetStatus.RETURNED, AssetStatus.LOST] 
                for asset in assets
            ) and len(assets) > 0
            
            if all_returned:
                # Update offboarding checklist
                checklist = session.query(OffboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if checklist and not checklist.assets_returned:
                    checklist.assets_returned = True
                    checklist.assets_return_date = datetime.utcnow()
                    session.commit()
                    
                    logger.info(f"All assets returned for employee ID {employee_id}")
                    
        except Exception as e:
            logger.error(f"Error checking asset return completion: {str(e)}")
    
    def _serialize_assets(self, assets: List[Asset]) -> List[Dict[str, Any]]:
        """Serialize asset objects to dictionaries"""
        return [
            {
                'id': asset.id,
                'asset_type': asset.asset_type,
                'asset_description': asset.asset_description,
                'asset_tag': asset.asset_tag,
                'serial_number': asset.serial_number,
                'issued_date': format_date(asset.issued_date) if asset.issued_date else None,
                'issued_by': asset.issued_by,
                'return_date': format_date(asset.return_date) if asset.return_date else None,
                'returned_to': asset.returned_to,
                'return_status': asset.return_status.value,
                'condition_on_return': asset.condition_on_return,
                'notes': asset.notes
            }
            for asset in assets
        ]
    
    def _send_asset_reminder_email(self, employee: Employee, pending_assets: List[Asset], 
                                  checklist: Optional[OffboardingChecklist]) -> Dict[str, Any]:
        """Send asset return reminder email"""
        try:
            subject = "Asset Return Reminder"
            
            # Build asset list HTML
            asset_list_html = "<ul>"
            for asset in pending_assets:
                asset_details = f"{asset.asset_type}"
                if asset.asset_tag:
                    asset_details += f" (Tag: {asset.asset_tag})"
                if asset.serial_number:
                    asset_details += f" (S/N: {asset.serial_number})"
                asset_list_html += f"<li>{asset_details}</li>"
            asset_list_html += "</ul>"
            
            body_html = f"""
            <p>Dear {employee.full_name},</p>
            
            <p>This is a reminder to return the following company assets assigned to you:</p>
            
            {asset_list_html}
            """
            
            if checklist and checklist.last_working_day:
                days_remaining = (checklist.last_working_day - date.today()).days
                if days_remaining > 0:
                    body_html += f"""
                    <p>As your last working day is <b>{format_date(checklist.last_working_day)}</b> 
                    ({days_remaining} days remaining), please ensure all assets are returned before or 
                    on your last working day.</p>
                    """
                else:
                    body_html += f"""
                    <p>As your last working day was <b>{format_date(checklist.last_working_day)}</b>, 
                    please return these assets immediately to complete your exit formalities.</p>
                    """
            
            body_html += f"""
            <p><b>Return Instructions:</b><br>
            Name: {config.COMPANY_NAME}<br>
            Address: {config.COMPANY_ADDRESS}<br>
            Contact Number: {config.COMPANY_PHONE}</p>
            
            <p><b>Note:</b> Please ensure that all assets are in good working condition. Take photos 
            or videos of the devices before dispatching. For valuable items like MacBooks, please 
            take insurance while shipping.</p>
            
            <p>Your final settlement will be processed only after all company assets are received 
            in good condition.</p>
            
            <p>Please reach out to us if you have any queries.</p>
            
            <p>Thanks & Regards<br>
            Team HR<br>
            Rapid Innovation</p>
            """
            
            email_data = {
                'to_email': employee.email_personal,
                'cc_emails': [config.DEFAULT_SENDER_EMAIL, employee.email_official] if employee.email_official else [config.DEFAULT_SENDER_EMAIL],
                'subject': subject,
                'body_html': body_html,
                'body_text': self.email_sender._html_to_text(body_html)
            }
            
            result = self.email_sender.send_email(email_data)
            
            if result['success']:
                # Log email
                self.email_sender.log_email(
                    employee_id=employee.id,
                    email_data={
                        'email_type': 'asset_return_reminder',
                        'to_email': employee.email_personal,
                        'subject': subject
                    }
                )
                
                return {
                    'success': True,
                    'message': 'Asset return reminder sent successfully'
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error sending asset reminder email: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending email: {str(e)}'
            }
    
    def _generate_handover_form_html(self, employee: Employee, assets: List[Asset]) -> str:
        """Generate HTML for asset handover form"""
        form_html = f"""
        <h3>Asset Handover Form</h3>
        <p><b>Employee Details:</b><br>
        Name: {employee.full_name}<br>
        Employee ID: {employee.employee_id}<br>
        Designation: {employee.designation}<br>
        Department: {employee.department}</p>
        
        <p><b>Date:</b> {format_date(date.today())}</p>
        
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f0f0f0;">
                <th>S.No</th>
                <th>Asset Type</th>
                <th>Description</th>
                <th>Asset Tag</th>
                <th>Serial Number</th>
                <th>Issue Date</th>
                <th>Return Status</th>
                <th>Return Date</th>
                <th>Condition</th>
                <th>Remarks</th>
            </tr>
        """
        
        for idx, asset in enumerate(assets, 1):
            status_color = {
                AssetStatus.ISSUED: '#ffc107',
                AssetStatus.RETURNED: '#28a745',
                AssetStatus.DAMAGED: '#dc3545',
                AssetStatus.LOST: '#6c757d'
            }.get(asset.return_status, '#ffffff')
            
            form_html += f"""
            <tr>
                <td>{idx}</td>
                <td>{asset.asset_type}</td>
                <td>{asset.asset_description or '-'}</td>
                <td>{asset.asset_tag or '-'}</td>
                <td>{asset.serial_number or '-'}</td>
                <td>{format_date(asset.issued_date) if asset.issued_date else '-'}</td>
                <td style="background-color: {status_color}; color: white;">{asset.return_status.value.upper()}</td>
                <td>{format_date(asset.return_date) if asset.return_date else '-'}</td>
                <td>{asset.condition_on_return or '-'}</td>
                <td>{asset.notes or '-'}</td>
            </tr>
            """
        
        form_html += """
        </table>
        
        <br>
        <p><b>Declaration:</b><br>
        I hereby confirm that I have returned all the company assets listed above in the condition mentioned.</p>
        
        <br><br>
        <table style="width: 100%;">
            <tr>
                <td style="width: 50%;">
                    <p>_____________________<br>
                    Employee Signature<br>
                    Date: _____________</p>
                </td>
                <td style="width: 50%;">
                    <p>_____________________<br>
                    HR/Admin Signature<br>
                    Date: _____________</p>
                </td>
            </tr>
        </table>
        """
        
        return form_html