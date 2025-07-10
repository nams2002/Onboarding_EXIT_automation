import datetime
import logging
from typing import Dict, Any, Optional
from datetime import date
from database.connection import get_db_session
from database.models import LetterTemplate, EmployeeType
from config import config

logger = logging.getLogger(__name__)

class ContractTemplateManager:
    """Manage contract templates for different employee types"""
    
    @staticmethod
    def get_contract_template(employee_type: str) -> Dict[str, str]:
        """Get contract template based on employee type"""
        templates = {
            'contractor': ContractTemplateManager.get_contractor_agreement_template(),
            'intern': ContractTemplateManager.get_internship_agreement_template(),
            'full_time': ContractTemplateManager.get_employment_agreement_template()
        }
        return templates.get(employee_type, {})
    
    @staticmethod
    def get_contractor_agreement_template() -> Dict[str, str]:
        """Get contractor agreement template"""
        return {
            'title': 'CONTRACT AGREEMENT',
            'sections': [
                {
                    'heading': 'PARTIES',
                    'content': '''This Contract Agreement is by and between {employee_name} ("Contractor") 
                    and RAPID INNOVATION ("Company") and defines the scope of work and fees for services 
                    to be performed.'''
                },
                {
                    'heading': 'WORKING PROFILE',
                    'content': '''Employment Type: Contractor
                    Designation: {designation}
                    Joining date: {joining_date}
                    
                    You are required to join the Company on {joining_date} and your employment shall 
                    start from this date. You will be treated as a contractor of the Company from the 
                    joining date and shall be entitled to the benefits available to contractors from 
                    that date onwards. For the initial one month, we will be evaluating your performance, 
                    and if it is satisfactory, we will continue the contract. However, if your performance 
                    is not up to the expected standards, the contract may be terminated. The contract can 
                    be extended on mutual agreement of both parties.'''
                },
                {
                    'heading': 'COMMUNICATION',
                    'content': '''RAPID INNOVATION will follow the standard delivery model for the implementation. 
                    Email is used for all communication throughout the project lifecycle. In general, email 
                    can serve as a mechanism for problem reporting by either party at any time during the 
                    course of a project.
                    
                    Googlemeet Calls - This is basically to share project related artifacts, milestones, 
                    tasks management, share updates, etc.'''
                },
                {
                    'heading': 'LOCATION OF WORK',
                    'content': 'Resources will work from home permanently.'
                },
                {
                    'heading': 'WORKING HOURS',
                    'content': '''As part of your role, you are expected to dedicate approximately {working_hours} 
                    hours per day, from {work_timings} IST, as per work requirements. This schedule ensures 
                    alignment with project needs and facilitates effective collaboration with the team.'''
                },
                {
                    'heading': 'SUPERVISION',
                    'content': 'The Contractor will work under the supervision of a Manager designated by the RAPID INNOVATION.'
                },
                {
                    'heading': 'PRICING AND FEE SCHEDULE',
                    'content': '''Regarding your compensation, you will be paid on Hourly basis Rs. {hourly_rate}, 
                    which reflects our acknowledgment of your valuable contributions to the team. This remuneration 
                    structure is designed to recognize your commitment and efforts in enhancing our projects and 
                    achieving our common goals.
                    
                    Note: The number of hours worked will be recorded on our company software, and payment will 
                    be done on a monthly basis as per your activity on software.'''
                },
                {
                    'heading': 'PROJECT MONITORING AND CONTROL',
                    'content': '''The project work will be executed on a time and materials basis. The contractor 
                    will work remotely from their location, managed and led by RAPID INNOVATION project manager 
                    who will be the single point of contact for all day to day coordination.'''
                },
                {
                    'heading': 'LEAVE POLICY',
                    'content': '''During your tenure as a Contractor with Rapid Innovation, you are not eligible 
                    for leaves. However, please note that for any leave taken, you will not be remunerated for 
                    that specific day.'''
                },
                {
                    'heading': 'EXIT POLICY',
                    'content': 'If you or the company decide to terminate the contract, a one-week notice period is required.'
                },
                {
                    'heading': 'CONFIDENTIALITY',
                    'content': '''The nature of the work performed, and any information transmitted to contractor 
                    by RAPID INNOVATION or to RAPID INNOVATION by contractor shall be confidential, and neither 
                    party shall divulge or otherwise disclose such information to any person other than authorized 
                    employees or authorized subcontractors whose job performance requires such acts and who are 
                    subject to written confidentiality obligations no less restrictive than those contained in 
                    this SOW, without the prior written consent of the other party.'''
                },
                {
                    'heading': 'LIMITATION OF LIABILITY',
                    'content': '''To the maximum extent permitted by applicable law, under no circumstances shall 
                    either party be liable to the other for any special, exemplary, incidental, consequential, 
                    or indirect damages, loss of good will or business profits, work stoppage, data loss, computer 
                    failure or malfunction, or exemplary or punitive damages of any kind or nature, even if that 
                    party has been advised of the possibility of such damages.'''
                },
                {
                    'heading': 'TAX DEDUCTION',
                    'content': '''The company will be deducting tax @ 10% as per the requirements of section 194J 
                    of the Income Tax Act, 1961 before making any payment.'''
                }
            ],
            'nda_section': {
                'heading': 'NON-DISCLOSURE AGREEMENT',
                'content': '''This Non-Disclosure Agreement is effective as of {joining_date} by and between 
                RAPID INNOVATION, for itself and any of its associated contractors. Each of the above parties 
                sometimes referred to hereinafter as a "Receiving Party" and/or "Disclosing Party" jointly as 
                the "Parties".
                
                The Receiving Party shall use the Confidential Information only in connection with its business 
                relationship with the Disclosing Party and shall make no other use whatsoever of the Confidential 
                Information.'''
            }
        }
    
    @staticmethod
    def get_internship_agreement_template() -> Dict[str, str]:
        """Get internship agreement template"""
        return {
            'title': 'INTERNSHIP AGREEMENT',
            'sections': [
                {
                    'heading': 'INTERNSHIP DETAILS',
                    'content': '''This agreement is entered into between Rapid Innovation ("Company") and 
                    {employee_name} ("Intern") for the internship position of {designation}.
                    
                    Duration: {internship_duration}
                    Start Date: {joining_date}
                    Stipend: Rs. {stipend} per month'''
                },
                {
                    'heading': 'SCOPE OF INTERNSHIP',
                    'content': '''The Intern will be assigned various tasks and projects related to their field 
                    of study and the Company's requirements. The specific responsibilities will be communicated 
                    by the assigned supervisor.'''
                },
                {
                    'heading': 'PERFORMANCE EVALUATION',
                    'content': '''We will assess your performance for the initial 15 days, and if we determine 
                    your performance is unsatisfactory, we may terminate your internship with us. After the 
                    internship tenure, we will judge your performance and accordingly will provide feedback & 
                    further confirmation for a full-time job.'''
                },
                {
                    'heading': 'WORKING ARRANGEMENTS',
                    'content': '''The internship will be conducted remotely. The Intern must ensure they have 
                    a stable network connection and uninterrupted power supply at their place. The Intern will 
                    be using their own laptop for the duration of the internship.'''
                },
                {
                    'heading': 'INTELLECTUAL PROPERTY',
                    'content': '''All work products, inventions, and developments created by the Intern during 
                    the internship shall be the sole property of the Company.'''
                },
                {
                    'heading': 'CONFIDENTIALITY',
                    'content': '''The Intern agrees to maintain strict confidentiality regarding all proprietary 
                    information of the Company and shall not disclose such information to any third party.'''
                },
                {
                    'heading': 'TERMINATION',
                    'content': '''Either party may terminate this internship with a 7-day notice period. Upon 
                    termination, the Intern must return all Company property and delete all confidential information.'''
                }
            ]
        }
    
    @staticmethod
    def get_employment_agreement_template() -> Dict[str, str]:
        """Get full-time employment agreement template"""
        return {
            'title': 'EMPLOYMENT AGREEMENT',
            'sections': [
                {
                    'heading': 'EMPLOYMENT TERMS',
                    'content': '''This Employment Agreement is entered into between Rapid Innovation ("Company") 
                    and {employee_name} ("Employee") for the position of {designation}.
                    
                    Date of Joining: {joining_date}
                    Probation Period: {probation_period} months
                    Annual CTC: Rs. {ctc}'''
                },
                {
                    'heading': 'JOB RESPONSIBILITIES',
                    'content': '''The Employee agrees to perform the duties and responsibilities as assigned by 
                    the Company from time to time. The Employee shall report to {reporting_manager} or such 
                    other person as designated by the Company.'''
                },
                {
                    'heading': 'COMPENSATION AND BENEFITS',
                    'content': '''The detailed compensation structure is provided in the annexure. The Employee 
                    shall be entitled to the benefits as per Company policy including group medical insurance, 
                    leave benefits, and other statutory benefits.'''
                },
                {
                    'heading': 'PROBATION AND CONFIRMATION',
                    'content': '''The Employee shall be on probation for {probation_period} months. The Company 
                    may extend the probation period at its discretion. Confirmation will be subject to satisfactory 
                    performance during the probation period.'''
                },
                {
                    'heading': 'NOTICE PERIOD',
                    'content': '''During probation: {notice_period_probation} days
                    After confirmation: {notice_period_confirmed} days
                    
                    If sufficient notice is not given, the Employee will forfeit any unpaid benefits and may 
                    be liable for damages as per the agreement.'''
                },
                {
                    'heading': 'CONFIDENTIALITY AND NON-DISCLOSURE',
                    'content': '''The Employee shall maintain strict confidentiality of all proprietary information 
                    and trade secrets of the Company, both during and after employment.'''
                },
                {
                    'heading': 'NON-COMPETE AND NON-SOLICITATION',
                    'content': '''For a period of one year after termination of employment, the Employee agrees 
                    not to engage in any business that competes with the Company or solicit any employees or 
                    clients of the Company.'''
                }
            ]
        }
    
    @staticmethod
    def get_nda_template() -> Dict[str, str]:
        """Get Non-Disclosure Agreement template"""
        return {
            'title': 'NON-DISCLOSURE AGREEMENT',
            'sections': [
                {
                    'heading': 'DEFINITION OF CONFIDENTIAL INFORMATION',
                    'content': '''Confidential Information means any non-public information including but not 
                    limited to: technical data, trade secrets, know-how, research, product plans, products, 
                    services, customers, customer lists, markets, software, developments, inventions, processes, 
                    formulas, technology, designs, drawings, engineering, hardware configuration information, 
                    marketing, finances, or other business information.'''
                },
                {
                    'heading': 'OBLIGATIONS',
                    'content': '''The Receiving Party agrees to:
                    1. Hold the Confidential Information in strict confidence
                    2. Not disclose the Confidential Information to any third parties
                    3. Use the Confidential Information solely for the permitted purpose
                    4. Protect the Confidential Information with the same degree of care as its own confidential information'''
                },
                {
                    'heading': 'EXCLUSIONS',
                    'content': '''This Agreement does not apply to information that:
                    1. Is or becomes publicly available through no breach by the Receiving Party
                    2. Is rightfully received from a third party without breach of confidentiality
                    3. Is independently developed without use of Confidential Information
                    4. Is required to be disclosed by law or court order'''
                },
                {
                    'heading': 'TERM',
                    'content': '''The obligations under this Agreement shall continue for a period of three (3) 
                    years from the date of disclosure of the Confidential Information.'''
                },
                {
                    'heading': 'REMEDIES',
                    'content': '''The Receiving Party acknowledges that breach of this Agreement may cause 
                    irreparable harm for which monetary damages would be inadequate. Therefore, the Disclosing 
                    Party shall be entitled to seek equitable relief including injunction and specific performance.'''
                }
            ]
        }
    
    @staticmethod
    def populate_template(template: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Populate template with actual data"""
        try:
            # Start with title
            content = f"<h1>{template['title']}</h1>\n\n"
            
            # Add sections
            for section in template.get('sections', []):
                content += f"<h2>{section['heading']}</h2>\n"
                
                # Replace placeholders with actual data
                section_content = section['content']
                for key, value in data.items():
                    placeholder = f"{{{key}}}"
                    if placeholder in section_content:
                        section_content = section_content.replace(placeholder, str(value))
                
                content += f"<p>{section_content}</p>\n\n"
            
            # Add NDA section if present
            if 'nda_section' in template:
                nda = template['nda_section']
                content += f"<h2>{nda['heading']}</h2>\n"
                
                nda_content = nda['content']
                for key, value in data.items():
                    placeholder = f"{{{key}}}"
                    if placeholder in nda_content:
                        nda_content = nda_content.replace(placeholder, str(value))
                
                content += f"<p>{nda_content}</p>\n\n"
            
            return content
            
        except Exception as e:
            logger.error(f"Error populating template: {str(e)}")
            return ""
    
    @staticmethod
    def save_template_to_db(template_name: str, template_type: str, 
                           content: Dict[str, Any]) -> Dict[str, Any]:
        """Save contract template to database"""
        try:
            with get_db_session() as session:
                # Check if template exists
                existing = session.query(LetterTemplate).filter_by(
                    template_name=template_name
                ).first()
                
                if existing:
                    # Update existing
                    existing.content_html = str(content)
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new
                    template = LetterTemplate(
                        template_name=template_name,
                        template_type=template_type,
                        content_html=str(content),
                        variables='{}',
                        created_by='system'
                    )
                    session.add(template)
                
                session.commit()
                
                return {
                    'success': True,
                    'message': f'Template {template_name} saved successfully'
                }
                
        except Exception as e:
            logger.error(f"Error saving template: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }