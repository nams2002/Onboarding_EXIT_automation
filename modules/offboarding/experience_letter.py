import os
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from database.connection import get_db_session
from database.models import Employee, OffboardingChecklist, EmployeeType
from modules.email.email_Sender import EmailSender
from config import config
from utils.helpers import format_date

logger = logging.getLogger(__name__)

class ExperienceLetterGenerator:
    """Generate experience letters and internship certificates"""
    
    def __init__(self):
        self.email_sender = EmailSender()
        
        # Create output directory
        self.output_dir = os.path.join(config.UPLOAD_FOLDER, 'experience_letters')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_experience_letter(self, employee_id: int, dues_settled: bool = True) -> Dict[str, Any]:
        """Generate experience letter or internship certificate"""
        try:
            with get_db_session() as session:
                # Get employee
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Check if employee has exited
                if employee.status.value not in ['offboarding', 'exited']:
                    return {
                        'success': False,
                        'message': 'Experience letter can only be generated for exited employees'
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
                
                # Check prerequisites based on employee type
                if employee.employee_type == EmployeeType.FULL_TIME:
                    # For full-time employees, check FnF and assets
                    if not dues_settled and (not checklist.fnf_processed or not checklist.assets_returned):
                        return {
                            'success': False,
                            'message': 'All dues must be settled before generating experience letter'
                        }
                
                # Prepare template data
                template_data = self._prepare_experience_data(employee, checklist, dues_settled)
                
                # Generate PDF
                if employee.employee_type == EmployeeType.INTERN:
                    pdf_path = self._generate_internship_certificate(employee, template_data)
                else:
                    pdf_path = self._generate_experience_letter_pdf(employee, template_data, dues_settled)
                
                if not pdf_path:
                    return {
                        'success': False,
                        'message': 'Failed to generate experience letter PDF'
                    }
                
                # Update offboarding checklist
                checklist.experience_letter_issued = True
                checklist.experience_letter_date = datetime.utcnow()
                session.commit()
                
                # Send experience letter email
                email_result = self._send_experience_letter_email(employee, pdf_path)
                
                if email_result['success']:
                    logger.info(f"Experience letter generated and sent for employee {employee.employee_id}")
                    
                    return {
                        'success': True,
                        'message': 'Experience letter generated and sent successfully',
                        'pdf_path': pdf_path
                    }
                else:
                    return {
                        'success': True,
                        'message': 'Experience letter generated but email failed',
                        'pdf_path': pdf_path
                    }
                
        except Exception as e:
            logger.error(f"Error generating experience letter: {str(e)}")
            return {
                'success': False,
                'message': f'Error generating experience letter: {str(e)}'
            }
    
    def _prepare_experience_data(self, employee: Employee, checklist: OffboardingChecklist, 
                                dues_settled: bool) -> Dict[str, Any]:
        """Prepare data for experience letter template"""
        # Calculate tenure
        start_date = employee.date_of_joining
        end_date = checklist.last_working_day or date.today()
        
        # Format dates
        joining_date = format_date(start_date)
        leaving_date = format_date(end_date)
        
        # Calculate years and months of service
        total_days = (end_date - start_date).days
        years = total_days // 365
        months = (total_days % 365) // 30
        
        tenure_text = ""
        if years > 0:
            tenure_text = f"{years} year{'s' if years > 1 else ''}"
        if months > 0:
            if tenure_text:
                tenure_text += f" and {months} month{'s' if months > 1 else ''}"
            else:
                tenure_text = f"{months} month{'s' if months > 1 else ''}"
        
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
            'joining_date': joining_date,
            'leaving_date': leaving_date,
            'tenure_text': tenure_text,
            'gender_pronoun': 'his',  # Default, should be determined from employee data
            'gender_pronoun_cap': 'His',
            'gender_subject': 'he',
            'gender_subject_cap': 'He',
            'dues_settled': dues_settled
        }
        
        # Add internship-specific data
        if employee.employee_type == EmployeeType.INTERN:
            template_data['internship_duration'] = tenure_text
            template_data['project_details'] = checklist.notes or "various projects"
        
        return template_data
    
    def _generate_experience_letter_pdf(self, employee: Employee, template_data: Dict[str, Any], 
                                       dues_settled: bool) -> Optional[str]:
        """Generate PDF experience letter for full-time employees and contractors"""
        try:
            # Create filename
            filename = f"experience_letter_{employee.employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leading=16
            )
            
            # Add company logo if exists
            logo_path = os.path.join('static', 'images', 'company_logo.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=2*inch, height=0.75*inch)
                elements.append(logo)
                elements.append(Spacer(1, 20))
            
            # Title
            elements.append(Paragraph("EXPERIENCE CERTIFICATE", title_style))
            elements.append(Spacer(1, 30))
            
            # Date
            elements.append(Paragraph(f"Date: {template_data['issue_date']}", normal_style))
            elements.append(Spacer(1, 30))
            
            # TO WHOMSOEVER IT MAY CONCERN
            elements.append(Paragraph("<b>TO WHOMSOEVER IT MAY CONCERN</b>", normal_style))
            elements.append(Spacer(1, 20))
            
            # Main content
            if employee.employee_type == EmployeeType.FULL_TIME:
                content = f"""
                This is to certify that <b>Mr/Ms. {template_data['employee_name']}</b> worked as the 
                <b>{template_data['designation']}</b> with <b>{template_data['company_name']}</b> from 
                <b>{template_data['joining_date']}</b> to <b>{template_data['leaving_date']}</b>.
                """
            else:  # Contractor
                content = f"""
                This is to certify that <b>Mr/Ms. {template_data['employee_name']}</b> worked as a 
                <b>{template_data['designation']} (Contractor)</b> with <b>{template_data['company_name']}</b> 
                from <b>{template_data['joining_date']}</b> to <b>{template_data['leaving_date']}</b>.
                """
            
            elements.append(Paragraph(content, normal_style))
            elements.append(Spacer(1, 20))
            
            # Performance statement
            performance = f"""
            During {template_data['gender_pronoun']} employment with Rapid Innovation, we found 
            {template_data['gender_pronoun']} performance to be satisfactory.
            """
            elements.append(Paragraph(performance, normal_style))
            elements.append(Spacer(1, 20))
            
            # Dues statement
            if dues_settled:
                dues_text = "All dues are settled."
            else:
                dues_text = "All dues are not settled."
            
            elements.append(Paragraph(dues_text, normal_style))
            elements.append(Spacer(1, 20))
            
            # Wishes
            wishes = f"""
            We wish {template_data['gender_pronoun']} success in {template_data['gender_pronoun']} 
            future endeavors.
            """
            elements.append(Paragraph(wishes, normal_style))
            elements.append(Spacer(1, 40))
            
            # Closing
            elements.append(Paragraph("Sincerely,", normal_style))
            elements.append(Spacer(1, 60))
            
            # Signature
            elements.append(Paragraph(template_data['hr_manager_name'], normal_style))
            elements.append(Paragraph(template_data['hr_manager_designation'], normal_style))
            
            # Build PDF
            doc.build(elements)
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating experience letter PDF: {str(e)}")
            return None
    
    def _generate_internship_certificate(self, employee: Employee, template_data: Dict[str, Any]) -> Optional[str]:
        """Generate PDF internship certificate"""
        try:
            # Create filename
            filename = f"internship_certificate_{employee.employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
                fontSize=18,
                textColor=colors.HexColor('#0066CC'),
                alignment=TA_CENTER,
                spaceAfter=40
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leading=16
            )
            
            # Add company logo if exists
            logo_path = os.path.join('static', 'images', 'company_logo.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=2*inch, height=0.75*inch)
                elements.append(logo)
                elements.append(Spacer(1, 20))
            
            # Title
            elements.append(Paragraph("INTERNSHIP CERTIFICATE", title_style))
            elements.append(Spacer(1, 30))
            
            # Date
            elements.append(Paragraph(f"Date: {template_data['issue_date']}", normal_style))
            elements.append(Spacer(1, 30))
            
            # TO WHOMSOEVER IT MAY CONCERN
            elements.append(Paragraph("<b>To Whom It May Concern</b>", normal_style))
            elements.append(Spacer(1, 20))
            
            # Main content
            content = f"""
            This letter is to certify that <b>Mr/Ms. {template_data['employee_name']}</b> has completed 
            {template_data['gender_pronoun']} internship with <b>{template_data['company_name']}</b>. 
            {template_data['gender_subject_cap']} internship tenure was from <b>{template_data['joining_date']}</b> 
            to <b>{template_data['leaving_date']}</b>. {template_data['gender_subject_cap']} was working with us 
            as an <b>{template_data['designation']}</b> and was actively & diligently involved in the projects 
            and tasks assigned to {template_data['gender_pronoun']}.
            """
            
            elements.append(Paragraph(content, normal_style))
            elements.append(Spacer(1, 20))
            
            # Performance statement
            performance = f"""
            During this time, we found {template_data['gender_pronoun']} to be punctual and hardworking.
            """
            elements.append(Paragraph(performance, normal_style))
            elements.append(Spacer(1, 20))
            
            # Wishes
            wishes = f"""
            We wish {template_data['gender_pronoun']} a bright future.
            """
            elements.append(Paragraph(wishes, normal_style))
            elements.append(Spacer(1, 40))
            
            # Closing
            elements.append(Paragraph("Sincerely,", normal_style))
            elements.append(Spacer(1, 60))
            
            # Signature
            elements.append(Paragraph(template_data['hr_manager_name'], normal_style))
            elements.append(Paragraph(template_data['hr_manager_designation'], normal_style))
            
            # Build PDF
            doc.build(elements)
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating internship certificate PDF: {str(e)}")
            return None
    
    def _send_experience_letter_email(self, employee: Employee, pdf_path: str) -> Dict[str, Any]:
        """Send experience letter email with PDF attachment"""
        try:
            # Determine email subject based on employee type
            if employee.employee_type == EmployeeType.INTERN:
                subject = f"Rapid Innovation - Internship Certificate - {employee.full_name}"
                doc_type = "Internship Certificate"
            else:
                subject = f"Rapid Innovation - Experience Letter - {employee.full_name}"
                doc_type = "Experience Letter"
            
            body_html = f"""
            <p>Hi {employee.full_name},</p>
            
            <p>I hope you are doing well.</p>
            
            <p>PFA: {doc_type}</p>
            
            <p>Kindly reach out to us if you have any other concerns.</p>
            
            <p>Regards<br>
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
                        'email_type': 'experience_letter',
                        'to_email': employee.email_personal,
                        'subject': subject
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending experience letter email: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending email: {str(e)}'
            }