"""
Employee Actions Module
Handles email sending and letter generation for employees
"""

import os
import logging
import streamlit as st
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader
from modules.email.email_Sender import EmailSender
from config import config

logger = logging.getLogger(__name__)

class EmployeeActions:
    """Handle employee-related actions like sending emails and generating letters"""
    
    def __init__(self):
        self.email_sender = EmailSender()
        
        # Email templates for onboarding
        self.onboarding_email_templates = [
            'welcome_onboard.html',
            'initial_document_request.html'
        ]
        
        # Email templates for offboarding  
        self.offboarding_email_templates = [
            'exit_initiation.html',
            'asset_return.html'
        ]
        
        # Letter templates for onboarding
        self.onboarding_letter_templates = [
            'offer_letter.html',
            'appointment_letter.html', 
            'contract_agreement.html',
            'internship_letter.html'
        ]
        
        # Letter templates for offboarding
        self.offboarding_letter_templates = [
            'experience_letter.html',
            'internship_certificate.html'
        ]
    
    def get_available_templates(self, template_type: str, process_type: str) -> List[str]:
        """Get available templates based on type and process"""
        if template_type == 'email':
            if process_type == 'onboarding':
                return self.onboarding_email_templates
            else:
                return self.offboarding_email_templates
        else:  # letter
            if process_type == 'onboarding':
                return self.onboarding_letter_templates
            else:
                return self.offboarding_letter_templates
    
    def send_email_to_employee(self, employee_data: Dict[str, Any], template_name: str,
                              additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send email to employee using direct HTML (template-based approach deprecated)"""
        try:
            # Generate direct HTML email based on template name
            email_data = self._generate_direct_email(employee_data, template_name, additional_data)

            # Send email
            result = self.email_sender.send_email(email_data)

            # Add CC information to result
            result['cc_emails'] = email_data.get('cc_emails', [])
            result['template_used'] = template_name

            if result['success']:
                logger.info(f"Email sent successfully to {employee_data.get('email')} using template {template_name}")
            else:
                logger.error(f"Failed to send email to {employee_data.get('email')}: {result.get('message')}")

            return result

        except Exception as e:
            logger.error(f"Error sending email to employee: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending email: {str(e)}'
            }
    
    def generate_letter_for_employee(self, employee_data: Dict[str, Any], template_name: str,
                                   additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate letter for employee using proper PDF generators"""
        try:
            # Prepare letter data
            letter_data = self._prepare_letter_data(employee_data, template_name, additional_data)

            # Generate PDF letter using HTML template
            file_path = self._generate_html_letter(employee_data, template_name, letter_data)

            if file_path:
                logger.info(f"Letter generated for {employee_data.get('full_name')} using template {template_name}")
                return {
                    'success': True,
                    'message': f'Letter generated successfully using {template_name}',
                    'file_path': file_path,
                    'template_name': template_name
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to generate letter file'
                }

        except Exception as e:
            logger.error(f"Error generating letter for employee: {str(e)}")
            return {
                'success': False,
                'message': f'Error generating letter: {str(e)}'
            }

    def _generate_direct_email(self, employee_data: Dict[str, Any], template_name: str,
                              additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate direct HTML email content based on template name"""

        # Get employee details
        full_name = employee_data.get('full_name', 'Employee')
        first_name = full_name.split()[0] if full_name else 'Employee'
        designation = employee_data.get('designation', 'Position')
        employee_type = employee_data.get('employee_type', 'full_time')

        # Determine email content based on template name
        if 'welcome' in template_name.lower():
            subject = f"Welcome On Board - {full_name}"
            body_html = f"""
            <p>Dear {full_name},</p>
            <p>Greetings of the day !!</p>
            <p>We are happy to have you join our organization. We believe that you will be a great asset to our company.</p>
            <p>Again, Congratulations. We are thrilled to have you join the team and look forward to working with you.</p>
            <p>Please let me know if you have any questions.</p>
            <p>Regards<br>Team HR<br>Rapid Innovation</p>
            """
        elif 'document' in template_name.lower():
            subject = f"Important Documents Required - {designation}"
            body_html = f"""
            <p>Hi {first_name},</p>
            <p>Greetings from Rapid Innovation!!</p>
            <p>This is regarding your joining for the "{designation}" position at Rapid Innovation.</p>
            <p>As a part of our Employment Joining process, we would require soft copies of the below-mentioned documents:</p>
            <ol>
                <li><strong>Educational Docs</strong> (10th, 12th, Graduation & Post Graduation Certificates)</li>
                <li><strong>ID proofs</strong> (Aadhaar card, Passport, Driving license, PAN card)</li>
                {'<li><strong>Resignation/relieving letters</strong>, the Last three Months of salary slips, Appointment letters, and offer letters from previous organizations</li>' if employee_type != 'intern' else ''}
                <li><strong>Passport-size photograph</strong></li>
            </ol>
            <p>Also, please share your full name and address as per your documents.</p>
            <p>Feel free to get in touch with me in case of any queries or questions.</p>
            <p>Thanks & Regards,<br><strong>Team HR</strong><br>Rapid Innovation</p>
            """
        elif 'bgv' in template_name.lower():
            subject = "Background Verification Process Initiated"
            body_html = f"""
            <p>Dear {full_name},</p>
            <p>This is to inform you that we have initiated the background verification process for your employment.</p>
            <p>We have reached out to your previous employer(s) for verification of the information provided by you. This is a standard process for all new employees.</p>
            <p>The verification process typically takes 7-10 business days. We will keep you updated on the progress.</p>
            <p>If you have any questions or concerns, please feel free to reach out to the HR team.</p>
            <p>Best regards,<br>Team HR<br>Rapid Innovation</p>
            """
        elif 'exit' in template_name.lower() or 'feedback' in template_name.lower():
            subject = "Exit Feedback Form - Your Valuable Feedback"
            body_html = f"""
            <p>Dear {full_name},</p>
            <p>As you prepare to leave Rapid Innovation, we would greatly appreciate your feedback about your experience with us.</p>
            <p>Your insights will help us improve our workplace and create a better environment for current and future employees.</p>
            <p>All responses will be kept confidential and will only be used for organizational improvement purposes.</p>
            <p>Thank you for your contributions to Rapid Innovation. We wish you all the best in your future endeavors!</p>
            <p>Best regards,<br>Team HR<br>Rapid Innovation</p>
            """
        else:
            # Generic email template
            subject = f"Communication from HR - {config.COMPANY_NAME}"
            body_html = f"""
            <p>Dear {full_name},</p>
            <p>This is a communication from the HR team at {config.COMPANY_NAME}.</p>
            <p>If you have any questions, please feel free to contact the HR department.</p>
            <p>Best regards,<br>Team HR<br>{config.COMPANY_NAME}</p>
            """

        # Prepare CC emails
        cc_emails = [config.DEFAULT_SENDER_EMAIL]
        manager_email = employee_data.get('manager_email')
        if manager_email and manager_email != config.DEFAULT_SENDER_EMAIL:
            cc_emails.append(manager_email)

        # Remove duplicates and employee's own email from CC
        cc_emails = list(set(cc_emails))
        if employee_data.get('email') in cc_emails:
            cc_emails.remove(employee_data.get('email'))

        return {
            'to_email': employee_data.get('email'),
            'cc_emails': cc_emails,
            'subject': subject,
            'body_html': body_html,
            'body_text': self.email_sender._html_to_text(body_html)
        }

    def _prepare_email_data(self, employee_data: Dict[str, Any], template_name: str,
                           additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare email data with proper recipients and CC"""
        
        # Base email data
        email_data = {
            'to_email': employee_data.get('email'),
            'template_name': template_name,
            'template_data': {
                'full_name': employee_data.get('full_name'),
                'employee_id': employee_data.get('employee_id'),
                'department': employee_data.get('department'),
                'employee_type': employee_data.get('employee_type'),
                'reporting_manager': employee_data.get('reporting_manager'),
                'company_name': config.COMPANY_NAME,
                'hr_email': config.DEFAULT_SENDER_EMAIL,
                'current_date': datetime.now().strftime('%B %d, %Y'),
                # Add config object for template access
                'config': {
                    'COMPANY_NAME': config.COMPANY_NAME,
                    'COMPANY_ADDRESS': config.COMPANY_ADDRESS,
                    'DEFAULT_SENDER_EMAIL': config.DEFAULT_SENDER_EMAIL,
                    'HR_MANAGER_NAME': config.HR_MANAGER_NAME,
                    'HR_MANAGER_DESIGNATION': config.HR_MANAGER_DESIGNATION
                },
                # Add additional template variables
                'joining_form_link': 'https://forms.google.com/your-joining-form',
                'date_of_joining': employee_data.get('date_of_joining', 'TBD'),
                'designation': employee_data.get('designation', 'TBD'),
                'systems_access': ['Email', 'Slack', 'Project Management Tool', 'HR Portal']
            }
        }
        
        # Add additional data if provided
        if additional_data:
            email_data['template_data'].update(additional_data)
        
        # Determine CC recipients based on template and employee type
        cc_emails = []
        
        # Always CC HR
        cc_emails.append(config.DEFAULT_SENDER_EMAIL)
        
        # Add manager to CC if available and not the same as HR
        manager_email = employee_data.get('manager_email')
        if manager_email and manager_email != config.DEFAULT_SENDER_EMAIL:
            cc_emails.append(manager_email)
        
        # Remove duplicates and employee's own email from CC
        cc_emails = list(set(cc_emails))
        if employee_data.get('email') in cc_emails:
            cc_emails.remove(employee_data.get('email'))
        
        email_data['cc_emails'] = cc_emails
        
        return email_data
    
    def _prepare_letter_data(self, employee_data: Dict[str, Any], template_name: str,
                            additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare letter data for generation"""
        
        letter_data = {
            'employee_name': employee_data.get('full_name', 'Unknown Employee'),
            'full_name': employee_data.get('full_name', 'Unknown Employee'),
            'employee_id': employee_data.get('employee_id', 'EMP999'),
            'department': employee_data.get('department', 'General'),
            'designation': employee_data.get('designation', 'Employee'),
            'employee_type': employee_data.get('employee_type', 'full_time'),
            'reporting_manager': employee_data.get('reporting_manager', 'To be assigned'),
            'date_of_joining': employee_data.get('date_of_joining', datetime.now().date()),
            'company_name': config.COMPANY_NAME,
            'company_address': config.COMPANY_ADDRESS,
            'hr_manager_name': config.HR_MANAGER_NAME,
            'hr_manager_designation': config.HR_MANAGER_DESIGNATION,
            'current_date': datetime.now().strftime('%B %d, %Y'),
            'issue_date': datetime.now().strftime('%B %d, %Y'),
            # Add config object for template access
            'config': {
                'COMPANY_NAME': config.COMPANY_NAME,
                'COMPANY_ADDRESS': config.COMPANY_ADDRESS,
                'DEFAULT_SENDER_EMAIL': config.DEFAULT_SENDER_EMAIL,
                'COMPANY_WEBSITE': getattr(config, 'COMPANY_WEBSITE', 'www.rapidinnovation.com'),
                'COMPANY_CITY': getattr(config, 'COMPANY_CITY', 'Goa')
            },
            # Add employment terms
            'probation_period': '3',
            'notice_period_probation': '15',
            'notice_period_confirmed': '30',
            'ctc': employee_data.get('ctc', None)
        }
        
        # Add additional data if provided
        if additional_data:
            letter_data.update(additional_data)
        
        return letter_data



    def _generate_html_letter(self, employee_data: Dict[str, Any], template_name: str,
                             letter_data: Dict[str, Any]) -> str:
        """Generate PDF letter from HTML template and save to file"""
        try:
            from utils.template_renderer import render_letter
            import os
            from datetime import datetime

            logger.info(f"Generating PDF letter with template: {template_name}")
            logger.info(f"Letter data keys: {list(letter_data.keys())}")

            # Render the letter template to HTML
            html_content = render_letter(template_name, **letter_data)

            # Create filename for PDF
            employee_id = employee_data.get('employee_id', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_filename = f"{template_name.replace('.html', '')}_{employee_id}_{timestamp}.pdf"

            # Determine output directory based on template type
            if 'offer' in template_name.lower():
                output_dir = os.path.join(config.UPLOAD_FOLDER, 'offer_letters')
            elif 'appointment' in template_name.lower():
                output_dir = os.path.join(config.UPLOAD_FOLDER, 'appointment_letters')
            elif 'experience' in template_name.lower() or 'internship' in template_name.lower():
                output_dir = os.path.join(config.UPLOAD_FOLDER, 'experience_letters')
            else:
                output_dir = os.path.join(config.UPLOAD_FOLDER, 'letters')

            # Create directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

            # Generate PDF from HTML using WeasyPrint
            pdf_path = os.path.join(output_dir, pdf_filename)
            success = self._convert_html_to_pdf(html_content, pdf_path)

            if success:
                logger.info(f"PDF letter saved to: {pdf_path}")
                return pdf_path
            else:
                logger.error("Failed to convert HTML to PDF")
                return None

        except Exception as e:
            logger.error(f"Error generating PDF letter: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _convert_html_to_pdf(self, html_content: str, output_path: str) -> bool:
        """Convert HTML content to PDF using WeasyPrint"""
        try:
            import weasyprint
            from weasyprint import HTML, CSS

            # Create CSS for better PDF formatting
            pdf_css = CSS(string='''
                @page {
                    size: A4;
                    margin: 2cm;
                }
                body {
                    font-family: 'Times New Roman', serif;
                    line-height: 1.6;
                    color: #000;
                }
                .letter-container {
                    max-width: 100%;
                    margin: 0;
                    padding: 0;
                }
                @media print {
                    .letter-container {
                        box-shadow: none;
                        border-radius: 0;
                        padding: 0;
                    }
                }
            ''')

            # Convert HTML to PDF
            html_doc = HTML(string=html_content)
            html_doc.write_pdf(output_path, stylesheets=[pdf_css])

            logger.info(f"Successfully converted HTML to PDF: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error converting HTML to PDF: {str(e)}")
            # Fallback: save as HTML if PDF conversion fails
            try:
                html_path = output_path.replace('.pdf', '.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.info(f"Fallback: saved as HTML file: {html_path}")
                return html_path
            except:
                return False

    def send_letter_via_email(self, employee_data: Dict[str, Any], file_path: str,
                             template_name: str) -> Dict[str, Any]:
        """Send generated letter via email"""
        try:
            # Clean template name by removing .html extension if present
            clean_template_name = template_name.replace('.html', '').replace('_', ' ')

            # Prepare email data
            subject = f"Your {clean_template_name.title()} - {config.COMPANY_NAME}"

            # Email body
            body_html = f"""
            <p>Dear {employee_data.get('full_name', 'Employee')},</p>

            <p>Please find attached your {clean_template_name.lower()} from {config.COMPANY_NAME}.</p>

            <p>If you have any questions, please feel free to contact the HR department.</p>

            <p>Best regards,<br>
            <strong>HR Team</strong><br>
            {config.COMPANY_NAME}</p>
            """

            # Prepare attachment with proper PDF naming
            attachment_name = f"{clean_template_name.title()}.pdf"

            email_data = {
                'to_email': employee_data.get('email'),
                'subject': subject,
                'body_html': body_html,
                'attachments': [{
                    'file_path': file_path,
                    'file_name': attachment_name
                }]
            }

            # Add CC emails
            cc_emails = [config.DEFAULT_SENDER_EMAIL]
            manager_email = employee_data.get('manager_email')
            if manager_email and manager_email != config.DEFAULT_SENDER_EMAIL:
                cc_emails.append(manager_email)

            # Remove duplicates and employee's own email from CC
            cc_emails = list(set(cc_emails))
            if employee_data.get('email') in cc_emails:
                cc_emails.remove(employee_data.get('email'))

            email_data['cc_emails'] = cc_emails

            # Send email
            result = self.email_sender.send_email(email_data)

            if result['success']:
                logger.info(f"Letter sent via email to {employee_data.get('email')}")
            else:
                logger.error(f"Failed to send letter via email: {result.get('message')}")

            return result

        except Exception as e:
            logger.error(f"Error sending letter via email: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending email: {str(e)}'
            }

    def get_template_preview(self, template_name: str, template_type: str) -> str:
        """Get a preview of the template"""
        try:
            template_folder = config.EMAIL_TEMPLATE_FOLDER if template_type == 'email' else config.LETTER_TEMPLATE_FOLDER
            template_path = os.path.join(template_folder, template_name)
            
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content[:500] + "..." if len(content) > 500 else content
            else:
                return "Template not found"
                
        except Exception as e:
            logger.error(f"Error getting template preview: {str(e)}")
            return "Error loading template preview"

# Global instance
employee_actions = EmployeeActions()
