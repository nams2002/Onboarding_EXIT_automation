"""
Environment-specific configurations

Handles different configurations for development, staging, and production environments.
"""

import os
from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    
    def __init__(self):
        super().__init__()
        self.DEBUG = True
        
        # Override for development
        self.database.url = os.getenv('DATABASE_URL', 'sqlite:///hr_automation_dev.db')
        self.email.smtp_password = os.getenv('SMTP_PASSWORD', '')  # Required in dev
        
        # Development-specific settings
        self.file_storage.upload_folder = 'uploads_dev'
        self.security.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')


class StagingConfig(BaseConfig):
    """Staging environment configuration"""
    
    def __init__(self):
        super().__init__()
        self.DEBUG = False
        
        # Staging-specific settings
        self.database.url = os.getenv('DATABASE_URL', 'sqlite:///hr_automation_staging.db')
        self.file_storage.upload_folder = 'uploads_staging'
        
        # More restrictive settings for staging
        self.file_storage.max_file_size = 5 * 1024 * 1024  # 5MB for staging


class ProductionConfig(BaseConfig):
    """Production environment configuration"""
    
    def __init__(self):
        super().__init__()
        self.DEBUG = False
        
        # Production should use environment variables
        self.database.url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/hr_automation')
        
        # Production-specific settings
        self.file_storage.use_s3 = True  # Prefer S3 in production
        self.email.use_sendgrid = True   # Prefer SendGrid in production
        
        # Security settings for production
        self.security.secret_key = os.getenv('SECRET_KEY')  # Must be set in production
        if not self.security.secret_key or self.security.secret_key == 'your-secret-key-here':
            raise ValueError("SECRET_KEY must be set in production environment")


def get_environment() -> str:
    """Detect the current environment"""
    return os.getenv('ENVIRONMENT', os.getenv('FLASK_ENV', 'development')).lower()


def get_config() -> BaseConfig:
    """Get configuration based on current environment"""
    env = get_environment()
    
    config_map = {
        'development': DevelopmentConfig,
        'dev': DevelopmentConfig,
        'staging': StagingConfig,
        'stage': StagingConfig,
        'production': ProductionConfig,
        'prod': ProductionConfig,
    }
    
    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()
