import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Any, Optional
import os
from jinja2 import Template, Environment, FileSystemLoader
from datetime import datetime
from config import config
from database.connection import get_db_session
from database.models import EmailTemplate, EmailLog

logger = logging.getLogger(__name__)

class EmailSender:
    """Email sending functionality"""
    
    def __init__(self):
        self.smtp_server = config.email.smtp_server
        self.smtp_port = config.email.smtp_port
        self.smtp_username = config.email.smtp_username
        self.smtp_password = config.email.smtp_password
        self.use_tls = config.email.smtp_use_tls
        self.default_sender = config.email.default_sender_email
        self.default_sender_name = config.email.default_sender_name

        # Initialize Jinja2 environment for templates
        template_folder = getattr(config, 'EMAIL_TEMPLATE_FOLDER', 'templates/email')
        self.template_env = Environment(
            loader=FileSystemLoader(template_folder),
            autoescape=True
        )
    
    def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a single email with template support"""
        try:
            # Process template if provided
            if 'template_name' in email_data:
                processed_data = self._process_template(email_data)
                if not processed_data['success']:
                    return processed_data
                email_data.update(processed_data['data'])

            # Create message
            msg = MIMEMultipart('related')
            msg['From'] = f"{self.default_sender_name} <{self.default_sender}>"
            msg['To'] = email_data['to_email']
            msg['Subject'] = email_data.get('subject', 'No Subject')

            # Add CC if provided
            if 'cc_emails' in email_data and email_data['cc_emails']:
                cc_emails = email_data['cc_emails']
                if isinstance(cc_emails, str):
                    msg['Cc'] = cc_emails
                else:
                    msg['Cc'] = ', '.join(cc_emails)

            # Create alternative container for text and HTML
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)

            # Create the body
            text_part = MIMEText(email_data.get('body_text', ''), 'plain')
            html_part = MIMEText(email_data.get('body_html', ''), 'html')

            msg_alternative.attach(text_part)
            msg_alternative.attach(html_part)

            # Add company logo as embedded image
            self._attach_company_logo(msg)

            # Add attachments if any
            if 'attachments' in email_data:
                for attachment in email_data['attachments']:
                    self._attach_file(msg, attachment)

            # Send email
            if config.USE_SENDGRID:
                return self._send_via_sendgrid(email_data)
            else:
                return self._send_via_smtp(msg, email_data)

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending email: {str(e)}'
            }

    def _process_template(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process email template with provided data"""
        try:
            template_name = email_data['template_name']
            template_data = email_data.get('template_data', {})

            # Load template
            template = self.template_env.get_template(template_name)

            # Render template
            html_content = template.render(**template_data)

            # Extract subject from template or use default
            subject = self._extract_subject_from_template(template_name, template_data)

            return {
                'success': True,
                'data': {
                    'body_html': html_content,
                    'body_text': self._html_to_text(html_content),
                    'subject': subject
                }
            }

        except Exception as e:
            logger.error(f"Error processing template {template_name}: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing template: {str(e)}'
            }

    def _extract_subject_from_template(self, template_name: str, template_data: Dict[str, Any]) -> str:
        """Extract or generate subject line for email template"""

        # Subject mapping for different templates
        subject_mapping = {
            'welcome_onboard.html': 'Welcome to Rapid Innovation - {full_name}',
            'initial_document_request.html': 'Document Requirements - {full_name}',
            'exit_initiation.html': 'Exit Process Initiated - {full_name}',
            'asset_return.html': 'Asset Return Required - {full_name}',
        }

        subject_template = subject_mapping.get(template_name, 'Rapid Innovation - {full_name}')

        try:
            return subject_template.format(**template_data)
        except KeyError:
            return subject_template.replace('{full_name}', template_data.get('full_name', 'Employee'))

    def send_templated_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email using a template"""
        try:
            # Get template from database
            with get_db_session() as session:
                template = session.query(EmailTemplate).filter_by(
                    template_name=email_data['template_name'],
                    active=True
                ).first()
                
                if not template:
                    return {
                        'success': False,
                        'message': f"Template {email_data['template_name']} not found"
                    }
                
                # Render template with variables
                template_vars = email_data.get('template_variables', {})
                
                # Render subject
                subject_template = Template(template.subject)
                rendered_subject = subject_template.render(**template_vars)
                
                # Render body
                body_template = Template(template.body_html)
                rendered_body = body_template.render(**template_vars)
                
                # Prepare email data
                final_email_data = {
                    'to_email': email_data['to_email'],
                    'cc_emails': email_data.get('cc_emails', []),
                    'subject': rendered_subject,
                    'body_html': rendered_body,
                    'body_text': template.body_text or self._html_to_text(rendered_body)
                }
                
                # Add attachments if provided
                if 'attachments' in email_data:
                    final_email_data['attachments'] = email_data['attachments']
                
                # Send email
                result = self.send_email(final_email_data)
                result['subject'] = rendered_subject
                return result
                
        except Exception as e:
            logger.error(f"Error sending templated email: {str(e)}")
            return {
                'success': False,
                'message': f'Error sending templated email: {str(e)}'
            }
    
    def _send_via_smtp(self, msg: MIMEMultipart, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via SMTP"""
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            # Login if credentials provided
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            # Get all recipients
            recipients = [email_data['to_email']]
            if 'cc_emails' in email_data and email_data['cc_emails']:
                cc_emails = email_data['cc_emails']
                if isinstance(cc_emails, str):
                    recipients.append(cc_emails)
                else:
                    recipients.extend(cc_emails)
            
            # Send email
            server.send_message(msg, self.default_sender, recipients)
            server.quit()
            
            logger.info(f"Email sent successfully to {email_data['to_email']}")
            
            return {
                'success': True,
                'message': 'Email sent successfully'
            }
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return {
                'success': False,
                'message': f'SMTP error: {str(e)}'
            }
    
    def _send_via_sendgrid(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via SendGrid API"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            sg = sendgrid.SendGridAPIClient(api_key=config.SENDGRID_API_KEY)
            
            from_email = Email(self.default_sender, self.default_sender_name)
            to_email = To(email_data['to_email'])
            subject = email_data['subject']
            content = Content("text/html", email_data.get('body_html', ''))
            
            mail = Mail(from_email, to_email, subject, content)
            
            # Add CC if provided
            if 'cc_emails' in email_data and email_data['cc_emails']:
                cc_emails = email_data['cc_emails']
                if isinstance(cc_emails, str):
                    mail.add_cc(cc_emails)
                else:
                    for cc in cc_emails:
                        mail.add_cc(cc)
            
            response = sg.send(mail)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent via SendGrid to {email_data['to_email']}")
                return {
                    'success': True,
                    'message': 'Email sent successfully'
                }
            else:
                return {
                    'success': False,
                    'message': f'SendGrid error: {response.body}'
                }
                
        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            return {
                'success': False,
                'message': f'SendGrid error: {str(e)}'
            }
    
    def _attach_company_logo(self, msg: MIMEMultipart):
        """Attach company logo as embedded image"""
        try:
            # Try Header.png first, then fallback to company_logo.png
            logo_paths = [
                'static/images/Header.png',
                'static/images/company_logo.png'
            ]
            
            logo_path = None
            for path in logo_paths:
                if os.path.exists(path):
                    logo_path = path
                    break
            
            if not logo_path:
                logger.warning("No company logo found, skipping logo attachment")
                return
            
            with open(logo_path, 'rb') as file:
                logo_part = MIMEBase('image', 'png')
                logo_part.set_payload(file.read())
                encoders.encode_base64(logo_part)
                logo_part.add_header('Content-ID', '<header_logo>')
                logo_part.add_header('Content-Disposition', 'inline', filename='header_logo.png')
                msg.attach(logo_part)
                
        except Exception as e:
            logger.error(f"Error attaching company logo: {str(e)}")

    def _attach_file(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Attach a file to the email"""
        try:
            file_path = attachment['file_path']
            file_name = attachment.get('file_name', os.path.basename(file_path))

            with open(file_path, 'rb') as file:
                # Determine MIME type based on file extension
                if file_name.lower().endswith('.pdf'):
                    part = MIMEBase('application', 'pdf')
                elif file_name.lower().endswith(('.jpg', '.jpeg')):
                    part = MIMEBase('image', 'jpeg')
                elif file_name.lower().endswith('.png'):
                    part = MIMEBase('image', 'png')
                elif file_name.lower().endswith('.doc'):
                    part = MIMEBase('application', 'msword')
                elif file_name.lower().endswith('.docx'):
                    part = MIMEBase('application', 'vnd.openxmlformats-officedocument.wordprocessingml.document')
                else:
                    part = MIMEBase('application', 'octet-stream')

                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {file_name}'
                )
                msg.attach(part)

        except Exception as e:
            logger.error(f"Error attaching file: {str(e)}")
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Replace multiple newlines with single newline
        text = re.sub(r'\n+', '\n', text)
        return text.strip()
    
    def send_bulk_emails(self, recipients: List[Dict[str, Any]], 
                        email_template: Dict[str, Any]) -> Dict[str, Any]:
        """Send bulk emails to multiple recipients"""
        results = {
            'total': len(recipients),
            'sent': 0,
            'failed': 0,
            'details': []
        }
        
        for recipient in recipients:
            try:
                # Merge recipient data with template
                email_data = {
                    'to_email': recipient['email'],
                    'template_name': email_template['template_name'],
                    'template_variables': {
                        **email_template.get('template_variables', {}),
                        **recipient.get('variables', {})
                    }
                }
                
                result = self.send_templated_email(email_data)
                
                if result['success']:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                
                results['details'].append({
                    'email': recipient['email'],
                    'success': result['success'],
                    'message': result.get('message', '')
                })
                
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'email': recipient['email'],
                    'success': False,
                    'message': str(e)
                })
        
        return results
    
    def log_email(self, employee_id: int, email_data: Dict[str, Any], 
                  status: str = 'sent', error_message: str = None):
        """Log email in database"""
        try:
            with get_db_session() as session:
                email_log = EmailLog(
                    employee_id=employee_id,
                    email_type=email_data.get('email_type', 'general'),
                    recipient_email=email_data['to_email'],
                    cc_emails=', '.join(email_data.get('cc_emails', [])) if email_data.get('cc_emails') else None,
                    subject=email_data['subject'],
                    body=email_data.get('body_html', ''),
                    status=status,
                    error_message=error_message
                )
                session.add(email_log)
                session.commit()
                
        except Exception as e:
            logger.error(f"Error logging email: {str(e)}")

# Email template loader
class EmailTemplateManager:
    """Manage email templates"""
    
    @staticmethod
    def create_template(template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new email template"""
        try:
            with get_db_session() as session:
                template = EmailTemplate(
                    template_name=template_data['template_name'],
                    template_type=template_data['template_type'],
                    subject=template_data['subject'],
                    body_html=template_data['body_html'],
                    body_text=template_data.get('body_text', ''),
                    variables=template_data.get('variables', '{}'),
                    created_by=template_data.get('created_by', 'system')
                )
                session.add(template)
                session.commit()
                
                return {
                    'success': True,
                    'message': 'Template created successfully',
                    'template_id': template.id
                }
                
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating template: {str(e)}'
            }
    
    @staticmethod
    def update_template(template_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an email template"""
        try:
            with get_db_session() as session:
                template = session.query(EmailTemplate).filter_by(id=template_id).first()
                
                if not template:
                    return {
                        'success': False,
                        'message': 'Template not found'
                    }
                
                # Update fields
                for field in ['subject', 'body_html', 'body_text', 'variables', 'active']:
                    if field in update_data:
                        setattr(template, field, update_data[field])
                
                template.updated_at = datetime.utcnow()
                session.commit()
                
                return {
                    'success': True,
                    'message': 'Template updated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error updating template: {str(e)}")
            return {
                'success': False,
                'message': f'Error updating template: {str(e)}'
            }
    
    @staticmethod
    def get_templates(template_type: str = None) -> List[EmailTemplate]:
        """Get email templates"""
        try:
            with get_db_session() as session:
                query = session.query(EmailTemplate).filter_by(active=True)
                
                if template_type:
                    query = query.filter_by(template_type=template_type)
                
                return query.all()
                
        except Exception as e:
            logger.error(f"Error fetching templates: {str(e)}")
            return []
