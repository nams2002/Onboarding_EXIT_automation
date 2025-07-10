"""
Consolidated Constants

All application constants in one place, organized by domain.
This replaces the scattered constants from utils/constants.py and config.py
"""

from typing import Dict, List, Any
from enum import Enum


# Employee Status
class EmployeeStatus(Enum):
    ACTIVE = 'active'
    ONBOARDING = 'onboarding'
    OFFBOARDING = 'offboarding'
    EXITED = 'exited'


# Employee Types
class EmployeeType(Enum):
    FULL_TIME = 'full_time'
    INTERN = 'intern'
    CONTRACTOR = 'contractor'


# Document Types
class DocumentType(Enum):
    EDUCATIONAL = 'educational'
    IDENTITY = 'identity'
    EMPLOYMENT = 'employment'
    OTHER = 'other'


# Exit Types
class ExitType(Enum):
    RESIGNATION = 'resignation'
    TERMINATION = 'termination'
    END_OF_CONTRACT = 'end_of_contract'
    RETIREMENT = 'retirement'
    ABSCONDING = 'absconding'


# Email Types
class EmailType(Enum):
    DOCUMENT_REQUEST = 'document_request'
    OFFER_LETTER = 'offer_letter'
    APPOINTMENT_LETTER = 'appointment_letter'
    WELCOME_ONBOARD = 'welcome_onboard'
    SYSTEM_ACCESS = 'system_access_granted'
    BGV_REQUEST = 'bgv_request'
    BGV_NOTIFICATION = 'bgv_notification'
    EXIT_CONFIRMATION = 'exit_confirmation'
    MANAGER_NOTIFICATION = 'manager_exit_notification'
    ASSET_REMINDER = 'asset_return_reminder'
    ACCESS_REVOCATION = 'access_revocation_confirmation'
    FNF_STATEMENT = 'fnf_statement'
    EXPERIENCE_LETTER = 'experience_letter'
    GENERAL = 'general'


# Task Status
class TaskStatus(Enum):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    BLOCKED = 'blocked'
    CANCELLED = 'cancelled'


# Notification Types
class NotificationType(Enum):
    SUCCESS = 'success'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'
    ONBOARDING = 'onboarding'
    OFFBOARDING = 'offboarding'
    DOCUMENT = 'document'
    SYSTEM = 'system'
    REMINDER = 'reminder'


# Report Types
class ReportType(Enum):
    EMPLOYEE_SUMMARY = 'employee_summary'
    ONBOARDING_STATUS = 'onboarding_status'
    OFFBOARDING_STATUS = 'offboarding_status'
    DOCUMENT_STATUS = 'document_status'
    ASSET_INVENTORY = 'asset_inventory'
    SYSTEM_ACCESS = 'system_access'
    MONTHLY_JOININGS = 'monthly_joinings'
    MONTHLY_EXITS = 'monthly_exits'
    PENDING_TASKS = 'pending_tasks'


# Leave Types
class LeaveType(Enum):
    CASUAL = 'casual_leave'
    SICK = 'sick_leave'
    EARNED = 'earned_leave'
    LOSS_OF_PAY = 'loss_of_pay'
    COMP_OFF = 'compensatory_off'
    MATERNITY = 'maternity_leave'
    PATERNITY = 'paternity_leave'


# Gender Options
class Gender(Enum):
    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'
    PREFER_NOT_TO_SAY = 'prefer_not_to_say'


# Document Names by Employee Type (Detailed Structure)
REQUIRED_DOCUMENTS_DETAILED = {
    'full_time': {
        'educational': [
            '10th Certificate',
            '12th Certificate',
            'Graduation Certificate',
            'Post Graduation Certificate'
        ],
        'identity': [
            'Aadhaar Card',
            'PAN Card',
            'Passport',
            'Driving License'
        ],
        'employment': [
            'Previous Employment - Appointment Letter',
            'Previous Employment - Relieving Letter',
            'Previous Employment - Last 3 Salary Slips',
            'Previous Employment - Experience Letter'
        ],
        'other': [
            'Passport Size Photograph'
        ]
    },
    'intern': {
        'educational': [
            '10th Certificate',
            '12th Certificate',
            'Graduation Certificate',
            'Post Graduation Certificate'
        ],
        'identity': [
            'Aadhaar Card',
            'PAN Card'
        ],
        'other': [
            'Passport Size Photograph'
        ]
    },
    'contractor': {
        'identity': [
            'Aadhaar Card',
            'PAN Card',
            'GST Certificate'
        ],
        'other': [
            'Passport Size Photograph',
            'Previous Work Samples'
        ]
    }
}

# Indian States (for address validation)
INDIAN_STATES = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
    'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
    'Andaman and Nicobar Islands', 'Chandigarh', 'Dadra and Nagar Haveli and Daman and Diu',
    'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
]

# Department List
DEPARTMENTS = [
    'Engineering',
    'Product',
    'Design',
    'Marketing',
    'Sales',
    'Human Resources',
    'Finance',
    'Operations',
    'Customer Success',
    'Quality Assurance',
    'Research & Development',
    'Legal',
    'Administration'
]

# Common Designations by Department
DESIGNATIONS = {
    'Engineering': [
        'Software Engineer',
        'Senior Software Engineer',
        'Lead Software Engineer',
        'Engineering Manager',
        'Technical Architect',
        'DevOps Engineer',
        'QA Engineer',
        'Data Engineer',
        'ML Engineer'
    ],
    'Product': [
        'Product Manager',
        'Senior Product Manager',
        'Product Owner',
        'Product Analyst'
    ],
    'Design': [
        'UI/UX Designer',
        'Senior Designer',
        'Design Lead',
        'Graphic Designer'
    ],
    'Marketing': [
        'Marketing Executive',
        'Marketing Manager',
        'Content Writer',
        'SEO Specialist',
        'Social Media Manager'
    ],
    'Sales': [
        'Sales Executive',
        'Sales Manager',
        'Business Development Executive',
        'Business Development Manager'
    ],
    'HR': [
        'HR Executive',
        'HR Manager',
        'Talent Acquisition Specialist',
        'HR Business Partner'
    ]
}

# File Size Limits (in bytes)
FILE_SIZE_LIMITS = {
    'DOCUMENT': 10 * 1024 * 1024,  # 10 MB
    'IMAGE': 5 * 1024 * 1024,       # 5 MB
    'BULK_UPLOAD': 50 * 1024 * 1024 # 50 MB
}

# Allowed File Extensions by Category
ALLOWED_EXTENSIONS = {
    'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
    'images': {'jpg', 'jpeg', 'png', 'gif', 'bmp'},
    'spreadsheets': {'xls', 'xlsx', 'csv'},
    'archives': {'zip', 'rar', '7z'}
}

# Date Formats
DATE_FORMATS = {
    'display': '%d %b %Y',      # 15 Jan 2024
    'input': '%Y-%m-%d',        # 2024-01-15
    'filename': '%Y%m%d',       # 20240115
    'timestamp': '%Y%m%d_%H%M%S' # 20240115_143022
}

# Regex Patterns
REGEX_PATTERNS = {
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'phone_india': r'^(\+91)?[6-9]\d{9}$',
    'pan': r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$',
    'aadhaar': r'^\d{12}$',
    'employee_id': r'^[A-Z]{2}\d{4,}$',
    'gst': r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
}

# Default Values
DEFAULTS = {
    'PROBATION_PERIOD_MONTHS': 3,
    'NOTICE_PERIOD_DAYS': 30,
    'FNF_PROCESSING_DAYS': 45,
    'BGV_PROCESSING_DAYS': 10,
    'DOCUMENT_RETENTION_DAYS': 365,
    'PASSWORD_EXPIRY_DAYS': 90,
    'SESSION_TIMEOUT_MINUTES': 30
}

# Error Messages
ERROR_MESSAGES = {
    'UNAUTHORIZED': 'You are not authorized to perform this action',
    'NOT_FOUND': 'The requested resource was not found',
    'INVALID_INPUT': 'Invalid input provided',
    'DATABASE_ERROR': 'An error occurred while processing your request',
    'FILE_UPLOAD_ERROR': 'Error uploading file',
    'EMAIL_SEND_ERROR': 'Error sending email',
    'DUPLICATE_ENTRY': 'A record with this information already exists',
    'DEPENDENCY_ERROR': 'Cannot complete action due to dependencies',
    'VALIDATION_ERROR': 'Validation failed for the provided data'
}

# Success Messages
SUCCESS_MESSAGES = {
    'CREATED': 'Record created successfully',
    'UPDATED': 'Record updated successfully',
    'DELETED': 'Record deleted successfully',
    'EMAIL_SENT': 'Email sent successfully',
    'FILE_UPLOADED': 'File uploaded successfully',
    'TASK_COMPLETED': 'Task completed successfully',
    'PROCESS_INITIATED': 'Process initiated successfully',
    'ACCESS_GRANTED': 'Access granted successfully',
    'ACCESS_REVOKED': 'Access revoked successfully'
}

# CTC Components (percentages and fixed amounts)
CTC_COMPONENTS = {
    'basic': 0.40,           # 40% of CTC
    'hra': 0.50,             # 50% of Basic (20% of CTC)
    'medical_allowance': 15000,  # Fixed amount
    'books_periodical': 12000,   # Fixed amount
    'health_club': 6000,         # Fixed amount
    'internet_telephone': 24000, # Fixed amount
    'pf_employer': 0.12          # 12% of Basic
}

# HTTP Status Codes (commonly used)
HTTP_STATUS = {
    'OK': 200,
    'CREATED': 201,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'CONFLICT': 409,
    'INTERNAL_SERVER_ERROR': 500
}

# Template Names
TEMPLATE_NAMES = {
    'emails': {
        'base': 'emails/base_template.html',
        'document_request': 'emails/initial_document_request.html',
        'welcome_onboard': 'emails/welcome_onboard.html',
        'exit_initiation': 'emails/exit_initiation.html',
        'asset_return': 'emails/asset_return.html'
    },
    'letters': {
        'appointment': 'letters/appointment_letter.html',
        'offer': 'letters/offer_letter.html',
        'internship': 'letters/internship_letter.html',
        'contract': 'letters/contract_agreement.html',
        'experience': 'letters/experience_letter.html',
        'internship_certificate': 'letters/internship_certificate.html'
    }
}

# API Endpoints
API_ENDPOINTS = {
    'employees': '/api/employees',
    'documents': '/api/documents',
    'onboarding': '/api/onboarding',
    'offboarding': '/api/offboarding',
    'reports': '/api/reports',
    'config': '/api/config'
}

# Cache Keys
CACHE_KEYS = {
    'config': 'app_config',
    'employee_types': 'employee_types',
    'departments': 'departments',
    'designations': 'designations',
    'system_platforms': 'system_platforms'
}

# Logging Levels
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# Time Zones
TIMEZONES = {
    'IST': 'Asia/Kolkata',
    'UTC': 'UTC',
    'EST': 'America/New_York',
    'PST': 'America/Los_Angeles'
}

# Currency Codes
CURRENCY_CODES = {
    'INR': 'Indian Rupee',
    'USD': 'US Dollar',
    'EUR': 'Euro',
    'GBP': 'British Pound'
}

# Priority Levels
PRIORITY_LEVELS = {
    'LOW': 1,
    'MEDIUM': 2,
    'HIGH': 3,
    'URGENT': 4,
    'CRITICAL': 5
}
