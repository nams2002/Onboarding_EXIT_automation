import re
from datetime import date, datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class Validators:
    """Collection of validation functions for HR system"""
    
    @staticmethod
    def validate_email(email: str) -> Dict[str, Any]:
        """Validate email format"""
        if not email:
            return {'valid': False, 'message': 'Email is required'}
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email.strip()):
            return {'valid': False, 'message': 'Invalid email format'}
        
        return {'valid': True, 'message': 'Valid email'}
    
    @staticmethod
    def validate_phone(phone: str, country: str = 'IN') -> Dict[str, Any]:
        """Validate phone number format"""
        if not phone:
            return {'valid': False, 'message': 'Phone number is required'}
        
        # Remove spaces, hyphens, and parentheses
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        if country == 'IN':
            # Indian phone number validation
            pattern = r'^(\+91)?[6-9]\d{9}$'
            if not re.match(pattern, cleaned_phone):
                return {'valid': False, 'message': 'Invalid Indian phone number. Must be 10 digits starting with 6-9'}
        else:
            # Generic international format
            pattern = r'^\+?[1-9]\d{7,14}$'
            if not re.match(pattern, cleaned_phone):
                return {'valid': False, 'message': 'Invalid phone number format'}
        
        return {'valid': True, 'message': 'Valid phone number', 'cleaned': cleaned_phone}
    
    @staticmethod
    def validate_pan(pan: str) -> Dict[str, Any]:
        """Validate Indian PAN card format"""
        if not pan:
            return {'valid': False, 'message': 'PAN is required'}
        
        pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        if not re.match(pattern, pan.upper()):
            return {'valid': False, 'message': 'Invalid PAN format. Should be like ABCDE1234F'}
        
        return {'valid': True, 'message': 'Valid PAN', 'formatted': pan.upper()}
    
    @staticmethod
    def validate_aadhaar(aadhaar: str) -> Dict[str, Any]:
        """Validate Indian Aadhaar number format"""
        if not aadhaar:
            return {'valid': False, 'message': 'Aadhaar number is required'}
        
        # Remove spaces
        cleaned_aadhaar = aadhaar.replace(' ', '')
        
        # Check if it's 12 digits
        if not re.match(r'^\d{12}$', cleaned_aadhaar):
            return {'valid': False, 'message': 'Aadhaar must be 12 digits'}
        
        # Verhoeff algorithm for checksum validation (simplified)
        # In production, implement full Verhoeff algorithm
        return {'valid': True, 'message': 'Valid Aadhaar format', 'cleaned': cleaned_aadhaar}
    
    @staticmethod
    def validate_name(name: str, field_name: str = 'Name') -> Dict[str, Any]:
        """Validate name (only alphabets and spaces)"""
        if not name:
            return {'valid': False, 'message': f'{field_name} is required'}
        
        if len(name.strip()) < 2:
            return {'valid': False, 'message': f'{field_name} must be at least 2 characters'}
        
        if len(name) > 100:
            return {'valid': False, 'message': f'{field_name} must not exceed 100 characters'}
        
        # Allow alphabets, spaces, dots, and hyphens
        if not re.match(r'^[a-zA-Z\s\.\-]+$', name):
            return {'valid': False, 'message': f'{field_name} can only contain letters, spaces, dots, and hyphens'}
        
        return {'valid': True, 'message': f'Valid {field_name}', 'formatted': ' '.join(name.split())}
    
    @staticmethod
    def validate_date(date_value: Any, field_name: str = 'Date',
                     min_date: Optional[date] = None,
                     max_date: Optional[date] = None) -> Dict[str, Any]:
        """Validate date and check range"""
        if not date_value:
            return {'valid': False, 'message': f'{field_name} is required'}
        
        # Convert string to date if needed
        if isinstance(date_value, str):
            try:
                date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
            except ValueError:
                return {'valid': False, 'message': f'Invalid date format. Use YYYY-MM-DD'}
        
        # Check date range
        if min_date and date_value < min_date:
            return {'valid': False, 'message': f'{field_name} cannot be before {min_date}'}
        
        if max_date and date_value > max_date:
            return {'valid': False, 'message': f'{field_name} cannot be after {max_date}'}
        
        return {'valid': True, 'message': f'Valid {field_name}', 'date': date_value}
    
    @staticmethod
    def validate_salary(amount: Any, field_name: str = 'Salary',
                       min_amount: float = 0,
                       max_amount: float = 10000000) -> Dict[str, Any]:
        """Validate salary/amount"""
        if amount is None:
            return {'valid': False, 'message': f'{field_name} is required'}
        
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return {'valid': False, 'message': f'{field_name} must be a valid number'}
        
        if amount < min_amount:
            return {'valid': False, 'message': f'{field_name} must be at least {min_amount}'}
        
        if amount > max_amount:
            return {'valid': False, 'message': f'{field_name} cannot exceed {max_amount}'}
        
        return {'valid': True, 'message': f'Valid {field_name}', 'amount': amount}
    
    @staticmethod
    def validate_employee_id(employee_id: str) -> Dict[str, Any]:
        """Validate employee ID format"""
        if not employee_id:
            return {'valid': False, 'message': 'Employee ID is required'}
        
        # Assuming format: RI1001 (prefix + 4 digits)
        pattern = r'^[A-Z]{2}\d{4,}$'
        if not re.match(pattern, employee_id.upper()):
            return {'valid': False, 'message': 'Invalid Employee ID format'}
        
        return {'valid': True, 'message': 'Valid Employee ID', 'formatted': employee_id.upper()}
    
    @staticmethod
    def validate_file(file_data: Any, allowed_extensions: set,
                     max_size_mb: float = 10) -> Dict[str, Any]:
        """Validate uploaded file"""
        if not file_data:
            return {'valid': False, 'message': 'No file uploaded'}
        
        # Check file extension
        filename = getattr(file_data, 'name', '')
        if not filename:
            return {'valid': False, 'message': 'Invalid file'}
        
        extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if extension not in allowed_extensions:
            return {
                'valid': False,
                'message': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'
            }
        
        # Check file size
        file_size = len(file_data.getvalue()) if hasattr(file_data, 'getvalue') else 0
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return {
                'valid': False,
                'message': f'File size exceeds {max_size_mb}MB limit'
            }
        
        return {
            'valid': True,
            'message': 'Valid file',
            'extension': extension,
            'size': file_size
        }
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        if not password:
            return {'valid': False, 'message': 'Password is required'}
        
        errors = []
        
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', password):
            errors.append('Password must contain at least one number')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Password must contain at least one special character')
        
        if errors:
            return {'valid': False, 'message': '; '.join(errors)}
        
        return {'valid': True, 'message': 'Strong password'}
    
    @staticmethod
    def validate_employee_type(employee_type: str) -> Dict[str, Any]:
        """Validate employee type"""
        valid_types = ['full_time', 'intern', 'contractor']
        
        if not employee_type:
            return {'valid': False, 'message': 'Employee type is required'}
        
        if employee_type not in valid_types:
            return {
                'valid': False,
                'message': f'Invalid employee type. Must be one of: {", ".join(valid_types)}'
            }
        
        return {'valid': True, 'message': 'Valid employee type'}
    
    @staticmethod
    def validate_notice_period(notice_days: int, employee_type: str,
                             is_probation: bool = False) -> Dict[str, Any]:
        """Validate notice period based on employee type"""
        from config import config
        
        if notice_days < 0:
            return {'valid': False, 'message': 'Notice period cannot be negative'}
        
        # Get required notice period
        if employee_type == 'full_time':
            required = config.NOTICE_PERIOD['full_time']['probation' if is_probation else 'confirmed']
        else:
            required = config.NOTICE_PERIOD.get(employee_type, 0)
        
        if notice_days < required:
            return {
                'valid': False,
                'message': f'Notice period is less than required {required} days',
                'short_notice': True,
                'shortage_days': required - notice_days
            }
        
        return {'valid': True, 'message': 'Valid notice period', 'short_notice': False}
    
    @staticmethod
    def validate_onboarding_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete onboarding data"""
        errors = []
        
        # Validate required fields
        required_fields = {
            'full_name': 'Full Name',
            'email_personal': 'Personal Email',
            'phone': 'Phone Number',
            'employee_type': 'Employee Type',
            'designation': 'Designation',
            'department': 'Department',
            'reporting_manager': 'Reporting Manager',
            'date_of_joining': 'Date of Joining'
        }
        
        for field, label in required_fields.items():
            if not data.get(field):
                errors.append(f'{label} is required')
        
        # Validate specific fields
        if data.get('email_personal'):
            email_result = Validators.validate_email(data['email_personal'])
            if not email_result['valid']:
                errors.append(email_result['message'])
        
        if data.get('phone'):
            phone_result = Validators.validate_phone(data['phone'])
            if not phone_result['valid']:
                errors.append(phone_result['message'])
        
        if data.get('employee_type'):
            type_result = Validators.validate_employee_type(data['employee_type'])
            if not type_result['valid']:
                errors.append(type_result['message'])
        
        # Validate compensation based on employee type
        if data.get('employee_type') == 'full_time':
            if not data.get('ctc'):
                errors.append('Annual CTC is required for full-time employees')
            else:
                salary_result = Validators.validate_salary(data['ctc'], 'Annual CTC', min_amount=100000)
                if not salary_result['valid']:
                    errors.append(salary_result['message'])
        
        elif data.get('employee_type') == 'intern':
            if not data.get('stipend'):
                errors.append('Monthly stipend is required for interns')
            else:
                stipend_result = Validators.validate_salary(data['stipend'], 'Stipend', min_amount=5000, max_amount=50000)
                if not stipend_result['valid']:
                    errors.append(stipend_result['message'])
        
        elif data.get('employee_type') == 'contractor':
            if not data.get('hourly_rate'):
                errors.append('Hourly rate is required for contractors')
            else:
                rate_result = Validators.validate_salary(data['hourly_rate'], 'Hourly Rate', min_amount=100, max_amount=5000)
                if not rate_result['valid']:
                    errors.append(rate_result['message'])
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        return {'valid': True, 'message': 'All validations passed'}
    
    @staticmethod
    def validate_offboarding_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate offboarding initiation data"""
        errors = []
        
        # Required fields
        if not data.get('employee_id'):
            errors.append('Employee ID is required')
        
        if not data.get('resignation_date'):
            errors.append('Resignation date is required')
        
        if not data.get('last_working_day'):
            errors.append('Last working day is required')
        
        # Validate dates
        if data.get('resignation_date') and data.get('last_working_day'):
            resign_result = Validators.validate_date(
                data['resignation_date'],
                'Resignation date',
                max_date=date.today()
            )
            if not resign_result['valid']:
                errors.append(resign_result['message'])
            
            lwd_result = Validators.validate_date(
                data['last_working_day'],
                'Last working day',
                min_date=date.today()
            )
            if not lwd_result['valid']:
                errors.append(lwd_result['message'])
            
            # Check if LWD is after resignation date
            if resign_result['valid'] and lwd_result['valid']:
                if lwd_result['date'] < resign_result['date']:
                    errors.append('Last working day cannot be before resignation date')
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        return {'valid': True, 'message': 'All validations passed'}