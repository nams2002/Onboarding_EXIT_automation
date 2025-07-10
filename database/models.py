from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Text, Float, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class EmployeeStatus(enum.Enum):
    ACTIVE = "active"
    ONBOARDING = "onboarding"
    OFFBOARDING = "offboarding"
    EXITED = "exited"

class EmployeeType(enum.Enum):
    FULL_TIME = "full_time"
    INTERN = "intern"
    CONTRACTOR = "contractor"

class DocumentType(enum.Enum):
    EDUCATIONAL = "educational"
    IDENTITY = "identity"
    EMPLOYMENT = "employment"
    OTHER = "other"

class AssetStatus(enum.Enum):
    ISSUED = "issued"
    RETURNED = "returned"
    DAMAGED = "damaged"
    LOST = "lost"

class Employee(Base):
    """Employee model - matches Google Sheets structure exactly"""
    __tablename__ = 'employees'

    # Primary key
    id = Column(Integer, primary_key=True)

    # Google Sheets columns (exact match)
    employee_id = Column(String(50))                              # From "Employee ID" column
    first_name = Column(String(100), nullable=False)              # From "First Name" column
    last_name = Column(String(100), nullable=True)                # From "Last Name" column (can be empty)
    email = Column(String(200), nullable=False)                   # From "Email ID" column
    reporting_manager = Column(String(100))                       # From "Reporting Manager" column
    manager_email = Column(String(200))                           # From "Manager Mail ID" column
    department = Column(String(100))                              # From "Department" column
    employee_type = Column(String(50))                            # From "Categories" column

    # Additional personal information fields
    email_personal = Column(String(200))                          # Personal email for onboarding
    phone = Column(String(20))                                    # Phone number
    address = Column(Text)                                        # Address
    designation = Column(String(100))                             # Job designation
    date_of_joining = Column(Date)                                # Date of joining

    # Work details
    work_location = Column(String(50))                            # Office/Remote/Hybrid
    notice_period = Column(Integer)                               # Notice period in days

    # Compensation details
    ctc = Column(Float)                                           # Annual CTC for full-time
    stipend = Column(Float)                                       # Monthly stipend for interns
    hourly_rate = Column(Float)                                   # Hourly rate for contractors
    probation_period = Column(Integer)                            # Probation period in months
    internship_duration = Column(Integer)                         # Internship duration in months
    contract_duration = Column(Integer)                           # Contract duration in months
    benefits = Column(Text)                                       # Benefits (comma-separated)

    # Emergency contact
    emergency_contact_name = Column(String(100))                  # Emergency contact name
    emergency_contact_phone = Column(String(20))                  # Emergency contact phone
    blood_group = Column(String(10))                              # Blood group
    special_requirements = Column(Text)                           # Special requirements/notes

    # Additional fields for HR system functionality
    status = Column(String(50), default='active')                 # active, onboarding, offboarding, inactive

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships (keeping minimal for HR functionality)
    documents = relationship("Document", back_populates="employee", cascade="all, delete-orphan")
    onboarding_checklist = relationship("OnboardingChecklist", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    offboarding_checklist = relationship("OffboardingChecklist", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    email_logs = relationship("EmailLog", back_populates="employee", cascade="all, delete-orphan")
    system_access = relationship("SystemAccess", back_populates="employee", cascade="all, delete-orphan")

    @property
    def full_name(self):
        """Get full name by combining first and last name"""
        if self.last_name and self.last_name.strip():
            return f"{self.first_name} {self.last_name}".strip()
        else:
            return self.first_name.strip() if self.first_name else ""
    assets = relationship("Asset", back_populates="employee", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name={self.full_name}, employee_id={self.employee_id})>"

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    document_name = Column(String(200), nullable=False)
    file_path = Column(Text)
    file_size = Column(Integer)  # in bytes
    mime_type = Column(String(100))
    uploaded_at = Column(DateTime, default=func.now())
    verified = Column(Boolean, default=False)
    verified_by = Column(String(200))
    verified_at = Column(DateTime)
    comments = Column(Text)
    
    # Relationship
    employee = relationship("Employee", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, name={self.document_name}, employee_id={self.employee_id})>"

class OnboardingChecklist(Base):
    __tablename__ = 'onboarding_checklist'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    
    # Checklist items
    documents_collected = Column(Boolean, default=False)
    documents_verified = Column(Boolean, default=False)
    offer_letter_sent = Column(Boolean, default=False)
    offer_letter_signed = Column(Boolean, default=False)
    systems_access_granted = Column(Boolean, default=False)
    welcome_email_sent = Column(Boolean, default=False)
    appointment_letter_sent = Column(Boolean, default=False)
    appointment_letter_signed = Column(Boolean, default=False)
    bgv_initiated = Column(Boolean, default=False)
    bgv_completed = Column(Boolean, default=False)
    onboarding_completed = Column(Boolean, default=False)
    
    # Timestamps
    offer_sent_date = Column(DateTime)
    offer_signed_date = Column(DateTime)
    appointment_sent_date = Column(DateTime)
    appointment_signed_date = Column(DateTime)
    bgv_initiated_date = Column(DateTime)
    bgv_completed_date = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Notes
    notes = Column(Text)
    
    # Relationship
    employee = relationship("Employee", back_populates="onboarding_checklist")
    
    def __repr__(self):
        return f"<OnboardingChecklist(id={self.id}, employee_id={self.employee_id}, completed={self.onboarding_completed})>"

class OffboardingChecklist(Base):
    __tablename__ = 'offboarding_checklist'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    
    # Exit details
    resignation_date = Column(Date)
    last_working_day = Column(Date)
    exit_type = Column(String(50))  # resignation, termination, end_of_contract
    exit_reason = Column(Text)
    
    # Checklist items
    manager_approval = Column(Boolean, default=False)
    manager_approval_date = Column(DateTime)
    knowledge_transfer = Column(Boolean, default=False)
    knowledge_transfer_date = Column(DateTime)
    assets_returned = Column(Boolean, default=False)
    assets_return_date = Column(DateTime)
    access_revoked = Column(Boolean, default=False)
    access_revoked_date = Column(DateTime)
    fnf_initiated = Column(Boolean, default=False)
    fnf_processed = Column(Boolean, default=False)
    fnf_amount = Column(Float)
    fnf_processed_date = Column(DateTime)
    experience_letter_issued = Column(Boolean, default=False)
    experience_letter_date = Column(DateTime)
    offboarding_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    
    # Notes
    notes = Column(Text)
    
    # Relationship
    employee = relationship("Employee", back_populates="offboarding_checklist")
    
    def __repr__(self):
        return f"<OffboardingChecklist(id={self.id}, employee_id={self.employee_id}, completed={self.offboarding_completed})>"

class EmailLog(Base):
    __tablename__ = 'email_logs'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    email_type = Column(String(100), nullable=False)  # document_request, offer_letter, welcome, exit_initiation, etc.
    recipient_email = Column(String(200), nullable=False)
    cc_emails = Column(Text)  # Comma-separated CC emails
    subject = Column(Text, nullable=False)
    body = Column(Text)
    attachments = Column(Text)  # JSON string of attachment details
    sent_at = Column(DateTime, default=func.now())
    status = Column(String(50), default='sent')  # sent, failed, bounced, opened
    error_message = Column(Text)
    opened_at = Column(DateTime)
    
    # Relationship
    employee = relationship("Employee", back_populates="email_logs")
    
    def __repr__(self):
        return f"<EmailLog(id={self.id}, type={self.email_type}, employee_id={self.employee_id})>"

class SystemAccess(Base):
    __tablename__ = 'system_access'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    system_name = Column(String(100), nullable=False)  # Gmail, Slack, etc.
    username = Column(String(200))
    access_granted = Column(Boolean, default=False)
    granted_at = Column(DateTime)
    granted_by = Column(String(200))
    revoked_at = Column(DateTime)
    revoked_by = Column(String(200))
    notes = Column(Text)
    
    # Relationship
    employee = relationship("Employee", back_populates="system_access")
    
    def __repr__(self):
        return f"<SystemAccess(id={self.id}, system={self.system_name}, employee_id={self.employee_id})>"

class Asset(Base):
    __tablename__ = 'assets'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    asset_type = Column(String(100), nullable=False)  # Laptop, Mouse, etc.
    asset_description = Column(Text)
    asset_tag = Column(String(100))  # Asset identification number
    serial_number = Column(String(200))
    issued_date = Column(Date)
    issued_by = Column(String(200))
    return_date = Column(Date)
    returned_to = Column(String(200))
    return_status = Column(Enum(AssetStatus), default=AssetStatus.ISSUED)
    condition_on_return = Column(Text)
    notes = Column(Text)
    
    # Relationship
    employee = relationship("Employee", back_populates="assets")
    
    def __repr__(self):
        return f"<Asset(id={self.id}, type={self.asset_type}, employee_id={self.employee_id})>"

class EmailTemplate(Base):
    __tablename__ = 'email_templates'
    
    id = Column(Integer, primary_key=True)
    template_name = Column(String(100), unique=True, nullable=False)
    template_type = Column(String(50), nullable=False)  # onboarding, offboarding, general
    subject = Column(Text, nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text)
    variables = Column(Text)  # JSON string of available variables
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(200))
    
    def __repr__(self):
        return f"<EmailTemplate(id={self.id}, name={self.template_name})>"

class LetterTemplate(Base):
    __tablename__ = 'letter_templates'
    
    id = Column(Integer, primary_key=True)
    template_name = Column(String(100), unique=True, nullable=False)
    template_type = Column(String(50), nullable=False)  # offer, appointment, experience, internship_certificate
    employee_type = Column(Enum(EmployeeType))  # Specific to employee type or null for all
    content_html = Column(Text, nullable=False)
    variables = Column(Text)  # JSON string of available variables
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(200))
    
    def __repr__(self):
        return f"<LetterTemplate(id={self.id}, name={self.template_name})>"

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(200), nullable=False)
    user_name = Column(String(200))
    action = Column(String(100), nullable=False)  # create, update, delete, view, download, etc.
    entity_type = Column(String(100), nullable=False)  # employee, document, letter, etc.
    entity_id = Column(Integer)
    old_values = Column(Text)  # JSON string of old values
    new_values = Column(Text)  # JSON string of new values
    ip_address = Column(String(50))
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user={self.user_name}, action={self.action})>"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin, manager, employee
    active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

class CompanySettings(Base):
    __tablename__ = 'company_settings'
    
    id = Column(Integer, primary_key=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text)
    setting_type = Column(String(50))  # string, integer, boolean, json
    description = Column(Text)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(String(200))
    
    def __repr__(self):
        return f"<CompanySettings(key={self.setting_key}, value={self.setting_value})>"