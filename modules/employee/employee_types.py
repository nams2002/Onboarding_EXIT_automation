from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import date
from config import config

class EmployeeTypeEnum(Enum):
    """Employee type enumeration"""
    FULL_TIME = "full_time"
    INTERN = "intern"
    CONTRACTOR = "contractor"

@dataclass
class EmployeeTypeConfig:
    """Configuration for each employee type"""
    name: str
    display_name: str
    probation_period_months: int
    notice_period_probation_days: int
    notice_period_confirmed_days: int
    has_pf: bool
    has_gratuity: bool
    has_medical_insurance: bool
    has_leave_benefits: bool
    required_documents: List[str]
    systems_access: List[str]
    compensation_type: str  # 'salary', 'stipend', 'hourly'
    bgv_required: bool
    min_tenure_months: Optional[int] = None
    max_tenure_months: Optional[int] = None

class EmployeeTypes:
    """Employee type definitions and configurations"""
    
    # Employee type configurations
    CONFIGURATIONS = {
        EmployeeTypeEnum.FULL_TIME: EmployeeTypeConfig(
            name="full_time",
            display_name="Full Time Employee",
            probation_period_months=3,
            notice_period_probation_days=15,
            notice_period_confirmed_days=30,
            has_pf=True,
            has_gratuity=True,
            has_medical_insurance=True,
            has_leave_benefits=True,
            required_documents=[
                '10th Certificate',
                '12th Certificate',
                'Graduation Certificate',
                'Post Graduation Certificate (if applicable)',
                'Aadhaar Card',
                'PAN Card',
                'Passport (if available)',
                'Driving License (if available)',
                'Previous Employment - Appointment Letter',
                'Previous Employment - Relieving Letter',
                'Previous Employment - Last 3 Salary Slips',
                'Previous Employment - Experience Letter',
                'Passport Size Photograph'
            ],
            systems_access=['Gmail', 'Slack', 'TeamLogger', 'Google Drive', 'Jira'],
            compensation_type='salary',
            bgv_required=True
        ),
        
        EmployeeTypeEnum.INTERN: EmployeeTypeConfig(
            name="intern",
            display_name="Intern",
            probation_period_months=0,  # 15 days evaluation period
            notice_period_probation_days=7,
            notice_period_confirmed_days=7,
            has_pf=False,
            has_gratuity=False,
            has_medical_insurance=False,
            has_leave_benefits=False,
            required_documents=[
                '10th Certificate',
                '12th Certificate',
                'Graduation Certificate',
                'Post Graduation Certificate (if applicable)',
                'Aadhaar Card',
                'PAN Card',
                'Passport Size Photograph'
            ],
            systems_access=['Gmail', 'Slack'],
            compensation_type='stipend',
            bgv_required=False,
            min_tenure_months=3,
            max_tenure_months=6
        ),
        
        EmployeeTypeEnum.CONTRACTOR: EmployeeTypeConfig(
            name="contractor",
            display_name="Contractor",
            probation_period_months=1,
            notice_period_probation_days=7,
            notice_period_confirmed_days=7,
            has_pf=False,
            has_gratuity=False,
            has_medical_insurance=False,
            has_leave_benefits=False,
            required_documents=[
                'Aadhaar Card',
                'PAN Card',
                'GST Certificate (if applicable)',
                'Previous Work Samples',
                'Passport Size Photograph'
            ],
            systems_access=['Gmail', 'Slack', 'TeamLogger'],
            compensation_type='hourly',
            bgv_required=False
        )
    }
    
    @classmethod
    def get_config(cls, employee_type: str) -> Optional[EmployeeTypeConfig]:
        """Get configuration for employee type"""
        try:
            enum_type = EmployeeTypeEnum(employee_type)
            return cls.CONFIGURATIONS.get(enum_type)
        except ValueError:
            return None
    
    @classmethod
    def get_all_types(cls) -> List[Dict[str, str]]:
        """Get all employee types with display names"""
        return [
            {
                'value': emp_type.value,
                'display_name': config.display_name
            }
            for emp_type, config in cls.CONFIGURATIONS.items()
        ]
    
    @classmethod
    def get_required_documents(cls, employee_type: str) -> List[str]:
        """Get required documents for employee type"""
        config = cls.get_config(employee_type)
        return config.required_documents if config else []
    
    @classmethod
    def get_systems_access(cls, employee_type: str) -> List[str]:
        """Get systems access for employee type"""
        config = cls.get_config(employee_type)
        return config.systems_access if config else []
    
    @classmethod
    def get_notice_period(cls, employee_type: str, is_confirmed: bool = False) -> int:
        """Get notice period in days"""
        config = cls.get_config(employee_type)
        if not config:
            return 0
        
        if employee_type == 'full_time':
            return config.notice_period_confirmed_days if is_confirmed else config.notice_period_probation_days
        else:
            return config.notice_period_probation_days
    
    @classmethod
    def get_probation_period(cls, employee_type: str) -> int:
        """Get probation period in months"""
        config = cls.get_config(employee_type)
        return config.probation_period_months if config else 0
    
    @classmethod
    def validate_employee_type_data(cls, employee_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data specific to employee type"""
        config = cls.get_config(employee_type)
        if not config:
            return {
                'valid': False,
                'errors': ['Invalid employee type']
            }
        
        errors = []
        
        # Validate compensation
        if config.compensation_type == 'salary':
            if not data.get('ctc') or data.get('ctc', 0) <= 0:
                errors.append('Annual CTC is required for full-time employees')
            elif data.get('ctc', 0) < 100000:
                errors.append('Annual CTC must be at least ₹1,00,000')
        
        elif config.compensation_type == 'stipend':
            if not data.get('stipend') or data.get('stipend', 0) <= 0:
                errors.append('Monthly stipend is required for interns')
            elif data.get('stipend', 0) < 5000:
                errors.append('Monthly stipend must be at least ₹5,000')
            elif data.get('stipend', 0) > 50000:
                errors.append('Monthly stipend cannot exceed ₹50,000')
        
        elif config.compensation_type == 'hourly':
            if not data.get('hourly_rate') or data.get('hourly_rate', 0) <= 0:
                errors.append('Hourly rate is required for contractors')
            elif data.get('hourly_rate', 0) < 100:
                errors.append('Hourly rate must be at least ₹100')
            elif data.get('hourly_rate', 0) > 5000:
                errors.append('Hourly rate cannot exceed ₹5,000')
        
        # Validate tenure for interns
        if employee_type == 'intern' and data.get('internship_duration'):
            duration_months = data.get('internship_duration')
            if config.min_tenure_months and duration_months < config.min_tenure_months:
                errors.append(f'Internship duration must be at least {config.min_tenure_months} months')
            if config.max_tenure_months and duration_months > config.max_tenure_months:
                errors.append(f'Internship duration cannot exceed {config.max_tenure_months} months')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @classmethod
    def get_benefits(cls, employee_type: str) -> Dict[str, bool]:
        """Get benefits applicable to employee type"""
        config = cls.get_config(employee_type)
        if not config:
            return {}
        
        return {
            'provident_fund': config.has_pf,
            'gratuity': config.has_gratuity,
            'medical_insurance': config.has_medical_insurance,
            'leave_benefits': config.has_leave_benefits,
            'background_verification': config.bgv_required
        }
    
    @classmethod
    def calculate_eligibility(cls, employee_type: str, tenure_days: int) -> Dict[str, bool]:
        """Calculate eligibility for various benefits based on tenure"""
        config = cls.get_config(employee_type)
        if not config:
            return {}
        
        tenure_months = tenure_days / 30
        tenure_years = tenure_days / 365
        
        eligibility = {
            'pf_withdrawal': config.has_pf and tenure_months >= 6,
            'gratuity': config.has_gratuity and tenure_years >= 5,
            'experience_letter': True,  # Always eligible
            'relieving_letter': tenure_days > 0,
            'full_final_settlement': True
        }
        
        # Special cases
        if employee_type == 'intern':
            eligibility['internship_certificate'] = True
            eligibility['experience_letter'] = False  # Interns get certificate instead
        
        return eligibility
    
    @classmethod
    def get_document_categories(cls, employee_type: str) -> Dict[str, List[str]]:
        """Get documents organized by category"""
        all_documents = cls.get_required_documents(employee_type)
        
        categories = {
            'educational': [],
            'identity': [],
            'employment': [],
            'other': []
        }
        
        for doc in all_documents:
            doc_lower = doc.lower()
            if any(term in doc_lower for term in ['10th', '12th', 'graduation', 'degree', 'diploma', 'certificate']):
                if 'experience' not in doc_lower and 'gst' not in doc_lower:
                    categories['educational'].append(doc)
            elif any(term in doc_lower for term in ['aadhaar', 'pan', 'passport', 'license', 'voter']):
                categories['identity'].append(doc)
            elif any(term in doc_lower for term in ['employment', 'salary', 'appointment', 'relieving', 'experience']):
                categories['employment'].append(doc)
            else:
                categories['other'].append(doc)
        
        return categories
    
    @classmethod
    def get_role_based_systems(cls, employee_type: str, designation: str) -> List[str]:
        """Get systems access based on role and designation"""
        base_systems = cls.get_systems_access(employee_type)
        additional_systems = []
        
        # Add role-specific systems
        designation_lower = designation.lower()
        
        if any(term in designation_lower for term in ['developer', 'engineer', 'technical']):
            additional_systems.extend(['GitHub', 'AWS Console'])
        
        if any(term in designation_lower for term in ['designer', 'ui', 'ux']):
            additional_systems.extend(['Figma', 'Adobe Creative Cloud'])
        
        if any(term in designation_lower for term in ['manager', 'lead', 'head']):
            additional_systems.extend(['Asana', 'Monday.com'])
        
        if any(term in designation_lower for term in ['hr', 'human resource']):
            additional_systems.extend(['HRMS', 'Payroll System'])
        
        if any(term in designation_lower for term in ['finance', 'accountant']):
            additional_systems.extend(['Tally', 'QuickBooks'])
        
        # Combine and remove duplicates
        all_systems = list(set(base_systems + additional_systems))
        return sorted(all_systems)
    
    @classmethod
    def get_compensation_structure(cls, employee_type: str, base_amount: float) -> Dict[str, Any]:
        """Get compensation structure based on employee type"""
        config = cls.get_config(employee_type)
        if not config:
            return {}
        
        if config.compensation_type == 'salary':
            # Calculate CTC breakdown
            basic = base_amount * 0.40
            hra = basic * 0.50
            special_allowance = base_amount * 0.25
            medical_allowance = 15000
            books_periodical = 12000
            health_club = 6000
            internet_telephone = 24000
            
            # Calculate PF
            pf_employer = basic * 0.12
            
            # Adjust special allowance to match CTC
            total_fixed = (basic + hra + medical_allowance + books_periodical + 
                          health_club + internet_telephone + pf_employer)
            special_allowance = base_amount - total_fixed
            
            return {
                'type': 'annual_ctc',
                'ctc': base_amount,
                'breakdown': {
                    'basic_salary': round(basic, 2),
                    'hra': round(hra, 2),
                    'special_allowance': round(special_allowance, 2),
                    'medical_allowance': medical_allowance,
                    'books_periodical': books_periodical,
                    'health_club': health_club,
                    'internet_telephone': internet_telephone,
                    'pf_employer': round(pf_employer, 2),
                    'gross_monthly': round((base_amount - pf_employer) / 12, 2),
                    'net_monthly_estimate': round((base_amount - pf_employer) * 0.75 / 12, 2)  # Approx after tax
                }
            }
        
        elif config.compensation_type == 'stipend':
            return {
                'type': 'monthly_stipend',
                'stipend': base_amount,
                'annual_total': base_amount * 12,
                'paid_days': 'As per attendance'
            }
        
        elif config.compensation_type == 'hourly':
            return {
                'type': 'hourly_rate',
                'hourly_rate': base_amount,
                'estimated_monthly': base_amount * 8 * 22,  # 8 hrs/day, 22 days/month
                'estimated_annual': base_amount * 8 * 22 * 12,
                'billing_cycle': 'Monthly',
                'payment_terms': 'Based on hours logged'
            }
        
        return {}
    
    @classmethod
    def get_exit_checklist(cls, employee_type: str) -> List[Dict[str, str]]:
        """Get exit checklist items for employee type"""
        common_items = [
            {'task': 'Manager Approval', 'description': 'Get exit approval from reporting manager'},
            {'task': 'Knowledge Transfer', 'description': 'Complete knowledge transfer to team'},
            {'task': 'Asset Return', 'description': 'Return all company assets'},
            {'task': 'System Access Revocation', 'description': 'Revoke access to all systems'},
            {'task': 'Exit Interview', 'description': 'Complete exit interview with HR'}
        ]
        
        config = cls.get_config(employee_type)
        if not config:
            return common_items
        
        type_specific_items = []
        
        if employee_type == 'full_time':
            type_specific_items.extend([
                {'task': 'PF Settlement', 'description': 'Process PF transfer/withdrawal'},
                {'task': 'Gratuity Calculation', 'description': 'Calculate gratuity if eligible'},
                {'task': 'Full & Final Settlement', 'description': 'Process complete F&F settlement'},
                {'task': 'Experience Letter', 'description': 'Issue experience letter'}
            ])
        
        elif employee_type == 'intern':
            type_specific_items.extend([
                {'task': 'Internship Certificate', 'description': 'Issue internship completion certificate'},
                {'task': 'Stipend Settlement', 'description': 'Clear pending stipend'}
            ])
        
        elif employee_type == 'contractor':
            type_specific_items.extend([
                {'task': 'Final Invoice', 'description': 'Process final invoice'},
                {'task': 'TDS Certificate', 'description': 'Issue TDS certificate'},
                {'task': 'Contract Closure', 'description': 'Formal contract closure'}
            ])
        
        return common_items + type_specific_items
    
    @classmethod
    def get_onboarding_timeline(cls, employee_type: str) -> List[Dict[str, Any]]:
        """Get onboarding timeline for employee type"""
        timeline = []
        
        if employee_type == 'full_time':
            timeline = [
                {'day': 0, 'task': 'Send document collection email', 'responsible': 'HR'},
                {'day': 1, 'task': 'Document submission', 'responsible': 'Employee'},
                {'day': 2, 'task': 'Document verification', 'responsible': 'HR'},
                {'day': 3, 'task': 'Generate and send offer letter', 'responsible': 'HR'},
                {'day': 4, 'task': 'Offer acceptance', 'responsible': 'Employee'},
                {'day': 5, 'task': 'System access setup', 'responsible': 'IT/HR'},
                {'day': 5, 'task': 'Send welcome email', 'responsible': 'HR'},
                {'day': 7, 'task': 'Generate appointment letter', 'responsible': 'HR'},
                {'day': 7, 'task': 'Initiate BGV process', 'responsible': 'HR'},
                {'day': 'D', 'task': 'First day orientation', 'responsible': 'HR/Manager'},
                {'day': 'D+7', 'task': 'First week check-in', 'responsible': 'Manager'},
                {'day': 'D+30', 'task': 'First month review', 'responsible': 'Manager/HR'},
                {'day': 'D+90', 'task': 'Probation review', 'responsible': 'Manager/HR'}
            ]
        
        elif employee_type == 'intern':
            timeline = [
                {'day': 0, 'task': 'Send document collection email', 'responsible': 'HR'},
                {'day': 1, 'task': 'Document submission', 'responsible': 'Intern'},
                {'day': 2, 'task': 'Generate internship letter', 'responsible': 'HR'},
                {'day': 3, 'task': 'Letter acceptance', 'responsible': 'Intern'},
                {'day': 4, 'task': 'Basic system access', 'responsible': 'IT/HR'},
                {'day': 'D', 'task': 'First day orientation', 'responsible': 'HR/Mentor'},
                {'day': 'D+15', 'task': 'Performance evaluation', 'responsible': 'Mentor'},
                {'day': 'D+30', 'task': 'Monthly review', 'responsible': 'Mentor/HR'}
            ]
        
        elif employee_type == 'contractor':
            timeline = [
                {'day': 0, 'task': 'Send contract agreement', 'responsible': 'HR'},
                {'day': 1, 'task': 'Contract review and signing', 'responsible': 'Contractor'},
                {'day': 2, 'task': 'System access setup', 'responsible': 'IT/HR'},
                {'day': 3, 'task': 'Project briefing', 'responsible': 'Manager'},
                {'day': 'D', 'task': 'Start of contract', 'responsible': 'Contractor'},
                {'day': 'D+30', 'task': 'First month evaluation', 'responsible': 'Manager'}
            ]
        
        return timeline