"""
Base Configuration Class

Defines the core configuration structure and default values.
"""

import os
from datetime import timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class CompanyInfo:
    """Company information configuration"""
    name: str = "Rapid Innovation Pvt. Ltd."
    address: str = "Hotel North 39, Junas Wada, near River Bridge, Mandrem, Goa 403524"
    phone: str = "9823268663"
    email: str = "teamhr@rapidinnovation.com"
    website: str = "https://rapidinnovation.com"
    logo_path: Optional[str] = None


@dataclass
class HRInfo:
    """HR department information"""
    manager_name: str = "Aarushi Sharma"
    manager_designation: str = "Assistant Manager HR"
    manager_email: str = "aarushi.sharma@rapidinnovation.com"
    team_emails: List[str] = field(default_factory=lambda: [
        "teamhr@rapidinnovation.com",
        "aarushi.sharma@rapidinnovation.com"
    ])


@dataclass
class EmailConfig:
    """Email configuration settings"""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = "teamhr@rapidinnovation.com"
    smtp_password: str = ""
    smtp_use_tls: bool = True
    default_sender_email: str = "hrms@rapidinnovation.dev"
    default_sender_name: str = "Team HR - Rapid Innovation"
    
    # SendGrid Configuration
    sendgrid_api_key: str = ""
    use_sendgrid: bool = False


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "sqlite:///hr_automation.db"


@dataclass
class FileStorageConfig:
    """File storage configuration"""
    upload_folder: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: set = field(default_factory=lambda: {
        'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 
        'xls', 'xlsx', 'txt', 'zip', 'rar'
    })
    
    # AWS S3 Configuration
    use_s3: bool = False
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = "hr-automation-docs"
    aws_region: str = "us-east-1"


@dataclass
class EmployeeConfig:
    """Employee-related configuration"""
    types: Dict[str, str] = field(default_factory=lambda: {
        'full_time': 'Full Time Employee',
        'intern': 'Intern',
        'contractor': 'Contractor'
    })
    
    probation_period: Dict[str, int] = field(default_factory=lambda: {
        'full_time': 3,
        'intern': 1,
        'contractor': 1
    })
    
    notice_period: Dict[str, Any] = field(default_factory=lambda: {
        'full_time': {
            'probation': 15,
            'confirmed': 30
        },
        'intern': 7,
        'contractor': 7
    })
    
    required_documents: Dict[str, List[str]] = field(default_factory=lambda: {
        'full_time': [
            '10th Certificate',
            '12th Certificate',
            'Graduation Certificate',
            'Post Graduation Certificate (if applicable)',
            'Aadhaar Card',
            'PAN Card',
            'Passport (if available)',
            'Driving License (if available)',
            'Previous Employment Documents',
            'Last 3 Months Salary Slips',
            'Passport Size Photograph'
        ],
        'intern': [
            '10th Certificate',
            '12th Certificate',
            'Graduation Certificate',
            'Post Graduation Certificate (if applicable)',
            'Aadhaar Card',
            'PAN Card',
            'Passport Size Photograph'
        ],
        'contractor': [
            'Aadhaar Card',
            'PAN Card',
            'GST Certificate (if applicable)',
            'Previous Work Samples',
            'Passport Size Photograph'
        ]
    })


@dataclass
class SystemConfig:
    """System and platform configuration"""
    platforms: List[str] = field(default_factory=lambda: [
        'Gmail',
        'Slack',
        'TeamLogger',
        'Razorpay',
        'GitHub',
        'Jira',
        'Google Drive'
    ])
    
    asset_types: List[str] = field(default_factory=lambda: [
        'Laptop',
        'Mouse',
        'Keyboard',
        'Headphones',
        'Monitor',
        'Mobile Phone',
        'ID Card',
        'Access Card',
        'Dongle',
        'Bag'
    ])


@dataclass
class IntegrationConfig:
    """Third-party integration configuration"""
    slack_api_token: str = ""
    google_workspace_admin_email: str = ""
    google_workspace_service_account_file: str = ""
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    
    # Feature flags
    enable_bgv: bool = True
    enable_auto_email: bool = True
    enable_slack_integration: bool = False
    enable_google_workspace_integration: bool = False
    enable_razorpay_integration: bool = False





@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = "your-secret-key-here"
    session_lifetime: timedelta = field(default_factory=lambda: timedelta(hours=8))
    permanent_session_lifetime: timedelta = field(default_factory=lambda: timedelta(days=7))


@dataclass
class BusinessConfig:
    """Business logic configuration"""
    tds_percentage: int = 10
    fnf_processing_days: int = 45
    items_per_page: int = 20
    scheduler_timezone: str = "Asia/Kolkata"


class BaseConfig:
    """Base configuration class that combines all configuration sections"""
    
    def __init__(self):
        # Application Settings
        self.APP_NAME = "Rapid Innovation HR Automation"
        self.VERSION = "1.0.0"
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # Initialize configuration sections
        self.company = CompanyInfo()
        self.hr = HRInfo()
        self.email = EmailConfig()
        self.database = DatabaseConfig()
        self.file_storage = FileStorageConfig()
        self.employee = EmployeeConfig()
        self.system = SystemConfig()
        self.integrations = IntegrationConfig()

        self.security = SecurityConfig()
        self.business = BusinessConfig()
        
        # Load environment-specific overrides
        self._load_from_environment()
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        # Security
        self.security.secret_key = os.getenv('SECRET_KEY', self.security.secret_key)
        
        # Database
        self.database.url = os.getenv('DATABASE_URL', self.database.url)
        
        # Email
        self.email.smtp_server = os.getenv('SMTP_SERVER', self.email.smtp_server)
        self.email.smtp_port = int(os.getenv('SMTP_PORT', str(self.email.smtp_port)))
        self.email.smtp_username = os.getenv('SMTP_USERNAME', self.email.smtp_username)
        self.email.smtp_password = os.getenv('SMTP_PASSWORD', self.email.smtp_password)
        self.email.default_sender_email = os.getenv('DEFAULT_SENDER_EMAIL', self.email.default_sender_email)
        self.email.sendgrid_api_key = os.getenv('SENDGRID_API_KEY', self.email.sendgrid_api_key)
        self.email.use_sendgrid = os.getenv('USE_SENDGRID', 'False').lower() == 'true'
        
        # File Storage
        self.file_storage.upload_folder = os.getenv('UPLOAD_FOLDER', self.file_storage.upload_folder)
        self.file_storage.use_s3 = os.getenv('USE_S3', 'False').lower() == 'true'
        self.file_storage.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID', self.file_storage.aws_access_key_id)
        self.file_storage.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY', self.file_storage.aws_secret_access_key)
        self.file_storage.aws_s3_bucket = os.getenv('AWS_S3_BUCKET', self.file_storage.aws_s3_bucket)
        self.file_storage.aws_region = os.getenv('AWS_REGION', self.file_storage.aws_region)
        
        # Integrations
        self.integrations.slack_api_token = os.getenv('SLACK_API_TOKEN', self.integrations.slack_api_token)
        self.integrations.google_workspace_admin_email = os.getenv('GOOGLE_WORKSPACE_ADMIN_EMAIL', self.integrations.google_workspace_admin_email)
        self.integrations.google_workspace_service_account_file = os.getenv('GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE', self.integrations.google_workspace_service_account_file)
        self.integrations.razorpay_key_id = os.getenv('RAZORPAY_KEY_ID', self.integrations.razorpay_key_id)
        self.integrations.razorpay_key_secret = os.getenv('RAZORPAY_KEY_SECRET', self.integrations.razorpay_key_secret)
        

    
    def get_template_context(self) -> Dict[str, Any]:
        """Get context data for templates"""
        return {
            'config': {
                'COMPANY_NAME': self.company.name,
                'COMPANY_ADDRESS': self.company.address,
                'COMPANY_PHONE': self.company.phone,
                'COMPANY_EMAIL': self.company.email,
                'COMPANY_WEBSITE': self.company.website,
                'COMPANY_LOGO_PATH': self.company.logo_path,
                'DEFAULT_SENDER_EMAIL': self.email.default_sender_email,
                'DEFAULT_SENDER_NAME': self.email.default_sender_name,
                'HR_MANAGER_NAME': self.hr.manager_name,
                'HR_MANAGER_DESIGNATION': self.hr.manager_designation,
                'HR_MANAGER_EMAIL': self.hr.manager_email,
            }
        }
    

    
    # Backward compatibility properties
    @property
    def COMPANY_NAME(self):
        return self.company.name
    
    @property
    def COMPANY_ADDRESS(self):
        return self.company.address
    
    @property
    def COMPANY_PHONE(self):
        return self.company.phone
    
    @property
    def COMPANY_EMAIL(self):
        return self.company.email
    
    @property
    def COMPANY_WEBSITE(self):
        return self.company.website
    
    @property
    def DEFAULT_SENDER_EMAIL(self):
        return self.email.default_sender_email
    
    @property
    def DEFAULT_SENDER_NAME(self):
        return self.email.default_sender_name
    
    @property
    def HR_MANAGER_NAME(self):
        return self.hr.manager_name
    
    @property
    def HR_MANAGER_DESIGNATION(self):
        return self.hr.manager_designation
    
    @property
    def HR_MANAGER_EMAIL(self):
        return self.hr.manager_email
    
    @property
    def EMPLOYEE_TYPES(self):
        return self.employee.types
    
    @property
    def REQUIRED_DOCUMENTS(self):
        return self.employee.required_documents
    
    @property
    def PROBATION_PERIOD(self):
        return self.employee.probation_period
    
    @property
    def NOTICE_PERIOD(self):
        return self.employee.notice_period
    
    @property
    def SYSTEM_PLATFORMS(self):
        return self.system.platforms
    
    @property
    def ASSET_TYPES(self):
        return self.system.asset_types
    
    @property
    def UPLOAD_FOLDER(self):
        return self.file_storage.upload_folder
    
    @property
    def MAX_FILE_SIZE(self):
        return self.file_storage.max_file_size
    
    @property
    def ALLOWED_EXTENSIONS(self):
        return self.file_storage.allowed_extensions
    
    @property
    def DATABASE_URL(self):
        return self.database.url
    
    @property
    def SECRET_KEY(self):
        return self.security.secret_key
    
    @property
    def USE_S3(self):
        return self.file_storage.use_s3
    
    @property
    def USE_SENDGRID(self):
        return self.email.use_sendgrid

    # Email backward compatibility properties
    @property
    def SMTP_SERVER(self):
        return self.email.smtp_server

    @property
    def SMTP_PORT(self):
        return self.email.smtp_port

    @property
    def SMTP_USERNAME(self):
        return self.email.smtp_username

    @property
    def SMTP_PASSWORD(self):
        return self.email.smtp_password

    @property
    def SMTP_USE_TLS(self):
        return self.email.smtp_use_tls

    @property
    def SENDGRID_API_KEY(self):
        return self.email.sendgrid_api_key

    @property
    def EMAIL_TEMPLATE_FOLDER(self):
        return "templates/email"
