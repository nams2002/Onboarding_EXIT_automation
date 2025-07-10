import os
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from database.connection import get_db_session
from database.models import Employee, OnboardingChecklist, EmployeeType
from modules.email.email_Sender import EmailSender
from config import config
from utils.helpers import format_date, format_currency

logger = logging.getLogger(__name__)

class AppointmentLetterGenerator:
    """Generate appointment letters for employees"""
    
    def __init__(self):
        self.email_sender = EmailSender()
        
        # Create output directory
        self.output_dir = os.path.join(config.UPLOAD_FOLDER, 'appointment_letters')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_appointment_letter(self, employee_id: int) -> Dict[str, Any]:
        """Generate appointment letter for a full-time employee"""
        try:
            with get_db_session() as session:
                # Get employee
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Appointment letters are only for full-time employees
                if employee.employee_type != EmployeeType.FULL_TIME:
                    return {
                        'success': False,
                        'message': 'Appointment letters are only for full-time employees'
                    }
                
                # Check if offer letter is signed
                checklist = session.query(OnboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if not checklist or not checklist.offer_letter_signed:
                    return {
                        'success': False,
                        'message': 'Offer letter must be signed before generating appointment letter'
                    }
                
                # Prepare template data
                template_data = self._prepare_appointment_data(employee)
                
                # Generate PDF
                pdf_path = self._generate_appointment_pdf(employee, template_data)
                
                if not pdf_path:
                    return {
                        'success': False,
                        'message': 'Failed to generate appointment letter PDF'
                    }
                
                # Update onboarding checklist
                checklist.appointment_letter_sent = True
                checklist.appointment_sent_date = datetime.utcnow()
                session.commit()
                
                # Send appointment letter email
                email_result = self._send_appointment_letter_email(employee, pdf_path)
                
                if email_result['success']:
                    logger.info(f"Appointment letter generated and sent for employee {employee.employee_id}")
                    
                    return {
                        'success': True,
                        'message': 'Appointment letter generated and sent successfully',
                        'pdf_path': pdf_path
                    }
                else:
                    return {
                        'success': True,
                        'message': 'Appointment letter generated but email failed',
                        'pdf_path': pdf_path
                    }
                
        except Exception as e:
            logger.error(f"Error generating appointment letter: {str(e)}")
            return {
                'success': False,
                'message': f'Error generating appointment letter: {str(e)}'
            }
    
    def _prepare_appointment_data(self, employee: Employee) -> Dict[str, Any]:
        """Prepare data for appointment letter template"""
        template_data = {
            'company_name': config.COMPANY_NAME,
            'company_address': config.COMPANY_ADDRESS,
            'hr_manager_name': config.HR_MANAGER_NAME,
            'hr_manager_designation': config.HR_MANAGER_DESIGNATION,
            'issue_date': format_date(date.today()),
            'employee_name': employee.full_name,
            'employee_address': employee.address or 'To be provided',
            'employee_id': employee.employee_id,
            'designation': employee.designation,
            'department': employee.department,
            'reporting_manager': employee.reporting_manager,
            'date_of_joining': format_date(employee.date_of_joining),
            'probation_period': config.PROBATION_PERIOD.get('full_time', 3),
            'notice_period_probation': config.NOTICE_PERIOD['full_time']['probation'],
            'notice_period_confirmed': config.NOTICE_PERIOD['full_time']['confirmed']
        }
        
        return template_data
    
    def _generate_appointment_pdf(self, employee: Employee, template_data: Dict[str, Any]) -> Optional[str]:
        """Generate PDF appointment letter"""
        try:
            # Create filename
            filename = f"appointment_letter_{employee.employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_path = os.path.join(self.output_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
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
                spaceAfter=12,
                keepWithNext=True
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leading=14
            )
            
            # Add company logo if exists
            logo_path = os.path.join('static', 'images', 'company_logo.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=2*inch, height=0.75*inch)
                elements.append(logo)
                elements.append(Spacer(1, 20))
            
            # Title
            elements.append(Paragraph("APPOINTMENT LETTER", title_style))
            elements.append(Spacer(1, 20))
            
            # Date
            elements.append(Paragraph(f"Date: {template_data['issue_date']}", normal_style))
            elements.append(Spacer(1, 20))
            
            # Address
            elements.append(Paragraph(f"<b>{template_data['employee_name']}</b>", normal_style))
            elements.append(Paragraph(template_data['employee_address'], normal_style))
            elements.append(Spacer(1, 20))
            
            # Subject
            elements.append(Paragraph("<b>Subject: Appointment Letter</b>", normal_style))
            elements.append(Spacer(1, 20))
            
            # Salutation
            elements.append(Paragraph(f"Dear {template_data['employee_name'].split()[0]},", normal_style))
            elements.append(Spacer(1, 12))
            
            # Opening paragraph
            opening = f"""
            With reference to your application and the subsequent interview you had with us, we are pleased 
            to appoint you to the position of <b>"{template_data['designation']}"</b> at Rapid Innovation.
            """
            elements.append(Paragraph(opening, normal_style))
            elements.append(Spacer(1, 12))
            
            # Joining details
            joining = f"""
            You joined our organization on <b>{template_data['date_of_joining']}</b>. Following are the 
            Terms & Conditions which have to be followed by all our employees. Acceptance and Acknowledgment 
            by you of this appointment letter will make this a formal contract of employment between you and 
            the company.
            """
            elements.append(Paragraph(joining, normal_style))
            elements.append(Spacer(1, 20))
            
            # Terms and Conditions
            elements.append(Paragraph("<b>TERMS AND CONDITIONS OF EMPLOYMENT</b>", heading_style))
            
            # Terms list
            terms = [
                f"""You undertake to perform functions in relation to "{template_data['designation']}" for the 
                Company and agree to perform such duties and carry out such functions, as may be assigned/entrusted 
                to you by the board of directors and the management of the Company or any other person appointed 
                by the board of directors/management of the Company on that behalf.""",
                
                """All employees are required to comply with company policies/guidelines, which shall be 
                communicated by the Company verbally and in writing during the course of their employment 
                with the Company.""",
                
                f"""From the date of your joining service in Rapid Innovation (hereinafter referred to as 
                'Company') you will be included in the full time roles of the Company.""",
                
                """During the term of your employment with the Company, you may not engage in any employment 
                or act in any way, which either conflicts with your duties and obligations to the Company, 
                or is contrary to the policies or the interests of the Company.""",
                
                f"""<b>Probation:</b> You shall be on probation for a period of {template_data['probation_period']} 
                months initially. The period of probation may be further extended on the sole discretion of 
                the Company. Your confirmation will be subject to your conduct and work being satisfactory 
                during this period.""",
                
                """<b>Leave:</b> You will be entitled for leave as per the category and level of your 
                employment as defined in the leave policy.""",
                
                """<b>Transfer of Services:</b> The Company may, at its sole discretion, transfer you to 
                any other office of the Company in India or overseas or to any of its affiliates as long 
                as the benefit of your employment accrues to the Company.""",
                
                """<b>Group Medical:</b> Group medical insurance scheme covers you and your family 
                (Spouse & 02 Children). Maximum members allowed for coverage is 4.""",
                
                """<b>Confidentiality:</b> You shall not at any time or times without the consent of the 
                Company either during the term of employment or thereafter disclose, divulge or make public 
                any confidential information of the Company.""",
                
                f"""<b>Notice Period:</b> Your employment with the company shall be governed by Company's 
                rules and regulations applicable from time to time. You will be required to give 
                {template_data['notice_period_confirmed']} days of notice if you wish to resign from the 
                employment of the company after getting confirmed. During probation, the notice period 
                will be {template_data['notice_period_probation']} days.""",
                
                """<b>Termination:</b> The company keeps the rights to decide in case of termination if 
                it is in the favor of 30 days of notice period or 30 days of salary in lieu of notice period.""",
                
                """You agree that during and upon termination of your employment, you shall not in any 
                manner either directly or indirectly solicit or entice the other employees or customers 
                of the Company.""",
                
                """You acknowledge and agree that any work that you may be conducting either on the premises 
                of the Company or otherwise with regard to patents, improvements, discoveries or any other 
                form of intellectual property, is being done on behalf of the Company.""",
                
                """You shall execute a Non-Disclosure Agreement under which you will have an obligation 
                to keep confidential the Company's proprietary information.""",
                
                """You agree that the interpretation and enforcement of this Agreement shall be governed 
                by the laws of India and all disputes under this Agreement shall be governed by the 
                provisions of the Indian Arbitration and Conciliation Act, 1996."""
            ]
            
            for i, term in enumerate(terms, 1):
                bullet_text = f"<b>{i}.</b> {term}"
                elements.append(Paragraph(bullet_text, normal_style))
            
            elements.append(Spacer(1, 20))
            
            # Employee Proprietary Agreement
            elements.append(PageBreak())
            elements.append(Paragraph("<b>EMPLOYEE PROPRIETARY INFORMATION, INVENTIONS, NON-COMPETITION AND NON-SOLICITATION AGREEMENT</b>", heading_style))
            
            proprietary_text = """
            In consideration of my employment or continued employment by Rapid Innovation (the "Company") 
            and the compensation now and hereafter paid to me, I hereby enter into this Proprietary 
            Information, Inventions, Non-Competition and Non-Solicitation Agreement (the "Agreement") 
            and agree to the terms outlined in the attached annexure.
            """
            elements.append(Paragraph(proprietary_text, normal_style))
            elements.append(Spacer(1, 20))
            
            # Non-compete section
            elements.append(Paragraph("<b>NON-COMPETE PROVISION</b>", heading_style))
            non_compete = """
            I agree that for the one (1) year period after the date my employment ends for any reason, 
            including but not limited to voluntary termination by me or involuntary termination by the 
            Company, I will not, directly or indirectly, as an officer, director, employee, consultant, 
            owner, partner, or in any other capacity solicit, provide, or attempt to provide Conflicting 
            Services anywhere in the United States, nor will I assist another person to solicit, attempt 
            to provide, or provide Conflicting Services anywhere in the United States.
            """
            elements.append(Paragraph(non_compete, normal_style))
            elements.append(Spacer(1, 20))
            
            # Penalty clause
            elements.append(Paragraph("<b>PENALTY CLAUSE:</b>", heading_style))
            penalty = """
            In case of a breach of an agreement state that the defaulter will be terminated with an immediate effect.
            """
            elements.append(Paragraph(penalty, normal_style))
            elements.append(Spacer(1, 20))
            
            # Acknowledgment
            acknowledgment = """
            This is to certify that I have read this agreement and all Annexure and understood all the 
            terms and conditions mentioned therein and I hereby accept and agree to abide by them.
            """
            elements.append(Paragraph(acknowledgment, normal_style))
            elements.append(Spacer(1, 30))
            
            # Effective date
            elements.append(Paragraph(f"This Agreement shall be effective as of the first day of my employment with the Company, namely: {template_data['date_of_joining']}", normal_style))
            elements.append(Spacer(1, 30))
            
            # Signature section
            signature_data = [
                ['ACCEPTED AND AGREED TO:', '', 'For Rapid Innovation'],
                ['', '', ''],
                ['', '', ''],
                ['_____________________', '', '_____________________'],
                [template_data['employee_name'], '', template_data['hr_manager_name']],
                ['(Signature of Employee)', '', template_data['hr_manager_designation']],
                ['', '', ''],
                ['Date: _____________', '', 'Date: _____________']
            ]
            
            signature_table = Table(signature_data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
            signature_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            
            elements.append(signature_table)
            
            # Build PDF
            doc.build(elements)
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating appointment letter PDF: {str(e)}")
            return None
    
    def _send_appointment_letter_email(self, employee: Employee, pdf_path: str) -> Dict[str, Any]:
        """Send appointment letter email with PDF attachment"""
        try:
            subject = f"Appointment Letter - {employee.full_name} - {employee.designation}"
            
            body_html = f"""
            <p>Hi {employee.full_name},</p>
            
            <p>Hope you are well !!</p>
            
            <p>Please find the attached Appointment Letter. Kindly go through the same & share a 
            signed copy with us.</p>
            
            <p>Please reach us in case of any queries.</p>
            
            <p>Thanks & Regards<br>
            Team HR<br>
            Rapid Innovation</p>
            """
            
            email_data = {
                'to_email': employee.email_official or employee.email_personal,
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
                        'email_type': 'appointment_letter',
                        'to_email': email_data['to_email'],
                        'subject': subject
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending appointment letter email: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending email: {str(e)}'
            }
    
    def mark_appointment_letter_signed(self, employee_id: int, signed_pdf_path: str = None) -> Dict[str, Any]:
        """Mark appointment letter as signed"""
        try:
            with get_db_session() as session:
                checklist = session.query(OnboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                
                if not checklist:
                    return {
                        'success': False,
                        'message': 'Onboarding checklist not found'
                    }
                
                checklist.appointment_letter_signed = True
                checklist.appointment_signed_date = datetime.utcnow()
                
                # TODO: Store signed PDF path if provided
                
                session.commit()
                
                logger.info(f"Appointment letter marked as signed for employee ID {employee_id}")
                
                return {
                    'success': True,
                    'message': 'Appointment letter marked as signed'
                }
                
        except Exception as e:
            logger.error(f"Error marking appointment letter as signed: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }