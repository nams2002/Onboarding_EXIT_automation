from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging
from config import config
from .models import Base, CompanySettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create engine with SQLite-specific configuration
if config.DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        config.DATABASE_URL,
        poolclass=NullPool,  # Disable connection pooling for Streamlit
        echo=config.DEBUG,  # Log SQL queries in debug mode
        connect_args={"check_same_thread": False}  # Allow SQLite to be used with multiple threads
    )
else:
    engine = create_engine(
        config.DATABASE_URL,
        poolclass=NullPool,  # Disable connection pooling for Streamlit
        echo=config.DEBUG  # Log SQL queries in debug mode
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize the database by creating all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        return False

def drop_all_tables():
    """Drop all tables from the database - USE WITH CAUTION"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("All database tables dropped successfully")
        return True
    except Exception as e:
        logger.error(f"Error dropping database tables: {str(e)}")
        return False

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()

def get_db():
    """Dependency for FastAPI/other frameworks to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def seed_initial_data():
    """Seed initial data into the database"""
    from .models import User, EmailTemplate, LetterTemplate, CompanySettings
    from werkzeug.security import generate_password_hash
    
    try:
        with get_db_session() as session:
            # Check if data already exists
            existing_users = session.query(User).count()
            if existing_users > 0:
                logger.info("Initial data already exists, skipping seed")
                return True
            
            # Create default admin user
            admin_user = User(
                username='admin',
                email='admin@rapidinnovation.com',
                full_name='System Administrator',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            session.add(admin_user)
            
            # Create default email templates
            email_templates = [
                {
                    'template_name': 'document_request_intern',
                    'template_type': 'onboarding',
                    'subject': 'Rapid Innovation - Important Documents Required - {designation} Intern',
                    'body_html': '''<p>Hi {intern_name},</p>
                    <p>Greetings from Rapid Innovation!!</p>
                    <p>This is regarding your joining for the "{designation} Intern" position at Rapid Innovation.</p>
                    <p>As a part of our Employment Joining process, we would require soft copies of the below-mentioned documents:</p>
                    <ol>
                        <li>Educational Docs (10th, 12th, Graduation & Post Graduation Certificates)</li>
                        <li>ID proofs (Aadhaar card, Passport, Driving license, PAN card)</li>
                        <li>Passport-size photographs</li>
                    </ol>
                    <p>Also, please share your full name and address as per your documents.</p>
                    <p>Feel free to get in touch with me in case of any queries or questions.</p>
                    <p>Thanks & Regards<br>Team HR<br>Rapid Innovation</p>''',
                    'variables': '{"intern_name": "Intern Name", "designation": "Designation"}'
                },
                {
                    'template_name': 'document_request_fulltime',
                    'template_type': 'onboarding',
                    'subject': 'Rapid Innovation - Important Documents Required - {designation}',
                    'body_html': '''<p>Hi {employee_name},</p>
                    <p>Greetings from Rapid Innovation!!</p>
                    <p>This is regarding your joining for the "{designation}" position at Rapid Innovation.</p>
                    <p>As a part of our Employment Joining process, we would require soft copies of the below-mentioned documents:</p>
                    <ol>
                        <li>Educational Docs (10th, 12th, Graduation & Post Graduation Certificates)</li>
                        <li>ID proofs (Aadhaar card, Passport, Driving license, PAN card)</li>
                        <li>Resignation/relieving letters, the Last three Months of salary slips, Appointment letters, and offer letters from previous organizations</li>
                        <li>Passport-size photograph</li>
                    </ol>
                    <p>Also, please share your full name and address as per your documents.</p>
                    <p>Feel free to get in touch with me in case of any queries or questions.</p>
                    <p>Thanks & Regards<br>Team HR<br>Rapid Innovation</p>''',
                    'variables': '{"employee_name": "Employee Name", "designation": "Designation"}'
                }
            ]
            
            for template_data in email_templates:
                template = EmailTemplate(**template_data)
                session.add(template)
            
            # Create default company settings
            settings = [
                {
                    'setting_key': 'company_name',
                    'setting_value': 'Rapid Innovation Pvt. Ltd.',
                    'setting_type': 'string',
                    'description': 'Company legal name'
                },
                {
                    'setting_key': 'company_address',
                    'setting_value': 'Hotel North 39, Junas Wada, near River Bridge, Mandrem, Goa 403524',
                    'setting_type': 'string',
                    'description': 'Company registered address'
                },
                {
                    'setting_key': 'hr_email',
                    'setting_value': 'teamhr@rapidinnovation.com',
                    'setting_type': 'string',
                    'description': 'HR department email'
                },
                {
                    'setting_key': 'employee_id_prefix',
                    'setting_value': 'RI',
                    'setting_type': 'string',
                    'description': 'Prefix for employee IDs'
                },
                {
                    'setting_key': 'employee_id_counter',
                    'setting_value': '1000',
                    'setting_type': 'integer',
                    'description': 'Counter for generating employee IDs'
                }
            ]
            
            for setting_data in settings:
                setting = CompanySettings(**setting_data)
                session.add(setting)
            
            session.commit()
            logger.info("Initial data seeded successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error seeding initial data: {str(e)}")
        return False

def get_next_employee_id():
    """Generate the next employee ID"""
    try:
        with get_db_session() as session:
            # Get prefix and counter from settings
            prefix_setting = session.query(CompanySettings).filter_by(
                setting_key='employee_id_prefix'
            ).first()
            counter_setting = session.query(CompanySettings).filter_by(
                setting_key='employee_id_counter'
            ).first()
            
            if not prefix_setting or not counter_setting:
                # Default values if settings don't exist
                prefix = 'RI'
                counter = 1000
            else:
                prefix = prefix_setting.setting_value
                counter = int(counter_setting.setting_value)
            
            # Generate employee ID
            employee_id = f"{prefix}{counter:04d}"
            
            # Update counter
            if counter_setting:
                counter_setting.setting_value = str(counter + 1)
                session.commit()
            
            return employee_id
            
    except Exception as e:
        logger.error(f"Error generating employee ID: {str(e)}")
        return None

# Initialize database on module import
if __name__ == "__main__":
    # Test database connection
    if test_connection():
        print("✅ Database connection successful")
        
        # Initialize database tables
        if init_database():
            print("✅ Database tables created")
            
            # Seed initial data
            if seed_initial_data():
                print("✅ Initial data seeded")
        else:
            print("❌ Failed to create database tables")
    else:
        print("❌ Database connection failed")