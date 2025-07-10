"""Application constants for HR Automation System"""

# Employee Status
EMPLOYEE_STATUS = {
    'ACTIVE': 'active',
    'ONBOARDING': 'onboarding',
    'OFFBOARDING': 'offboarding',
    'EXITED': 'exited'
}

# Employee Types
EMPLOYEE_TYPES = {
    'FULL_TIME': 'full_time',
    'INTERN': 'intern',
    'CONTRACTOR': 'contractor'
}

# Document Types
DOCUMENT_TYPES = {
    'EDUCATIONAL': 'educational',
    'IDENTITY': 'identity',
    'EMPLOYMENT': 'employment',
    'OTHER': 'other'
}

# Document Names by Employee Type
REQUIRED_DOCUMENTS = {
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

# System Platforms
SYSTEM_PLATFORMS = {
    'EMAIL': 'Gmail',
    'COMMUNICATION': 'Slack',
    'TIME_TRACKING': 'TeamLogger',
    'PAYMENT': 'Razorpay',
    'VERSION_CONTROL': 'GitHub',
    'PROJECT_MANAGEMENT': 'Jira',
    'STORAGE': 'Google Drive'
}

# Asset Types
ASSET_TYPES = [
    'Laptop',
    'Desktop',
    'Monitor',
    'Keyboard',
    'Mouse',
    'Headphones',
    'Webcam',
    'Mobile Phone',
    'Tablet',
    'Dongle',
    'Charger',
    'Laptop Bag',
    'ID Card',
    'Access Card',
    'Keys',
    'Other'
]

# Exit Types
EXIT_TYPES = {
    'RESIGNATION': 'resignation',
    'TERMINATION': 'termination',
    'END_OF_CONTRACT': 'end_of_contract',
    'RETIREMENT': 'retirement',
    'ABSCONDING': 'absconding'
}

# Email Types
EMAIL_TYPES = {
    'DOCUMENT_REQUEST': 'document_request',
    'OFFER_LETTER': 'offer_letter',
    'APPOINTMENT_LETTER': 'appointment_letter',
    'WELCOME_ONBOARD': 'welcome_onboard',
    'SYSTEM_ACCESS': 'system_access_granted',
    'BGV_REQUEST': 'bgv_request',
    'BGV_NOTIFICATION': 'bgv_notification',
    'EXIT_CONFIRMATION': 'exit_confirmation',
    'MANAGER_NOTIFICATION': 'manager_exit_notification',
    'ASSET_REMINDER': 'asset_return_reminder',
    'ACCESS_REVOCATION': 'access_revocation_confirmation',
    'FNF_STATEMENT': 'fnf_statement',
    'EXPERIENCE_LETTER': 'experience_letter',
    'GENERAL': 'general'
}

# Task Status
TASK_STATUS = {
    'PENDING': 'pending',
    'IN_PROGRESS': 'in_progress',
    'COMPLETED': 'completed',
    'BLOCKED': 'blocked',
    'CANCELLED': 'cancelled'
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

# Common Designations
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

# Allowed File Extensions
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

# Notification Types
NOTIFICATION_TYPES = {
    'SUCCESS': 'success',
    'ERROR': 'error',
    'WARNING': 'warning',
    'INFO': 'info',
    'ONBOARDING': 'onboarding',
    'OFFBOARDING': 'offboarding',
    'DOCUMENT': 'document',
    'SYSTEM': 'system',
    'REMINDER': 'reminder'
}

# Report Types
REPORT_TYPES = {
    'EMPLOYEE_SUMMARY': 'employee_summary',
    'ONBOARDING_STATUS': 'onboarding_status',
    'OFFBOARDING_STATUS': 'offboarding_status',
    'DOCUMENT_STATUS': 'document_status',
    'ASSET_INVENTORY': 'asset_inventory',
    'SYSTEM_ACCESS': 'system_access',
    'MONTHLY_JOININGS': 'monthly_joinings',
    'MONTHLY_EXITS': 'monthly_exits',
    'PENDING_TASKS': 'pending_tasks'
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

# CTC Components (percentages)
CTC_COMPONENTS = {
    'basic': 0.40,           # 40% of CTC
    'hra': 0.50,             # 50% of Basic (20% of CTC)
    'medical_allowance': 15000,  # Fixed amount
    'books_periodical': 12000,   # Fixed amount
    'health_club': 6000,         # Fixed amount
    'internet_telephone': 24000, # Fixed amount
    'pf_employer': 0.12          # 12% of Basic
}

# Leave Types
LEAVE_TYPES = {
    'CASUAL': 'casual_leave',
    'SICK': 'sick_leave',
    'EARNED': 'earned_leave',
    'LOSS_OF_PAY': 'loss_of_pay',
    'COMP_OFF': 'compensatory_off',
    'MATERNITY': 'maternity_leave',
    'PATERNITY': 'paternity_leave'
}

# Gender Options
GENDER_OPTIONS = {
    'MALE': 'male',
    'FEMALE': 'female',
    'OTHER': 'other',
    'PREFER_NOT_TO_SAY': 'prefer_not_to_say'
}