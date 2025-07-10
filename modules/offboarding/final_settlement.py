import os
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from database.connection import get_db_session
from database.models import Employee, OffboardingChecklist, EmployeeType
from modules.email.email_Sender import EmailSender
from config import config
from utils.helpers import format_date, format_currency, calculate_fnf

logger = logging.getLogger(__name__)

class FnFLetterGenerator:
    """Generate Full and Final Settlement letters"""
    
    def __init__(self):
        self.email_sender = EmailSender()
        
        # Create output directory
        self.output_dir = os.path.join(config.UPLOAD_FOLDER, 'fnf_letters')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_fnf_letter(self, employee_id: int, fnf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Full and Final settlement letter"""
        try:
            with get_db_session() as session:
                # Get employee
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # FnF is only for full-time employees and contractors
                if employee.employee_type == EmployeeType.INTERN:
                    return {
                        'success': False,
                        'message': 'FnF letters are not applicable for interns'
                    }
                
                # Get offboarding checklist
                checklist = session.query(OffboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if not checklist:
                    return {
                        'success': False,
                        'message': 'Offboarding checklist not found'
                    }
                
                # Check if knowledge transfer and assets are returned
                if not checklist.knowledge_transfer:
                    return {
                        'success': False,
                        'message': 'Knowledge transfer must be completed before FnF'
                    }
                
                if not checklist.assets_returned:
                    return {
                        'success': False,
                        'message': 'All assets must be returned before FnF'
                    }
                
                # Prepare template data
                template_data = self._prepare_fnf_data(employee, checklist, fnf_data)
                
                # Generate PDF
                pdf_path = self._generate_fnf_pdf(employee, template_data)
                
                if not pdf_path:
                    return {
                        'success': False,
                        'message': 'Failed to generate FnF letter PDF'
                    }
                
                # Update offboarding checklist
                checklist.fnf_initiated = True
                checklist.fnf_amount = template_data['fnf_components']['net_amount']
                session.commit()
                
                # Send FnF letter email
                email_result = self._send_fnf_letter_email(employee, pdf_path, template_data)
                
                if email_result['success']:
                    logger.info(f"FnF letter generated and sent for employee {employee.employee_id}")
                    
                    return {
                        'success': True,
                        'message': 'FnF letter generated and sent successfully',
                        'pdf_path': pdf_path,
                        'fnf_amount': template_data['fnf_components']['net_amount']
                    }
                else:
                    return {
                        'success': True,
                        'message': 'FnF letter generated but email failed',
                        'pdf_path': pdf_path,
                        'fnf_amount': template_data['fnf_components']['net_amount']
                    }
                
        except Exception as e:
            logger.error(f"Error generating FnF letter: {str(e)}")
            return {
                'success': False,
                'message': f'Error generating FnF letter: {str(e)}'
            }
    
    def _prepare_fnf_data(self, employee: Employee, checklist: OffboardingChecklist, 
                         fnf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for FnF letter template"""
        # Calculate FnF components
        employee_data = {
            'ctc': employee.ctc or 0,
            'employee_type': employee.employee_type.value
        }
        
        exit_data = {
            'last_working_day': checklist.last_working_day,
            'last_salary_date': fnf_data.get('last_salary_date', checklist.last_working_day.replace(day=1)),
            'leave_balance': fnf_data.get('leave_balance', 0),
            'years_of_service': (checklist.last_working_day - employee.date_of_joining).days / 365,
            'notice_period_recovery': fnf_data.get('notice_period_recovery', 0),
            'other_deductions': fnf_data.get('other_deductions', 0)
        }
        
        fnf_components = calculate_fnf(employee_data, exit_data)
        
        template_data = {
            'company_name': config.COMPANY_NAME,
            'company_address': config.COMPANY_ADDRESS,
            'hr_manager_name': config.HR_MANAGER_NAME,
            'hr_manager_designation': config.HR_MANAGER_DESIGNATION,
            'issue_date': format_date(date.today()),
            'employee_name': employee.full_name,
            'employee_id': employee.employee_id,
            'designation': employee.designation,
            'department': employee.department,
            'joining_date': format_date(employee.date_of_joining),
            'leaving_date': format_date(checklist.last_working_day),
            'resignation_date': format_date(checklist.resignation_date),
            'fnf_components': fnf_components,
            'payment_mode': fnf_data.get('payment_mode', 'Bank Transfer'),
            'bank_details': fnf_data.get('bank_details', {}),
            'remarks': fnf_data.get('remarks', '')
        }
        
        return template_data
    
    def _generate_fnf_pdf(self, employee: Employee, template_data: Dict[str, Any]) -> Optional[str]:
        """Generate PDF FnF letter"""
        try:
            # Create filename
            filename = f"fnf_statement_{employee.employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(self.output_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#0066CC'),
                alignment=TA_CENTER,
                spaceAfter=30
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor('#333333'),
                spaceAfter=12
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceAfter=12
            )
            
            right_style = ParagraphStyle(
                'RightAlign',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_RIGHT
            )
            
            # Add company logo if exists
            logo_path = os.path.join('static', 'images', 'company_logo.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=2*inch, height=0.75*inch)
                elements.append(logo)
                elements.append(Spacer(1, 20))
            
            # Title
            elements.append(Paragraph("FULL AND FINAL SETTLEMENT", title_style))
            elements.append(Spacer(1, 20))
            
            # Date and reference
            elements.append(Paragraph(f"Date: {template_data['issue_date']}", right_style))
            elements.append(Paragraph(f"Ref: FNF/{employee.employee_id}/2024", right_style))
            elements.append(Spacer(1, 20))
            
            # Employee details section
            elements.append(Paragraph("<b>EMPLOYEE DETAILS</b>", heading_style))
            
            emp_details_data = [
                ['Employee Name:', template_data['employee_name']],
                ['Employee ID:', template_data['employee_id']],
                ['Designation:', template_data['designation']],
                ['Department:', template_data['department']],
                ['Date of Joining:', template_data['joining_date']],
                ['Date of Resignation:', template_data['resignation_date']],
                ['Last Working Day:', template_data['leaving_date']]
            ]
            
            emp_details_table = Table(emp_details_data, colWidths=[2.5*inch, 3.5*inch])
            emp_details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            elements.append(emp_details_table)
            elements.append(Spacer(1, 30))
            
            # Settlement details section
            elements.append(Paragraph("<b>SETTLEMENT DETAILS</b>", heading_style))
            
            # Earnings section
            earnings_data = [
                ['EARNINGS', '', 'Amount (₹)'],
                ['Pending Salary', '', format_currency(template_data['fnf_components']['pending_salary'])]
            ]
            
            if template_data['fnf_components']['leave_encashment'] > 0:
                earnings_data.append(['Leave Encashment', '', format_currency(template_data['fnf_components']['leave_encashment'])])
            
            if template_data['fnf_components']['gratuity'] > 0:
                earnings_data.append(['Gratuity', '', format_currency(template_data['fnf_components']['gratuity'])])
            
            earnings_data.append(['', '', ''])
            earnings_data.append(['Total Earnings', '', format_currency(template_data['fnf_components']['total_earnings'])])
            
            # Deductions section
            deductions_data = [
                ['', '', ''],
                ['DEDUCTIONS', '', 'Amount (₹)']
            ]
            
            if template_data['fnf_components']['notice_period_recovery'] > 0:
                deductions_data.append(['Notice Period Recovery', '', format_currency(template_data['fnf_components']['notice_period_recovery'])])
            
            if template_data['fnf_components']['other_deductions'] > 0:
                deductions_data.append(['Other Deductions', '', format_currency(template_data['fnf_components']['other_deductions'])])
            
            deductions_data.append(['', '', ''])
            deductions_data.append(['Total Deductions', '', format_currency(template_data['fnf_components']['total_deductions'])])
            
            # Net amount
            net_data = [
                ['', '', ''],
                ['NET AMOUNT PAYABLE', '', format_currency(template_data['fnf_components']['net_amount'])]
            ]
            
            # Combine all data
            settlement_data = earnings_data + deductions_data + net_data
            
            settlement_table = Table(settlement_data, colWidths=[3*inch, 1*inch, 2*inch])
            settlement_table.setStyle(TableStyle([
                # Header rows
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, len(earnings_data)), (-1, len(earnings_data)), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.9)),
                ('BACKGROUND', (0, len(earnings_data)), (-1, len(earnings_data)), colors.Color(0.9, 0.9, 0.9)),
                
                # Total rows
                ('FONTNAME', (0, len(earnings_data)-1), (-1, len(earnings_data)-1), 'Helvetica-Bold'),
                ('FONTNAME', (0, len(earnings_data)+len(deductions_data)-1), (-1, len(earnings_data)+len(deductions_data)-1), 'Helvetica-Bold'),
                
                # Net amount row
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0, 0.4, 0.8, 0.2)),
                
                # General styling
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            elements.append(settlement_table)
            elements.append(Spacer(1, 30))
            
            # Payment details
            if template_data.get('bank_details'):
                elements.append(Paragraph("<b>PAYMENT DETAILS</b>", heading_style))
                payment_text = f"""
                Payment Mode: {template_data['payment_mode']}<br/>
                """
                if template_data['payment_mode'] == 'Bank Transfer':
                    payment_text += f"""
                    Bank Name: {template_data['bank_details'].get('bank_name', 'N/A')}<br/>
                    Account Number: {template_data['bank_details'].get('account_number', 'N/A')}<br/>
                    IFSC Code: {template_data['bank_details'].get('ifsc_code', 'N/A')}
                    """
                elements.append(Paragraph(payment_text, normal_style))
                elements.append(Spacer(1, 20))
            
            # Processing timeline
            elements.append(Paragraph("<b>PROCESSING INFORMATION</b>", heading_style))
            processing_text = f"""
            Your full and final settlement will be processed within {config.FNF_PROCESSING_DAYS} days 
            from your last working day. The amount will be credited to your registered bank account.
            """
            elements.append(Paragraph(processing_text, normal_style))
            elements.append(Spacer(1, 20))
            
            # Tax note
            tax_note = """
            <b>Note:</b> Tax will be deducted as per applicable laws. Form 16 for the current financial 
            year will be issued at the end of the financial year.
            """
            elements.append(Paragraph(tax_note, normal_style))
            elements.append(Spacer(1, 20))
            
            # Remarks
            if template_data.get('remarks'):
                elements.append(Paragraph("<b>REMARKS</b>", heading_style))
                elements.append(Paragraph(template_data['remarks'], normal_style))
                elements.append(Spacer(1, 20))
            
            # Declaration
            declaration = """
            This is a system-generated statement of your full and final settlement. Please review the 
            details carefully. If you have any queries or discrepancies, please contact the HR department 
            within 7 days of receiving this statement.
            """
            elements.append(Paragraph(declaration, normal_style))
            elements.append(Spacer(1, 40))
            
            # Signature section
            elements.append(Paragraph("For Rapid Innovation", normal_style))
            elements.append(Spacer(1, 40))
            
            elements.append(Paragraph(template_data['hr_manager_name'], normal_style))
            elements.append(Paragraph(template_data['hr_manager_designation'], normal_style))
            
            # Build PDF
            doc.build(elements)
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating FnF PDF: {str(e)}")
            return None
    
    def _send_fnf_letter_email(self, employee: Employee, pdf_path: str, 
                              template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send FnF letter email with PDF attachment"""
        try:
            subject = f"Full and Final Settlement Statement - {employee.full_name}"
            
            body_html = f"""
            <p>Dear {employee.full_name},</p>
            
            <p>Please find attached your Full and Final Settlement statement.</p>
            
            <p><b>Settlement Summary:</b><br>
            Total Earnings: {format_currency(template_data['fnf_components']['total_earnings'])}<br>
            Total Deductions: {format_currency(template_data['fnf_components']['total_deductions'])}<br>
            <b>Net Amount Payable: {format_currency(template_data['fnf_components']['net_amount'])}</b></p>
            
            <p>The amount will be processed within {config.FNF_PROCESSING_DAYS} days from your last working day 
            and credited to your registered bank account.</p>
            
            <p>If you have any queries regarding this settlement, please contact the HR department within 
            7 days of receiving this statement.</p>
            
            <p>We wish you all the best in your future endeavors.</p>
            
            <p>Best Regards,<br>
            Team HR<br>
            Rapid Innovation</p>
            """
            
            email_data = {
                'to_email': employee.email_personal,
                'cc_emails': [config.DEFAULT_SENDER_EMAIL],
                'subject': subject,
                'body_html': body_html,
                'body_text': self.email_sender._html_to_text(body_html),
                'attachments': [{
                    'file_path': pdf_path,
                    'file_name': os.path.basename(pdf_path)
                }]
            }
            
            result = self.email_sender.send_email(email_data)
            
            if result['success']:
                # Log email
                self.email_sender.log_email(
                    employee_id=employee.id,
                    email_data={
                        'email_type': 'fnf_statement',
                        'to_email': employee.email_personal,
                        'subject': subject
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending FnF letter email: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending email: {str(e)}'
            }
    
    def mark_fnf_processed(self, employee_id: int, payment_details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mark FnF as processed after payment"""
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
                
                checklist.fnf_processed = True
                checklist.fnf_processed_date = datetime.utcnow()
                
                if payment_details:
                    checklist.notes = f"FnF Payment Details: {payment_details}"
                
                session.commit()
                
                logger.info(f"FnF marked as processed for employee ID {employee_id}")
                
                return {
                    'success': True,
                    'message': 'FnF marked as processed'
                }
                
        except Exception as e:
            logger.error(f"Error marking FnF as processed: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }