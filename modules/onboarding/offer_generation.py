import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from database.connection import get_db_session
from database.models import Employee, OnboardingChecklist, LetterTemplate, EmployeeType
from modules.email.email_Sender import EmailSender
from config import config
from utils.helpers import calculate_ctc_breakdown, format_currency, format_date

logger = logging.getLogger(__name__)

class OfferGenerator:
    """Generate and manage offer letters"""
    
    def __init__(self):
        self.email_sender = EmailSender()
        self.template_env = Environment(
            loader=FileSystemLoader(config.LETTER_TEMPLATE_FOLDER),
            autoescape=True
        )
        
        # Create output directory
        self.output_dir = os.path.join(config.UPLOAD_FOLDER, 'offer_letters')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_offer_letter(self, employee_id: int, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate offer letter for an employee"""
        try:
            with get_db_session() as session:
                # Get employee
                employee = session.query(Employee).filter_by(id=employee_id).first()
                if not employee:
                    return {
                        'success': False,
                        'message': 'Employee not found'
                    }
                
                # Prepare template data
                template_data = self._prepare_offer_data(employee, offer_data)
                
                # Generate PDF
                pdf_path = self._generate_offer_pdf(employee, template_data)
                
                if not pdf_path:
                    return {
                        'success': False,
                        'message': 'Failed to generate offer letter PDF'
                    }
                
                # Update onboarding checklist
                checklist = session.query(OnboardingChecklist).filter_by(
                    employee_id=employee_id
                ).first()
                if checklist:
                    checklist.offer_letter_sent = True
                    checklist.offer_sent_date = datetime.utcnow()
                    session.commit()
                
                # Send offer letter email
                email_result = self._send_offer_letter_email(employee, pdf_path, template_data)

                if email_result['success']:
                    logger.info(f"Offer letter generated and sent for employee {employee.employee_id}")

                    return {
                        'success': True,
                        'message': 'Offer letter generated and sent successfully',
                        'pdf_path': pdf_path
                    }
                else:
                    return {
                        'success': True,
                        'message': 'Offer letter generated but email failed',
                        'pdf_path': pdf_path
                    }
                
        except Exception as e:
            logger.error(f"Error generating offer letter: {str(e)}")
            return {
                'success': False,
                'message': f'Error generating offer letter: {str(e)}'
            }
    
    def _prepare_offer_data(self, employee: Employee, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for offer letter template"""
        template_data = {
            'company_name': config.COMPANY_NAME,
            'company_address': config.COMPANY_ADDRESS,
            'hr_manager_name': config.HR_MANAGER_NAME,
            'hr_manager_designation': config.HR_MANAGER_DESIGNATION,
            'issue_date': format_date(date.today()),
            'employee_name': employee.full_name,
            'employee_address': employee.address or 'To be provided',
            'designation': employee.designation,
            'department': employee.department,
            'reporting_manager': employee.reporting_manager,
            'date_of_joining': format_date(employee.date_of_joining),
            'employee_type': config.EMPLOYEE_TYPES[employee.employee_type.value],
            'probation_period': config.PROBATION_PERIOD.get(employee.employee_type.value, 3),
            'work_location': 'Remote',
            'working_hours': '9:00 AM to 6:00 PM IST',
            'working_days': 'Monday to Friday'
        }
        
        # Add compensation details based on employee type
        if employee.employee_type == EmployeeType.FULL_TIME:
            ctc = offer_data.get('ctc', employee.ctc or 0)
            template_data['ctc'] = format_currency(ctc)
            template_data['ctc_words'] = self._number_to_words(ctc)
            
            # Calculate CTC breakdown
            ctc_breakdown = calculate_ctc_breakdown(ctc)
            template_data.update({
                'basic_salary': format_currency(ctc_breakdown['basic_salary']),
                'hra': format_currency(ctc_breakdown['hra']),
                'special_allowance': format_currency(ctc_breakdown['special_allowance']),
                'medical_allowance': format_currency(ctc_breakdown['medical_allowance']),
                'books_periodical': format_currency(ctc_breakdown['books_periodical']),
                'health_club': format_currency(ctc_breakdown['health_club']),
                'internet_telephone': format_currency(ctc_breakdown['internet_telephone']),
                'pf_employer': format_currency(ctc_breakdown['pf_employer']),
                'gross_ctc': format_currency(ctc_breakdown['gross_ctc']),
                'total_ctc': format_currency(ctc_breakdown['total_ctc'])
            })
            
            # Monthly amounts
            template_data['monthly_gross'] = format_currency(ctc_breakdown['gross_ctc'] / 12)
            template_data['monthly_basic'] = format_currency(ctc_breakdown['basic_salary'] / 12)
            
        elif employee.employee_type == EmployeeType.INTERN:
            stipend = offer_data.get('stipend', employee.stipend or 0)
            template_data['stipend'] = format_currency(stipend)
            template_data['internship_duration'] = offer_data.get('duration', '6 months')
            
        else:  # Contractor
            hourly_rate = offer_data.get('hourly_rate', employee.hourly_rate or 0)
            template_data['hourly_rate'] = format_currency(hourly_rate)
            template_data['expected_hours'] = offer_data.get('expected_hours', '8 hours per day')
            template_data['billing_cycle'] = 'Monthly'
        
        # Add custom data from offer_data
        template_data.update(offer_data.get('custom_data', {}))
        
        return template_data
    
    def _generate_offer_pdf(self, employee: Employee, template_data: Dict[str, Any]) -> Optional[str]:
        """Generate PDF offer letter"""
        try:
            # Create filename
            filename = f"offer_letter_{employee.employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
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
                spaceAfter=12
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceAfter=12
            )
            
            # Add company logo if exists
            logo_path = os.path.join('static', 'images', 'company_logo.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=2*inch, height=0.75*inch)
                elements.append(logo)
                elements.append(Spacer(1, 20))
            
            # Title
            if employee.employee_type == EmployeeType.FULL_TIME:
                title = "OFFER LETTER"
            elif employee.employee_type == EmployeeType.INTERN:
                title = "INTERNSHIP LETTER"
            else:
                title = "CONTRACT AGREEMENT"
            
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 20))
            
            # Date and reference
            elements.append(Paragraph(f"<b>Date:</b> {template_data['issue_date']}", normal_style))
            elements.append(Paragraph(f"<b>Ref:</b> RI/HR/{employee.employee_id}/2024", normal_style))
            elements.append(Spacer(1, 20))
            
            # Address
            elements.append(Paragraph(f"<b>{template_data['employee_name']}</b>", normal_style))
            elements.append(Paragraph(template_data['employee_address'], normal_style))
            elements.append(Spacer(1, 20))
            
            # Subject line
            subject = f"<b>Sub: {title} - {template_data['designation']}</b>"
            elements.append(Paragraph(subject, normal_style))
            elements.append(Spacer(1, 20))
            
            # Salutation
            elements.append(Paragraph(f"Dear {template_data['employee_name'].split()[0]},", normal_style))
            elements.append(Spacer(1, 12))
            
            # Opening paragraph
            if employee.employee_type == EmployeeType.FULL_TIME:
                opening = f"""
                With reference to your application and subsequent discussion/interview, we are pleased to 
                offer you the position of <b>{template_data['designation']}</b>. You are expected to join 
                on <b>{template_data['date_of_joining']}</b> on or before.
                """
            elif employee.employee_type == EmployeeType.INTERN:
                opening = f"""
                With reference to your application and subsequent discussion/interview, we are pleased to 
                offer you the position of <b>{template_data['designation']}</b>. You are expected to join 
                on <b>{template_data['date_of_joining']}</b>.
                """
            else:
                opening = f"""
                This Contract Agreement is by and between {template_data['employee_name']} and 
                {config.COMPANY_NAME} and defines the scope of work and fees for services to be performed.
                """
            
            elements.append(Paragraph(opening, normal_style))
            elements.append(Spacer(1, 20))
            
            # Employment details
            elements.append(Paragraph("<b>EMPLOYMENT DETAILS</b>", heading_style))
            
            # Create employment details table
            employment_data = [
                ['Position:', template_data['designation']],
                ['Department:', template_data['department']],
                ['Reporting To:', template_data['reporting_manager']],
                ['Date of Joining:', template_data['date_of_joining']],
                ['Work Location:', template_data['work_location']],
                ['Employment Type:', template_data['employee_type']]
            ]
            
            if employee.employee_type == EmployeeType.FULL_TIME:
                employment_data.append(['Probation Period:', f"{template_data['probation_period']} months"])
            
            employment_table = Table(employment_data, colWidths=[2*inch, 4*inch])
            employment_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            elements.append(employment_table)
            elements.append(Spacer(1, 20))
            
            # Compensation details
            if employee.employee_type == EmployeeType.FULL_TIME:
                elements.append(Paragraph("<b>COMPENSATION DETAILS</b>", heading_style))
                elements.append(Paragraph(
                    f"Your CTC (Cost-to-Company) will be <b>{template_data['ctc']} ({template_data['ctc_words']})</b> per annum.",
                    normal_style
                ))
                elements.append(Spacer(1, 12))
                
                # CTC breakdown table
                ctc_data = [
                    ['Component', 'Monthly (₹)', 'Annual (₹)'],
                    ['Basic Salary', template_data['monthly_basic'], template_data['basic_salary']],
                    ['HRA', format_currency(float(template_data['hra'].replace('₹', '').replace(',', '')) / 12), template_data['hra']],
                    ['Special Allowance', format_currency(float(template_data['special_allowance'].replace('₹', '').replace(',', '')) / 12), template_data['special_allowance']],
                    ['Medical Allowance', format_currency(15000 / 12), template_data['medical_allowance']],
                    ['Books & Periodicals', format_currency(12000 / 12), template_data['books_periodical']],
                    ['Health Club Facility', format_currency(6000 / 12), template_data['health_club']],
                    ['Internet & Telephone', format_currency(24000 / 12), template_data['internet_telephone']],
                    ['', '', ''],
                    ['Gross CTC', template_data['monthly_gross'], template_data['gross_ctc']],
                    ['PF Employer Contribution', format_currency(float(template_data['pf_employer'].replace('₹', '').replace(',', '')) / 12), template_data['pf_employer']],
                    ['', '', ''],
                    ['Total CTC', '', template_data['total_ctc']]
                ]
                
                ctc_table = Table(ctc_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
                ctc_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0, 0.4, 0.8, 0.2)),
                    ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0, 0.4, 0.8, 0.2)),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                
                elements.append(ctc_table)
                elements.append(Spacer(1, 20))
                
            elif employee.employee_type == EmployeeType.INTERN:
                elements.append(Paragraph("<b>STIPEND DETAILS</b>", heading_style))
                elements.append(Paragraph(
                    f"It will be <b>{template_data['internship_duration']} of Internship</b> starting from your date of joining, "
                    f"and the stipend will be <b>{template_data['stipend']}</b> per month.",
                    normal_style
                ))
                elements.append(Spacer(1, 20))
                
            else:  # Contractor
                elements.append(Paragraph("<b>COMPENSATION DETAILS</b>", heading_style))
                elements.append(Paragraph(
                    f"Regarding your compensation, you will be paid on Hourly basis <b>{template_data['hourly_rate']}</b>, "
                    f"which reflects our acknowledgment of your valuable contributions to the team.",
                    normal_style
                ))
                elements.append(Spacer(1, 20))
            
            # Terms and conditions
            elements.append(Paragraph("<b>TERMS AND CONDITIONS</b>", heading_style))
            
            # Add relevant terms based on employee type
            terms = self._get_terms_and_conditions(employee.employee_type)
            for i, term in enumerate(terms, 1):
                elements.append(Paragraph(f"{i}. {term}", normal_style))
            
            elements.append(Spacer(1, 20))
            
            # Closing
            closing = """
            We are confident that you will be able to make a significant contribution to the success of our Company.
            <br/><br/>
            Please sign and share the scanned copy of this letter and return it to the HR Department to indicate 
            your acceptance of this offer.
            """
            elements.append(Paragraph(closing, normal_style))
            elements.append(Spacer(1, 30))
            
            # Signature section
            elements.append(Paragraph("Sincerely,", normal_style))
            elements.append(Spacer(1, 40))
            
            signature_data = [
                [template_data['hr_manager_name'], '', 'Accepted By'],
                [template_data['hr_manager_designation'], '', template_data['employee_name']],
                ['', '', ''],
                ['Date: _____________', '', 'Date: _____________']
            ]
            
            signature_table = Table(signature_data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
            signature_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            elements.append(signature_table)
            
            # Build PDF
            doc.build(elements)
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return None
    
    def _get_terms_and_conditions(self, employee_type: EmployeeType) -> list:
        """Get terms and conditions based on employee type"""
        common_terms = [
            "This position is designated as remote until further notified by the management.",
            "You undertake to perform functions in relation to your position and agree to perform such duties as may be assigned to you.",
            "All employees are required to comply with company policies/guidelines.",
            "During the term of your employment, you may not engage in any employment or act in any way which conflicts with your duties.",
            "Any change in your personal information should be notified to the Company in writing within seven (7) days.",
            "Confidentiality: You shall not disclose any confidential information of the Company.",
        ]
        
        if employee_type == EmployeeType.FULL_TIME:
            specific_terms = [
                f"You will be on probation for a period of {config.PROBATION_PERIOD['full_time']} months initially.",
                f"Notice Period: {config.NOTICE_PERIOD['full_time']['confirmed']} days after confirmation, {config.NOTICE_PERIOD['full_time']['probation']} days during probation.",
                "You will be entitled for leave as per the company leave policy.",
                "Group medical insurance scheme covers you and your family (Spouse & 02 Children).",
                "The Company shall withhold taxes as required under applicable laws.",
            ]
        elif employee_type == EmployeeType.INTERN:
            specific_terms = [
                "We will assess your performance for the initial 15 days.",
                "After the internship tenure, we will judge your performance for a full-time position.",
                f"Notice Period: {config.NOTICE_PERIOD['intern']} days if you wish to resign.",
                "You will be using your laptop for the duration of the internship.",
                "Please ensure that you have a stable network connection and uninterrupted power supply.",
            ]
        else:  # Contractor
            specific_terms = [
                f"Notice Period: If either party decides to terminate the contract, a {config.NOTICE_PERIOD['contractor']}-day notice period is required.",
                "The number of hours worked will be recorded on our company software.",
                "Payment will be done on a monthly basis as per your activity on software.",
                "During your tenure as a Contractor, you are not eligible for leaves.",
                f"The company will be deducting tax @ {config.TDS_PERCENTAGE}% as per section 194J of the Income Tax Act.",
            ]
        
        return common_terms + specific_terms
    
    def _send_offer_letter_email(self, employee: Employee, pdf_path: str, 
                                template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send offer letter email with PDF attachment"""
        try:
            # Determine email template based on employee type
            if employee.employee_type == EmployeeType.FULL_TIME:
                subject = f"Rapid Innovation - Offer letter - {employee.designation}"
                email_type = "offer_letter"
            elif employee.employee_type == EmployeeType.INTERN:
                subject = f"Rapid Innovation - Letter of Internship - {employee.designation} Intern"
                email_type = "internship_letter"
            else:
                subject = f"Rapid Innovation - Contractor's Agreement - {employee.full_name}"
                email_type = "contract_agreement"
            
            # Email body
            body_html = f"""
            <p>Hello {employee.full_name},</p>
            
            <p>Greetings from Rapid Innovation!!</p>
            
            <p>{'As discussed, we' if employee.employee_type != EmployeeType.FULL_TIME else 'We'} are pleased to extend the offer to you 
            for the position of <b>{employee.designation}</b> at Rapid Innovation
            {', starting on ' + template_data['date_of_joining'] if employee.employee_type == EmployeeType.INTERN else ''}.</p>
            
            <p>PFA the copy of the {'internship letter' if employee.employee_type == EmployeeType.INTERN else 'offer letter' if employee.employee_type == EmployeeType.FULL_TIME else 'agreement'} 
            for your ready reference. Kindly revert with your acceptance by sending the duly signed copy of the letter.</p>
            
            {'<p>This opportunity is a permanent remote job.</p>' if employee.employee_type != EmployeeType.INTERN else ''}
            
            <p>At Rapid Innovation, we provide every possible opportunity for the growth and development of our people, 
            and we hope that you will also contribute to the growth of Rapid Innovation.</p>
            
            <p>We look forward to a lasting relationship between us.</p>
            
            <p>Best wishes for your new endeavors!!</p>
            
            <p>Please feel free to contact us if you have any queries.</p>
            
            <p>Best regards,<br>
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
                        'email_type': email_type,
                        'to_email': employee.email_personal,
                        'subject': subject
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending offer letter email: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending email: {str(e)}'
            }


    def _number_to_words(self, number: float) -> str:
        """Convert number to words (Indian numbering system)"""
        # Simplified version - in production, use a library like num2words
        ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
        tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
        teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
        
        # Convert to string for simplicity
        if number < 100000:
            return f"{int(number):,} only"
        
        lakhs = int(number / 100000)
        remainder = int(number % 100000)
        
        if lakhs == 1:
            return f"One Lakh {remainder:,} only" if remainder > 0 else "One Lakh only"
        else:
            return f"{lakhs} Lakhs {remainder:,} only" if remainder > 0 else f"{lakhs} Lakhs only"
    
    def mark_offer_accepted(self, employee_id: int, signed_pdf_path: str = None) -> Dict[str, Any]:
        """Mark offer letter as accepted"""
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
                
                checklist.offer_letter_signed = True
                checklist.offer_signed_date = datetime.utcnow()
                
                # TODO: Store signed PDF path if provided
                
                session.commit()
                
                logger.info(f"Offer letter marked as accepted for employee ID {employee_id}")
                
                return {
                    'success': True,
                    'message': 'Offer letter marked as accepted'
                }
                
        except Exception as e:
            logger.error(f"Error marking offer as accepted: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }