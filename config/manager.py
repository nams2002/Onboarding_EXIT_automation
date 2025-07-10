"""
Configuration Manager

Provides centralized access to configuration and template context.
"""

from typing import Dict, Any, Optional
from .base import BaseConfig
from .environments import get_config


class ConfigManager:
    """Manages configuration access and template context"""
    
    def __init__(self):
        self._config: Optional[BaseConfig] = None
        self._template_context: Optional[Dict[str, Any]] = None
    
    @property
    def config(self) -> BaseConfig:
        """Get the current configuration"""
        if self._config is None:
            self._config = get_config()
        return self._config
    
    def reload_config(self):
        """Reload configuration (useful for development)"""
        self._config = None
        self._template_context = None
    
    def get_template_context(self) -> Dict[str, Any]:
        """Get template context with all necessary variables"""
        if self._template_context is None:
            self._template_context = self.config.get_template_context()
        return self._template_context
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get company information for templates"""
        return {
            'name': self.config.company.name,
            'address': self.config.company.address,
            'phone': self.config.company.phone,
            'email': self.config.company.email,
            'website': self.config.company.website,
            'logo_path': self.config.company.logo_path,
        }
    
    def get_hr_info(self) -> Dict[str, Any]:
        """Get HR information for templates"""
        return {
            'manager_name': self.config.hr.manager_name,
            'manager_designation': self.config.hr.manager_designation,
            'manager_email': self.config.hr.manager_email,
            'team_emails': self.config.hr.team_emails,
        }
    
    def get_email_config(self) -> Dict[str, Any]:
        """Get email configuration"""
        return {
            'smtp_server': self.config.email.smtp_server,
            'smtp_port': self.config.email.smtp_port,
            'smtp_username': self.config.email.smtp_username,
            'smtp_password': self.config.email.smtp_password,
            'smtp_use_tls': self.config.email.smtp_use_tls,
            'default_sender_email': self.config.email.default_sender_email,
            'default_sender_name': self.config.email.default_sender_name,
            'use_sendgrid': self.config.email.use_sendgrid,
            'sendgrid_api_key': self.config.email.sendgrid_api_key,
        }
    
    def get_employee_config(self) -> Dict[str, Any]:
        """Get employee-related configuration"""
        return {
            'types': self.config.employee.types,
            'probation_period': self.config.employee.probation_period,
            'notice_period': self.config.employee.notice_period,
            'required_documents': self.config.employee.required_documents,
        }
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        return {
            'platforms': self.config.system.platforms,
            'asset_types': self.config.system.asset_types,
        }
    
    def get_file_storage_config(self) -> Dict[str, Any]:
        """Get file storage configuration"""
        return {
            'upload_folder': self.config.file_storage.upload_folder,
            'max_file_size': self.config.file_storage.max_file_size,
            'allowed_extensions': self.config.file_storage.allowed_extensions,
            'use_s3': self.config.file_storage.use_s3,
            'aws_access_key_id': self.config.file_storage.aws_access_key_id,
            'aws_secret_access_key': self.config.file_storage.aws_secret_access_key,
            'aws_s3_bucket': self.config.file_storage.aws_s3_bucket,
            'aws_region': self.config.file_storage.aws_region,
        }
    
    def get_integration_config(self) -> Dict[str, Any]:
        """Get integration configuration"""
        return {
            'slack_api_token': self.config.integrations.slack_api_token,
            'google_workspace_admin_email': self.config.integrations.google_workspace_admin_email,
            'google_workspace_service_account_file': self.config.integrations.google_workspace_service_account_file,
            'razorpay_key_id': self.config.integrations.razorpay_key_id,
            'razorpay_key_secret': self.config.integrations.razorpay_key_secret,
            'enable_bgv': self.config.integrations.enable_bgv,
            'enable_auto_email': self.config.integrations.enable_auto_email,
            'enable_slack_integration': self.config.integrations.enable_slack_integration,
            'enable_google_workspace_integration': self.config.integrations.enable_google_workspace_integration,
            'enable_razorpay_integration': self.config.integrations.enable_razorpay_integration,
        }
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """Get MCP configuration"""
        return self.config.get_mcp_config()
    
    def validate_required_settings(self) -> list:
        """Validate that all required settings are present"""
        errors = []
        
        # Check critical settings
        if not self.config.security.secret_key or self.config.security.secret_key == 'your-secret-key-here':
            errors.append("SECRET_KEY must be set")
        
        if self.config.email.use_sendgrid and not self.config.email.sendgrid_api_key:
            errors.append("SENDGRID_API_KEY must be set when USE_SENDGRID is True")
        
        if self.config.file_storage.use_s3:
            if not self.config.file_storage.aws_access_key_id:
                errors.append("AWS_ACCESS_KEY_ID must be set when USE_S3 is True")
            if not self.config.file_storage.aws_secret_access_key:
                errors.append("AWS_SECRET_ACCESS_KEY must be set when USE_S3 is True")
        

        
        return errors
