"""
Configuration Validators

Validates configuration settings and provides helpful error messages.
"""

import os
import re
from typing import List, Dict, Any
from .base import BaseConfig


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Check if it's a valid Indian phone number
    return len(digits) >= 10


def validate_config(config: BaseConfig) -> List[str]:
    """Validate configuration and return list of errors"""
    errors = []
    
    # Validate company information
    if not config.company.name:
        errors.append("Company name is required")
    
    if not config.company.address:
        errors.append("Company address is required")
    
    if config.company.email and not validate_email(config.company.email):
        errors.append(f"Invalid company email format: {config.company.email}")
    
    if config.company.website and not validate_url(config.company.website):
        errors.append(f"Invalid company website URL: {config.company.website}")
    
    if config.company.phone and not validate_phone(config.company.phone):
        errors.append(f"Invalid company phone number: {config.company.phone}")
    
    # Validate HR information
    if not config.hr.manager_name:
        errors.append("HR manager name is required")
    
    if not config.hr.manager_email:
        errors.append("HR manager email is required")
    elif not validate_email(config.hr.manager_email):
        errors.append(f"Invalid HR manager email format: {config.hr.manager_email}")
    
    if not config.hr.manager_designation:
        errors.append("HR manager designation is required")
    
    # Validate email configuration
    if not config.email.default_sender_email:
        errors.append("Default sender email is required")
    elif not validate_email(config.email.default_sender_email):
        errors.append(f"Invalid default sender email format: {config.email.default_sender_email}")
    
    if not config.email.default_sender_name:
        errors.append("Default sender name is required")
    
    if config.email.smtp_username and not validate_email(config.email.smtp_username):
        errors.append(f"Invalid SMTP username format: {config.email.smtp_username}")
    
    if config.email.smtp_port and (config.email.smtp_port < 1 or config.email.smtp_port > 65535):
        errors.append(f"Invalid SMTP port: {config.email.smtp_port}")
    
    # Validate SendGrid configuration
    if config.email.use_sendgrid and not config.email.sendgrid_api_key:
        errors.append("SendGrid API key is required when USE_SENDGRID is True")
    
    # Validate database configuration
    if not config.database.url:
        errors.append("Database URL is required")
    
    # Validate file storage configuration
    if not config.file_storage.upload_folder:
        errors.append("Upload folder is required")
    
    if config.file_storage.max_file_size <= 0:
        errors.append("Max file size must be greater than 0")
    
    if not config.file_storage.allowed_extensions:
        errors.append("At least one allowed file extension is required")
    
    # Validate AWS S3 configuration
    if config.file_storage.use_s3:
        if not config.file_storage.aws_access_key_id:
            errors.append("AWS Access Key ID is required when USE_S3 is True")
        
        if not config.file_storage.aws_secret_access_key:
            errors.append("AWS Secret Access Key is required when USE_S3 is True")
        
        if not config.file_storage.aws_s3_bucket:
            errors.append("AWS S3 bucket is required when USE_S3 is True")
        
        if not config.file_storage.aws_region:
            errors.append("AWS region is required when USE_S3 is True")
    
    # Validate security configuration
    if not config.security.secret_key:
        errors.append("Secret key is required")
    elif config.security.secret_key == 'your-secret-key-here':
        errors.append("Secret key must be changed from default value")
    elif len(config.security.secret_key) < 32:
        errors.append("Secret key should be at least 32 characters long")
    
    # Validate employee configuration
    if not config.employee.types:
        errors.append("Employee types configuration is required")
    
    if not config.employee.required_documents:
        errors.append("Required documents configuration is required")
    
    # Validate system configuration
    if not config.system.platforms:
        errors.append("System platforms configuration is required")
    
    if not config.system.asset_types:
        errors.append("Asset types configuration is required")
    
    # MCP functionality removed - no validation needed
    
    # Validate business configuration
    if config.business.tds_percentage < 0 or config.business.tds_percentage > 100:
        errors.append("TDS percentage must be between 0 and 100")
    
    if config.business.fnf_processing_days <= 0:
        errors.append("FnF processing days must be positive")
    
    if config.business.items_per_page <= 0:
        errors.append("Items per page must be positive")
    
    # Validate integration configuration
    for email in config.hr.team_emails:
        if not validate_email(email):
            errors.append(f"Invalid HR team email format: {email}")
    
    return errors


def validate_template_context(context: Dict[str, Any]) -> List[str]:
    """Validate template context for completeness"""
    errors = []
    required_keys = [
        'COMPANY_NAME',
        'COMPANY_ADDRESS',
        'COMPANY_EMAIL',
        'DEFAULT_SENDER_EMAIL',
        'HR_MANAGER_NAME',
        'HR_MANAGER_DESIGNATION',
    ]
    
    config_dict = context.get('config', {})
    
    for key in required_keys:
        if key not in config_dict or not config_dict[key]:
            errors.append(f"Template context missing required key: {key}")
    
    return errors


def validate_environment_variables() -> List[str]:
    """Validate critical environment variables"""
    errors = []
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        errors.append(".env file not found - copy .env.example to .env and configure")
    
    # Check critical environment variables
    critical_vars = ['SECRET_KEY']
    
    for var in critical_vars:
        if not os.getenv(var):
            errors.append(f"Environment variable {var} is not set")
    
    return errors


def get_validation_summary(config: BaseConfig) -> Dict[str, Any]:
    """Get a comprehensive validation summary"""
    config_errors = validate_config(config)
    template_errors = validate_template_context(config.get_template_context())
    env_errors = validate_environment_variables()
    
    all_errors = config_errors + template_errors + env_errors
    
    return {
        'is_valid': len(all_errors) == 0,
        'total_errors': len(all_errors),
        'config_errors': config_errors,
        'template_errors': template_errors,
        'environment_errors': env_errors,
        'all_errors': all_errors,
        'summary': {
            'config_valid': len(config_errors) == 0,
            'template_valid': len(template_errors) == 0,
            'environment_valid': len(env_errors) == 0,
        }
    }
