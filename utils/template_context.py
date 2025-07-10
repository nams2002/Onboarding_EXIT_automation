"""
Template Context Provider

Provides consistent context data for all templates, ensuring no hardcoded values.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from config import config


class TemplateContextProvider:
    """Provides consistent context for template rendering"""
    
    def __init__(self):
        self.config = config
    
    def get_base_context(self) -> Dict[str, Any]:
        """Get base context that should be available in all templates"""
        return {
            'config': {
                'COMPANY_NAME': self.config.company.name,
                'COMPANY_ADDRESS': self.config.company.address,
                'COMPANY_PHONE': self.config.company.phone,
                'COMPANY_EMAIL': self.config.company.email,
                'COMPANY_WEBSITE': self.config.company.website,
                'COMPANY_LOGO_PATH': self.config.company.logo_path,
                'DEFAULT_SENDER_EMAIL': self.config.email.default_sender_email,
                'DEFAULT_SENDER_NAME': self.config.email.default_sender_name,
                'HR_MANAGER_NAME': self.config.hr.manager_name,
                'HR_MANAGER_DESIGNATION': self.config.hr.manager_designation,
                'HR_MANAGER_EMAIL': self.config.hr.manager_email,
            },
            'datetime': datetime,
            'date': datetime.date,
        }
    
    def get_email_context(self, **kwargs) -> Dict[str, Any]:
        """Get context for email templates"""
        context = self.get_base_context()
        context.update(kwargs)
        return context
    
    def get_letter_context(self, **kwargs) -> Dict[str, Any]:
        """Get context for letter templates"""
        context = self.get_base_context()
        
        # Add letter-specific context
        context.update({
            'issue_date': datetime.now().strftime('%d %B %Y'),
            'hr_manager_name': self.config.hr.manager_name,
            'hr_manager_designation': self.config.hr.manager_designation,
        })
        
        context.update(kwargs)
        return context
    
    def get_appointment_letter_context(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get context specifically for appointment letters"""
        context = self.get_letter_context()
        
        # Add appointment letter specific data
        context.update({
            'employee_name': employee_data.get('full_name', ''),
            'designation': employee_data.get('designation', ''),
            'date_of_joining': employee_data.get('date_of_joining'),
            'employee_type': employee_data.get('employee_type', ''),
            'salary': employee_data.get('salary'),
            'probation_period': self.config.employee.probation_period.get(
                employee_data.get('employee_type', 'full_time'), 3
            ),
            'notice_period': self.config.employee.notice_period.get(
                employee_data.get('employee_type', 'full_time'), 30
            ),
        })
        
        return context
    
    def get_offer_letter_context(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get context specifically for offer letters"""
        context = self.get_letter_context()
        
        context.update({
            'candidate_name': employee_data.get('full_name', ''),
            'position': employee_data.get('designation', ''),
            'department': employee_data.get('department', ''),
            'salary': employee_data.get('salary'),
            'joining_date': employee_data.get('date_of_joining'),
            'employee_type': employee_data.get('employee_type', ''),
        })
        
        return context
    
    def get_experience_letter_context(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get context specifically for experience letters"""
        context = self.get_letter_context()
        
        context.update({
            'employee_name': employee_data.get('full_name', ''),
            'designation': employee_data.get('designation', ''),
            'department': employee_data.get('department', ''),
            'date_of_joining': employee_data.get('date_of_joining'),
            'last_working_day': employee_data.get('last_working_day'),
            'employee_id': employee_data.get('employee_id', ''),
        })
        
        return context
    
    def get_document_request_context(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get context for document request emails"""
        context = self.get_email_context()
        
        # Get required documents based on employee type
        employee_type = employee_data.get('employee_type', 'full_time')
        required_docs = self.config.employee.required_documents.get(employee_type, [])
        
        context.update({
            'employee_name': employee_data.get('full_name', ''),
            'designation': employee_data.get('designation', ''),
            'employee_type': self.config.employee.types.get(employee_type, ''),
            'required_documents': required_docs,
            'upload_deadline': employee_data.get('upload_deadline'),
        })
        
        return context
    
    def get_welcome_email_context(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get context for welcome emails"""
        context = self.get_email_context()
        
        context.update({
            'employee_name': employee_data.get('full_name', ''),
            'designation': employee_data.get('designation', ''),
            'department': employee_data.get('department', ''),
            'date_of_joining': employee_data.get('date_of_joining'),
            'employee_id': employee_data.get('employee_id', ''),
            'reporting_manager': employee_data.get('reporting_manager', ''),
            'work_location': employee_data.get('work_location', ''),
        })
        
        return context
    
    def get_exit_email_context(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get context for exit-related emails"""
        context = self.get_email_context()
        
        context.update({
            'employee_name': employee_data.get('full_name', ''),
            'designation': employee_data.get('designation', ''),
            'department': employee_data.get('department', ''),
            'employee_id': employee_data.get('employee_id', ''),
            'last_working_day': employee_data.get('last_working_day'),
            'exit_type': employee_data.get('exit_type', ''),
            'reporting_manager': employee_data.get('reporting_manager', ''),
        })
        
        return context
    
    def get_asset_return_context(self, employee_data: Dict[str, Any], assets: list) -> Dict[str, Any]:
        """Get context for asset return emails"""
        context = self.get_email_context()
        
        context.update({
            'employee_name': employee_data.get('full_name', ''),
            'employee_id': employee_data.get('employee_id', ''),
            'assets': assets,
            'return_deadline': employee_data.get('asset_return_deadline'),
            'last_working_day': employee_data.get('last_working_day'),
        })
        
        return context
    
    def validate_context(self, context: Dict[str, Any], required_keys: list) -> list:
        """Validate that context has all required keys"""
        missing_keys = []
        
        for key in required_keys:
            if '.' in key:
                # Handle nested keys like 'config.COMPANY_NAME'
                keys = key.split('.')
                current = context
                try:
                    for k in keys:
                        current = current[k]
                    if not current:
                        missing_keys.append(key)
                except (KeyError, TypeError):
                    missing_keys.append(key)
            else:
                if key not in context or not context[key]:
                    missing_keys.append(key)
        
        return missing_keys


# Global instance
template_context = TemplateContextProvider()


def get_template_context(template_type: str = 'base', **kwargs) -> Dict[str, Any]:
    """
    Convenience function to get template context
    
    Args:
        template_type: Type of template ('base', 'email', 'letter', etc.)
        **kwargs: Additional context data
    
    Returns:
        Dictionary with template context
    """
    if template_type == 'email':
        return template_context.get_email_context(**kwargs)
    elif template_type == 'letter':
        return template_context.get_letter_context(**kwargs)
    elif template_type == 'appointment_letter':
        return template_context.get_appointment_letter_context(kwargs.get('employee_data', {}))
    elif template_type == 'offer_letter':
        return template_context.get_offer_letter_context(kwargs.get('employee_data', {}))
    elif template_type == 'experience_letter':
        return template_context.get_experience_letter_context(kwargs.get('employee_data', {}))
    elif template_type == 'document_request':
        return template_context.get_document_request_context(kwargs.get('employee_data', {}))
    elif template_type == 'welcome_email':
        return template_context.get_welcome_email_context(kwargs.get('employee_data', {}))
    elif template_type == 'exit_email':
        return template_context.get_exit_email_context(kwargs.get('employee_data', {}))
    elif template_type == 'asset_return':
        return template_context.get_asset_return_context(
            kwargs.get('employee_data', {}), 
            kwargs.get('assets', [])
        )
    else:
        return template_context.get_base_context()
