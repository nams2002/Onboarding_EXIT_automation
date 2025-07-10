import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from database.connection import get_db_session
from database.models import LetterTemplate, EmployeeType
from config import config

logger = logging.getLogger(__name__)

class LetterTemplateManager:
    """Manage letter templates for various HR documents"""

# Template types
    TEMPLATE_TYPES = {
        'OFFER': 'offer_letter',
        'APPOINTMENT': 'appointment_letter',
        'EXPERIENCE': 'experience_letter',
        'RELIEVING': 'relieving_letter',
        'INTERNSHIP_CERT': 'internship_certificate',
        'CONFIRMATION': 'confirmation_letter',
        'PROMOTION': 'promotion_letter',
        'INCREMENT': 'increment_letter',
        'WARNING': 'warning_letter',
        'APPRECIATION': 'appreciation_letter'
    }
    
    @staticmethod
    def get_offer_letter_template(employee_type: str) -> Dict[str, Any]:
        """Get offer letter template based on employee type"""
        base_template = {
            'header': {
                'company_name': config.COMPANY_NAME,
                'company_address': config.COMPANY_ADDRESS,
                'date_format': '{issue_date}',
                'reference': 'Ref: RI/HR/{employee_id}/2024'
            },
            'recipient': {
                'name': '{employee_name}',
                'address': '{employee_address}'
            },
            'subject': 'Offer Letter - {designation}',
            'salutation': 'Dear {first_name},',
            'closing': {
                'message': 'We are confident that you will be able to make a significant contribution to the success of our Company.',
                'signature_instruction': 'Please sign and share the scanned copy of this letter and return it to the HR Department to indicate your acceptance of this offer.',
                'regards': 'Sincerely,',
                'signatory': {
                    'name': config.HR_MANAGER_NAME,
                    'designation': config.HR_MANAGER_DESIGNATION
                }
            }
        }
        
        # Employee type specific content
        if employee_type == 'full_time':
            base_template['body'] = {
                'opening': '''With reference to your application and subsequent discussion/interview, we are pleased to offer you the position of <b>{designation}</b>. You are expected to join on <b>{date_of_joining}</b> on or before.''',
                'compensation': '''Your CTC (Cost-to-Company) will be <b>{ctc} ({ctc_words})</b> per annum.''',
                'probation': '''You will be on probation for a period of {probation_period} months from the date of your joining. Your performance will be assessed for confirmation on various parameters as required at the time of assessment.''',
                'additional': '''This position is designated as remote until further notified by the management. Please ensure that you have a stable network connection and uninterrupted power supply at your place.'''
            }
        elif employee_type == 'intern':
            base_template['body'] = {
                'opening': '''With reference to your application and subsequent discussion/interview, we are pleased to offer you the position of <b>{designation} Intern</b>. You are expected to join on <b>{date_of_joining}</b>.''',
                'compensation': '''It will be <b>{internship_duration} of Internship</b> starting from your date of joining, and the stipend will be <b>{stipend}</b> per month.''',
                'probation': '''We will assess your performance for the initial 15 days, and if we determine your performance is unsatisfactory, we may terminate your employment with us.''',
                'additional': '''After the internship tenure, we will judge your performance and accordingly will provide feedback & further confirmation for a full-time job. You will be using your laptop for the duration of the internship.'''
            }
        else:  # contractor
            base_template['body'] = {
                'opening': '''This Contract Agreement is by and between {employee_name} and RAPID INNOVATION and defines the scope of work and fees for services to be performed.''',
                'compensation': '''Regarding your compensation, you will be paid on Hourly basis <b>{hourly_rate}</b>, which reflects our acknowledgment of your valuable contributions to the team.''',
                'additional': '''The number of hours worked will be recorded on our company software, and payment will be done on a monthly basis as per your activity on software.'''
            }
        
        return base_template
    
    @staticmethod
    def get_appointment_letter_template() -> Dict[str, Any]:
        """Get appointment letter template"""
        return {
            'header': {
                'title': 'APPOINTMENT LETTER',
                'confidential': True
            },
            'content_sections': [
                {
                    'type': 'opening',
                    'text': '''With reference to your application and the subsequent interview you had with us, we are pleased to appoint you to the position of <b>"{designation}"</b> at Rapid Innovation.'''
                },
                {
                    'type': 'joining_details',
                    'text': '''You joined our organization on <b>{date_of_joining}</b>. Following are the Terms & Conditions which have to be followed by all our employees.'''
                },
                {
                    'type': 'terms_heading',
                    'text': 'TERMS AND CONDITIONS OF EMPLOYMENT'
                },
                {
                    'type': 'terms_list',
                    'items': [
                        'You undertake to perform functions in relation to your position and agree to perform such duties as may be assigned to you.',
                        'All employees are required to comply with company policies/guidelines.',
                        'You will be included in the full time roles of the Company.',
                        'During your employment, you may not engage in any employment or act in any way which conflicts with your duties.',
                        'Probation: {probation_period} months initially.',
                        'Leave: As per company policy.',
                        'Transfer of Services: Company may transfer you at its discretion.',
                        'Group Medical: Covers you and family (Spouse & 2 Children).',
                        'Confidentiality: Maintain strict confidentiality.',
                        'Notice Period: {notice_period_probation} days during probation, {notice_period_confirmed} days after confirmation.'
                    ]
                }
            ]
        }
    
    @staticmethod
    def get_experience_letter_template(dues_settled: bool = True) -> Dict[str, Any]:
        """Get experience letter template"""
        return {
            'header': {
                'title': 'EXPERIENCE CERTIFICATE',
                'date': '{issue_date}'
            },
            'to_whom': 'TO WHOMSOEVER IT MAY CONCERN',
            'body': {
                'certification': '''This is to certify that <b>Mr/Ms. {employee_name}</b> worked as the <b>{designation}</b> with <b>{company_name}</b> from <b>{joining_date}</b> to <b>{leaving_date}</b>.''',
                'performance': '''During {gender_pronoun} employment with Rapid Innovation, we found {gender_pronoun} performance to be satisfactory.''',
                'dues': 'All dues are settled.' if dues_settled else 'All dues are not settled.',
                'wishes': '''We wish {gender_pronoun} success in {gender_pronoun} future endeavors.'''
            }
        }
    
    @staticmethod
    def get_relieving_letter_template() -> Dict[str, Any]:
        """Get relieving letter template"""
        return {
            'header': {
                'title': 'RELIEVING LETTER',
                'reference': 'Ref: RL/{employee_id}/2024'
            },
            'body': {
                'opening': '''This is to certify that <b>{employee_name}</b> (Employee ID: {employee_id}) has been relieved from the services of {company_name} on <b>{last_working_day}</b> after serving due notice period.''',
                'resignation': '''{gender_subject_cap} submitted {gender_pronoun} resignation on {resignation_date} and has completed all formalities including knowledge transfer and asset handover.''',
                'wishes': '''We thank {gender_pronoun} for {gender_pronoun} contributions to the organization and wish {gender_pronoun} all the best for {gender_pronoun} future endeavors.'''
            }
        }
    
    @staticmethod
    def get_internship_certificate_template() -> Dict[str, Any]:
        """Get internship certificate template"""
        return {
            'header': {
                'title': 'INTERNSHIP CERTIFICATE',
                'style': 'certificate'
            },
            'to_whom': 'To Whom It May Concern',
            'body': {
                'certification': '''This letter is to certify that <b>Mr/Ms. {employee_name}</b> has completed {gender_pronoun} internship with <b>{company_name}</b>.''',
                'duration': '''{gender_subject_cap} internship tenure was from <b>{joining_date}</b> to <b>{leaving_date}</b>.''',
                'work': '''{gender_subject_cap} was working with us as an <b>{designation}</b> and was actively & diligently involved in the projects and tasks assigned to {gender_pronoun}.''',
                'performance': '''During this time, we found {gender_pronoun} to be punctual and hardworking.''',
                'wishes': '''We wish {gender_pronoun} a bright future.'''
            }
        }
    
    @staticmethod
    def get_confirmation_letter_template() -> Dict[str, Any]:
        """Get confirmation letter template after probation"""
        return {
            'header': {
                'title': 'CONFIRMATION LETTER',
                'reference': 'Ref: CL/{employee_id}/2024'
            },
            'subject': 'Confirmation of Employment',
            'body': {
                'opening': '''We are pleased to inform you that based on your performance during the probation period, you have been confirmed as a permanent employee of {company_name}.''',
                'effective_date': '''Your confirmation is effective from <b>{confirmation_date}</b>.''',
                'benefits': '''You are now entitled to all benefits applicable to confirmed employees as per company policy.''',
                'wishes': '''We look forward to your continued association with us and wish you a successful career with {company_name}.'''
            }
        }
    
    @staticmethod
    def get_promotion_letter_template() -> Dict[str, Any]:
        """Get promotion letter template"""
        return {
            'header': {
                'title': 'PROMOTION LETTER',
                'confidential': True
            },
            'subject': 'Promotion - {new_designation}',
            'body': {
                'opening': '''We are pleased to inform you that in recognition of your excellent performance and contribution to the organization, you have been promoted.''',
                'details': '''Your new designation will be <b>{new_designation}</b> in the {new_department} department, effective from <b>{promotion_date}</b>.''',
                'compensation': '''Your revised compensation will be <b>{new_ctc}</b> per annum. The detailed breakup is attached as an annexure.''',
                'responsibilities': '''In your new role, you will be reporting to {new_reporting_manager} and will be responsible for {key_responsibilities}.''',
                'wishes': '''We are confident that you will continue to excel in your new role and contribute to the growth of the organization.'''
            }
        }
    
    @staticmethod
    def get_increment_letter_template() -> Dict[str, Any]:
        """Get salary increment letter template"""
        return {
            'header': {
                'title': 'INCREMENT LETTER',
                'confidential': True
            },
            'subject': 'Salary Revision',
            'body': {
                'opening': '''Based on your performance review and in line with our compensation review cycle, we are pleased to inform you about your salary revision.''',
                'details': '''Your revised CTC will be <b>{new_ctc}</b> per annum, effective from <b>{increment_date}</b>. This represents an increase of {increment_percentage}% from your current compensation.''',
                'breakdown': '''The detailed compensation structure is provided in the annexure attached to this letter.''',
                'appreciation': '''We appreciate your contributions to the organization and look forward to your continued association with us.'''
            }
        }
    
    @staticmethod
    def create_custom_template(template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom letter template"""
        try:
            with get_db_session() as session:
                template = LetterTemplate(
                    template_name=template_data['template_name'],
                    template_type=template_data['template_type'],
                    employee_type=template_data.get('employee_type'),
                    content_html=template_data['content_html'],
                    variables=template_data.get('variables', '{}'),
                    created_by=template_data.get('created_by', 'user')
                )
                
                session.add(template)
                session.commit()
                
                logger.info(f"Custom letter template created: {template.template_name}")
                
                return {
                    'success': True,
                    'message': 'Template created successfully',
                    'template_id': template.id
                }
                
        except Exception as e:
            logger.error(f"Error creating custom template: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def get_template_variables(template_type: str) -> List[str]:
        """Get list of variables used in a template type"""
        common_variables = [
            'employee_name', 'employee_id', 'designation', 'department',
            'date_of_joining', 'company_name', 'issue_date', 'first_name',
            'gender_pronoun', 'gender_pronoun_cap', 'gender_subject', 'gender_subject_cap'
        ]
        
        template_specific = {
            'offer_letter': ['ctc', 'ctc_words', 'stipend', 'hourly_rate', 'probation_period', 
                           'internship_duration', 'work_timings', 'notice_period_probation', 
                           'notice_period_confirmed', 'reporting_manager'],
            'appointment_letter': ['probation_period', 'notice_period_probation', 'notice_period_confirmed'],
            'experience_letter': ['joining_date', 'leaving_date', 'tenure_text'],
            'relieving_letter': ['last_working_day', 'resignation_date'],
            'promotion_letter': ['new_designation', 'new_department', 'new_ctc', 'promotion_date', 
                               'new_reporting_manager', 'key_responsibilities'],
            'increment_letter': ['new_ctc', 'increment_date', 'increment_percentage'],
            'confirmation_letter': ['confirmation_date']
        }
        
        variables = common_variables.copy()
        if template_type in template_specific:
            variables.extend(template_specific[template_type])
        
        return list(set(variables))  # Remove duplicates
    
    @staticmethod
    def populate_letter_template(template: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Populate letter template with actual data"""
        try:
            html_content = "<div class='letter-container'>\n"
            
            # Add header
            if 'header' in template:
                html_content += "<div class='letter-header'>\n"
                if 'title' in template['header']:
                    html_content += f"<h1>{template['header']['title']}</h1>\n"
                if 'date' in template['header']:
                    date_str = template['header']['date']
                    for key, value in data.items():
                        date_str = date_str.replace(f'{{{key}}}', str(value))
                    html_content += f"<p class='date'>{date_str}</p>\n"
                if 'reference' in template['header']:
                    ref_str = template['header']['reference']
                    for key, value in data.items():
                        ref_str = ref_str.replace(f'{{{key}}}', str(value))
                    html_content += f"<p class='reference'>{ref_str}</p>\n"
                html_content += "</div>\n"
            
            # Add recipient details
            if 'recipient' in template:
                html_content += "<div class='recipient-details'>\n"
                for key, value in template['recipient'].items():
                    formatted_value = value
                    for data_key, data_value in data.items():
                        formatted_value = formatted_value.replace(f'{{{data_key}}}', str(data_value))
                    html_content += f"<p>{formatted_value}</p>\n"
                html_content += "</div>\n"
            
            # Add subject
            if 'subject' in template:
                subject = template['subject']
                for key, value in data.items():
                    subject = subject.replace(f'{{{key}}}', str(value))
                html_content += f"<p class='subject'><b>Subject: {subject}</b></p>\n"
            
            # Add salutation
            if 'salutation' in template:
                salutation = template['salutation']
                for key, value in data.items():
                    salutation = salutation.replace(f'{{{key}}}', str(value))
                html_content += f"<p class='salutation'>{salutation}</p>\n"
            
            # Add body content
            if 'body' in template:
                html_content += "<div class='letter-body'>\n"
                if isinstance(template['body'], dict):
                    for section_key, section_content in template['body'].items():
                        formatted_content = section_content
                        for key, value in data.items():
                            formatted_content = formatted_content.replace(f'{{{key}}}', str(value))
                        html_content += f"<p>{formatted_content}</p>\n"
                else:
                    formatted_body = template['body']
                    for key, value in data.items():
                        formatted_body = formatted_body.replace(f'{{{key}}}', str(value))
                    html_content += f"<p>{formatted_body}</p>\n"
                html_content += "</div>\n"
            
            # Add content sections (for structured templates)
            if 'content_sections' in template:
                for section in template['content_sections']:
                    if section['type'] == 'terms_list' and 'items' in section:
                        html_content += "<ol>\n"
                        for item in section['items']:
                            formatted_item = item
                            for key, value in data.items():
                                formatted_item = formatted_item.replace(f'{{{key}}}', str(value))
                            html_content += f"<li>{formatted_item}</li>\n"
                        html_content += "</ol>\n"
                    else:
                        formatted_text = section.get('text', '')
                        for key, value in data.items():
                            formatted_text = formatted_text.replace(f'{{{key}}}', str(value))
                        if section['type'] == 'terms_heading':
                            html_content += f"<h2>{formatted_text}</h2>\n"
                        else:
                            html_content += f"<p>{formatted_text}</p>\n"
            
            # Add closing
            if 'closing' in template:
                html_content += "<div class='letter-closing'>\n"
                if 'message' in template['closing']:
                    html_content += f"<p>{template['closing']['message']}</p>\n"
                if 'signature_instruction' in template['closing']:
                    html_content += f"<p>{template['closing']['signature_instruction']}</p>\n"
                if 'regards' in template['closing']:
                    html_content += f"<p class='regards'>{template['closing']['regards']}</p>\n"
                if 'signatory' in template['closing']:
                    html_content += "<div class='signature-section'>\n"
                    html_content += f"<p class='signatory-name'>{template['closing']['signatory']['name']}</p>\n"
                    html_content += f"<p class='signatory-designation'>{template['closing']['signatory']['designation']}</p>\n"
                    html_content += "</div>\n"
                html_content += "</div>\n"
            
            # Add to whom it may concern (for certificates)
            if 'to_whom' in template:
                html_content = html_content.replace("<div class='letter-body'>", 
                    f"<p class='to-whom'><b>{template['to_whom']}</b></p>\n<div class='letter-body'>")
            
            html_content += "</div>\n"
            
            return html_content
            
        except Exception as e:
            logger.error(f"Error populating letter template: {str(e)}")
            return ""