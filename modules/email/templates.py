import logging
from typing import Dict, List, Any, Optional
from database.connection import get_db_session
from database.models import EmailTemplate
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailTemplateManager:
    """Manage email templates for the HR system"""
    
    # Note: These templates are deprecated in favor of direct HTML email generation
    # They are kept for backward compatibility but should not be used for new emails
    # All new email functions should use direct HTML with actual employee data
    DEFAULT_TEMPLATES = [
        {
            'template_name': 'document_request_intern',
            'template_type': 'onboarding',
            'subject': 'Rapid Innovation - Important Documents Required - [DEPRECATED]',
            'body_html': '''
                <p>This template is deprecated. Use direct HTML email generation instead.</p>
            ''',
            'variables': '{"note": "Deprecated template"}'
        },
        {
            'template_name': 'document_request_fulltime',
            'template_type': 'onboarding',
            'subject': 'Rapid Innovation - Important Documents Required - [DEPRECATED]',
            'body_html': '''
                <p>This template is deprecated. Use direct HTML email generation instead.</p>
            ''',
            'variables': '{"note": "Deprecated template"}'
        },
        {
            'template_name': 'welcome_onboard',
            'template_type': 'onboarding',
            'subject': 'Welcome On Board - [DEPRECATED]',
            'body_html': '''
                <p>This template is deprecated. Use direct HTML email generation instead.</p>
            ''',
            'variables': '{"note": "Deprecated template"}'
        },
        {
            'template_name': 'offer_letter_intern',
            'template_type': 'onboarding',
            'subject': 'Rapid Innovation - Letter of Internship - [DEPRECATED]',
            'body_html': '''
                <p>This template is deprecated. Use direct HTML email generation instead.</p>
            ''',
            'variables': '{"note": "Deprecated template"}'
        },
        {
            'template_name': 'bgv_notification',
            'template_type': 'onboarding',
            'subject': 'Background Verification Process Initiated - [DEPRECATED]',
            'body_html': '''
                <p>This template is deprecated. Use direct HTML email generation instead.</p>
            ''',
            'variables': '{"note": "Deprecated template"}'
        },
        {
            'template_name': 'exit_feedback_form',
            'template_type': 'offboarding',
            'subject': 'Exit Feedback Form - [DEPRECATED]',
            'body_html': '''
                <p>This template is deprecated. Use direct HTML email generation instead.</p>
            ''',
            'variables': '{"note": "Deprecated template"}'
        }
    ]
    
    @classmethod
    def initialize_default_templates(cls) -> Dict[str, Any]:
        """Initialize default email templates in the database"""
        try:
            created_count = 0
            existing_count = 0
            
            with get_db_session() as session:
                for template_data in cls.DEFAULT_TEMPLATES:
                    # Check if template already exists
                    existing = session.query(EmailTemplate).filter_by(
                        template_name=template_data['template_name']
                    ).first()
                    
                    if not existing:
                        template = EmailTemplate(
                            template_name=template_data['template_name'],
                            template_type=template_data['template_type'],
                            subject=template_data['subject'],
                            body_html=template_data['body_html'],
                            body_text=cls._html_to_text(template_data['body_html']),
                            variables=template_data['variables'],
                            created_by='system'
                        )
                        session.add(template)
                        created_count += 1
                    else:
                        existing_count += 1
                
                session.commit()
            
            logger.info(f"Email templates initialized: {created_count} created, {existing_count} existing")
            
            return {
                'success': True,
                'message': f'Templates initialized: {created_count} new, {existing_count} existing',
                'created': created_count,
                'existing': existing_count
            }
            
        except Exception as e:
            logger.error(f"Error initializing email templates: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def create_custom_template(template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom email template"""
        try:
            with get_db_session() as session:
                # Check if template name already exists
                existing = session.query(EmailTemplate).filter_by(
                    template_name=template_data['template_name']
                ).first()
                
                if existing:
                    return {
                        'success': False,
                        'message': 'Template with this name already exists'
                    }
                
                template = EmailTemplate(
                    template_name=template_data['template_name'],
                    template_type=template_data['template_type'],
                    subject=template_data['subject'],
                    body_html=template_data['body_html'],
                    body_text=template_data.get('body_text', EmailTemplateManager._html_to_text(template_data['body_html'])),
                    variables=template_data.get('variables', '{}'),
                    created_by=template_data.get('created_by', 'user')
                )
                
                session.add(template)
                session.commit()
                
                logger.info(f"Custom email template created: {template.template_name}")
                
                return {
                    'success': True,
                    'message': 'Template created successfully',
                    'template_id': template.id
                }
                
        except Exception as e:
            logger.error(f"Error creating custom template: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def update_template(template_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing email template"""
        try:
            with get_db_session() as session:
                template = session.query(EmailTemplate).filter_by(id=template_id).first()
                
                if not template:
                    return {
                        'success': False,
                        'message': 'Template not found'
                    }
                
                # Update allowed fields
                allowed_fields = ['subject', 'body_html', 'body_text', 'variables', 'active']
                for field in allowed_fields:
                    if field in update_data:
                        setattr(template, field, update_data[field])
                
                template.updated_at = datetime.utcnow()
                session.commit()
                
                logger.info(f"Email template updated: {template.template_name}")
                
                return {
                    'success': True,
                    'message': 'Template updated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error updating template: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def get_template(template_name: str) -> Optional[EmailTemplate]:
        """Get a specific email template by name"""
        try:
            with get_db_session() as session:
                return session.query(EmailTemplate).filter_by(
                    template_name=template_name,
                    active=True
                ).first()
        except Exception as e:
            logger.error(f"Error fetching template: {str(e)}")
            return None
    
    @staticmethod
    def get_templates_by_type(template_type: str) -> List[EmailTemplate]:
        """Get all templates of a specific type"""
        try:
            with get_db_session() as session:
                return session.query(EmailTemplate).filter_by(
                    template_type=template_type,
                    active=True
                ).all()
        except Exception as e:
            logger.error(f"Error fetching templates by type: {str(e)}")
            return []
    
    @staticmethod
    def deactivate_template(template_id: int) -> Dict[str, Any]:
        """Deactivate an email template"""
        try:
            with get_db_session() as session:
                template = session.query(EmailTemplate).filter_by(id=template_id).first()
                
                if not template:
                    return {
                        'success': False,
                        'message': 'Template not found'
                    }
                
                template.active = False
                template.updated_at = datetime.utcnow()
                session.commit()
                
                logger.info(f"Email template deactivated: {template.template_name}")
                
                return {
                    'success': True,
                    'message': 'Template deactivated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error deactivating template: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def get_template_variables(template_name: str) -> Dict[str, str]:
        """Get the variables required for a template"""
        try:
            template = EmailTemplateManager.get_template(template_name)
            if template and template.variables:
                import json
                return json.loads(template.variables)
            return {}
        except Exception as e:
            logger.error(f"Error getting template variables: {str(e)}")
            return {}
    
    @staticmethod
    def _html_to_text(html: str) -> str:
        """Convert HTML to plain text"""
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Replace multiple newlines with single newline
        text = re.sub(r'\n+', '\n', text)
        return text.strip()