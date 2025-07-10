import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables
load_dotenv()

class Config:
    """Application configuration settings"""
    
    # Application Settings
    APP_NAME = "Rapid Innovation HR Automation"
    VERSION = "1.0.0"
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Database Configuration
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'sqlite:///hr_automation.db'  # Use SQLite for development
    )
    
    # Email Configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'teamhr@rapidinnovation.com')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_USE_TLS = True
    DEFAULT_SENDER_EMAIL = os.getenv('DEFAULT_SENDER_EMAIL', 'hrms@rapidinnovation.dev')
    DEFAULT_SENDER_NAME = "Team HR - Rapid Innovation"
    
    # SendGrid Configuration (Alternative to SMTP)
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
    USE_SENDGRID = os.getenv('USE_SENDGRID', 'False').lower() == 'true'
    
    # File Storage Configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 
        'xls', 'xlsx', 'txt', 'zip', 'rar'
    }
    
    # AWS S3 Configuration (Optional)
    USE_S3 = os.getenv('USE_S3', 'False').lower() == 'true'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'hr-automation-docs')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Company Information
    COMPANY_NAME = "Rapid Innovation Pvt. Ltd."
    COMPANY_ADDRESS = "Hotel North 39, Junas Wada, near River Bridge, Mandrem, Goa 403524"
    COMPANY_PHONE = "9823268663"
    COMPANY_EMAIL = "teamhr@rapidinnovation.com"
    COMPANY_WEBSITE = "https://rapidinnovation.com"
    
    # HR Configuration
    HR_MANAGER_NAME = "Aarushi Sharma"
    HR_MANAGER_DESIGNATION = "Assistant Manager HR"
    HR_MANAGER_EMAIL = "aarushi.sharma@rapidinnovation.com"

    # Team Email Configurations for Internal Notifications
    IT_TEAM_EMAILS = [
        "it@rapidinnovation.com",
        "tech@rapidinnovation.com"
    ]

    HR_TEAM_EMAILS = [
        "teamhr@rapidinnovation.com",
        "aarushi.sharma@rapidinnovation.com"
    ]
    
    # Employee Types
    EMPLOYEE_TYPES = {
        'full_time': 'Full Time Employee',
        'intern': 'Intern',
        'contractor': 'Contractor'
    }
    
    # Document Types
    REQUIRED_DOCUMENTS = {
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
    }
    
    # Probation Period (in months)
    PROBATION_PERIOD = {
        'full_time': 3,
        'intern': 1,
        'contractor': 1
    }
    
    # Notice Period (in days)
    NOTICE_PERIOD = {
        'full_time': {
            'probation': 15,
            'confirmed': 30
        },
        'intern': 7,
        'contractor': 7
    }
    
    # System Access Platforms
    SYSTEM_PLATFORMS = [
        'Gmail',
        'Slack',
        'TeamLogger',
        'Razorpay',
        'GitHub',
        'Jira',
        'Google Drive'
    ]
    
    # Asset Types
    ASSET_TYPES = [
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
    ]
    
    # Email Templates Configuration
    EMAIL_TEMPLATE_FOLDER = 'templates/emails'
    LETTER_TEMPLATE_FOLDER = 'templates/letters'
    
    # API Keys for Third-party Services
    SLACK_API_TOKEN = os.getenv('SLACK_API_TOKEN', '')
    GOOGLE_WORKSPACE_ADMIN_EMAIL = os.getenv('GOOGLE_WORKSPACE_ADMIN_EMAIL', '')
    GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE', '')
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')

    # OpenAI Configuration removed
    
    # Session Configuration
    SESSION_LIFETIME = timedelta(hours=8)
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Background Job Configuration
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = 'Asia/Kolkata'
    
    # Feature Flags
    ENABLE_BGV = True
    ENABLE_AUTO_EMAIL = True
    ENABLE_SLACK_INTEGRATION = False
    ENABLE_GOOGLE_WORKSPACE_INTEGRATION = False
    ENABLE_RAZORPAY_INTEGRATION = False


    
    # Tax Configuration
    TDS_PERCENTAGE = 10  # For contractors under Section 194J
    
    # FnF Settlement
    FNF_PROCESSING_DAYS = 45  # 30-45 days as mentioned in documents
    


    @classmethod
    def validate_config(cls):
        """Validate critical configuration settings"""
        errors = []

        if not cls.SECRET_KEY or cls.SECRET_KEY == 'your-secret-key-here':
            errors.append("SECRET_KEY must be set in environment variables")

        if cls.USE_SENDGRID and not cls.SENDGRID_API_KEY:
            errors.append("SENDGRID_API_KEY must be set when USE_SENDGRID is True")

        if cls.USE_S3:
            if not cls.AWS_ACCESS_KEY_ID or not cls.AWS_SECRET_ACCESS_KEY:
                errors.append("AWS credentials must be set when USE_S3 is True")



        return errors

# Create config instance
config = Config()