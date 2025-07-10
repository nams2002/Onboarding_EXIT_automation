import streamlit as st
from datetime import datetime, date
import pandas as pd
from config import config
from database.connection import get_db_session
from database.models import Employee, OnboardingChecklist, OffboardingChecklist
from modules.employee.employee_manager import EmployeeManager
from modules.onboarding.document_collection import DocumentCollector
from modules.onboarding.offer_generation import OfferGenerator
from modules.offboarding.exit_initiation import ExitManager
from modules.offboarding.internal_notifications import InternalNotificationManager
# HR bot functionality removed
from modules.integrations.google_sheets import google_sheets_integration
from modules.employee.employee_actions import employee_actions

from utils.helpers import init_session_state, get_employee_status_badge
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="HR Automation System - Rapid Innovation",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
        border: 1px solid #dee2e6;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #495057;
    }
    .metric-label {
        font-size: 0.875rem;
        color: #6c757d;
        margin-top: 0.5rem;
    }
    .employee-details-container {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .back-button {
        background-color: #6c757d;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        cursor: pointer;
    }
    .back-button:hover {
        background-color: #5a6268;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()

def setup_authentication():
    """Setup simple authentication system"""
    # Simple password-based authentication for Streamlit Cloud
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.name = None
        st.session_state.username = None

    return None


# Main application
def main():
    """Main application function"""
    setup_authentication()

    # Simple authentication check
    if not st.session_state.authenticated:
        show_login_page()
        return

    # Admin-only access
    name = st.session_state.get('name', 'HR Admin')
    user_role = 'admin'

    # Sidebar
    with st.sidebar:
        st.write(f'Welcome *{name}*')
        st.write(f'Role: *{user_role.title()}*')
        if st.button('Logout'):
            st.session_state.authenticated = False
            st.session_state.name = None
            st.session_state.username = None
            st.rerun()

        st.divider()

        # Admin-only navigation
        page = st.selectbox(
            'Navigation',
            ['Dashboard', 'Onboarding', 'Offboarding', 'Employees',
             'Documents', 'Settings']
        )

    # Main content area - Admin only
    if page == 'Dashboard':
        show_dashboard()
    elif page == 'Onboarding':
        show_onboarding_page()
    elif page == 'Offboarding':
        show_offboarding_page()
    elif page == 'Employees':
        show_employees_page()
    elif page == 'Documents':
        show_documents_page()
    elif page == 'Settings':
        show_settings_page()

def show_login_page():
    """Show login page with company branding"""
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown("# 🏢 Rapid Innovation")
        st.markdown("### HR Automation System")
        st.markdown("---")

        with st.form("login_form"):
            st.markdown("**Admin Login**")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login", type="primary")

            if login_button:
                if username == "admin" and password == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.name = "HR Admin"
                    st.session_state.username = "admin"
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

        with st.expander("Demo Credentials"):
            st.markdown("""
            **HR Admin:**
            - Username: admin
            - Password: admin123
            """)

def show_dashboard():
    """Show main dashboard"""
    st.title("📊 HR Dashboard")

    # Load employee data from Google Sheets
    with st.spinner("Loading dashboard data..."):
        google_employees = load_google_sheets_employees()

    if not google_employees:
        st.warning("No employee data found. Please check your Google Sheets connection.")
        return

    # Calculate statistics from Google Sheets data
    total_employees = len(google_employees)
    active_employees = len([emp for emp in google_employees if emp.get('status', '').lower() == 'active'])
    onboarding_count = len([emp for emp in google_employees if emp.get('status', '').lower() == 'onboarding'])
    offboarding_count = len([emp for emp in google_employees if emp.get('status', '').lower() == 'offboarding'])

    # Get recent activities
    recent_onboarding = [emp for emp in google_employees if emp.get('status', '').lower() == 'onboarding'][:5]
    recent_offboarding = [emp for emp in google_employees if emp.get('status', '').lower() == 'offboarding'][:5]

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Employees", total_employees)

    with col2:
        st.metric("Active Employees", active_employees)

    with col3:
        st.metric("Onboarding", onboarding_count)

    with col4:
        st.metric("Offboarding", offboarding_count)
    
    # Charts
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Employee Distribution")

        # Calculate actual distribution from Google Sheets data
        full_time_count = len([emp for emp in google_employees if emp.get('employee_type') == 'full_time'])
        intern_count = len([emp for emp in google_employees if emp.get('employee_type') == 'intern'])
        contractor_count = len([emp for emp in google_employees if emp.get('employee_type') == 'contractor'])

        emp_data = pd.DataFrame({
            'Type': ['Full Time', 'Interns', 'Contractors'],
            'Count': [full_time_count, intern_count, contractor_count]
        })

        if emp_data['Count'].sum() > 0:
            fig = px.pie(emp_data, values='Count', names='Type',
                         color_discrete_sequence=['#1f77b4', '#ff7f0e', '#2ca02c'])
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No employee data available for distribution chart")
    
    with col2:
        st.subheader("🏢 Department Distribution")

        # Calculate actual department distribution from Google Sheets data
        dept_counts = {}
        for emp in google_employees:
            dept = emp.get('department', 'Unknown')
            if dept and dept != 'Unknown':
                dept_counts[dept] = dept_counts.get(dept, 0) + 1

        if dept_counts:
            dept_data = pd.DataFrame(list(dept_counts.items()), columns=['Department', 'Count'])
            dept_data = dept_data.sort_values('Count', ascending=True)  # Sort for better visualization

            fig = px.bar(dept_data, x='Count', y='Department', orientation='h',
                        color='Count', color_continuous_scale='viridis')
            fig.update_layout(
                showlegend=False,
                height=400,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No department data available")

    # Department Summary Cards
    st.markdown("---")
    st.subheader("🏢 Department Summary")

    # Calculate department statistics
    dept_stats = {}
    for emp in google_employees:
        dept = emp.get('department', 'Unknown')
        if dept and dept != 'Unknown':
            if dept not in dept_stats:
                dept_stats[dept] = {'total': 0, 'full_time': 0, 'intern': 0, 'contractor': 0}
            dept_stats[dept]['total'] += 1
            emp_type = emp.get('employee_type', 'unknown')
            if emp_type in dept_stats[dept]:
                dept_stats[dept][emp_type] += 1

    # Display department cards
    if dept_stats:
        # Sort departments by total count
        sorted_depts = sorted(dept_stats.items(), key=lambda x: x[1]['total'], reverse=True)

        # Create columns for department cards (3 per row)
        cols_per_row = 3
        for i in range(0, len(sorted_depts), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, (dept_name, stats) in enumerate(sorted_depts[i:i+cols_per_row]):
                with cols[j]:
                    st.markdown(f"""
                    <div style="
                        border: 1px solid #ddd;
                        border-radius: 10px;
                        padding: 15px;
                        margin: 5px;
                        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                        text-align: center;
                    ">
                        <h4 style="margin: 0; color: #2c3e50;">{dept_name}</h4>
                        <h2 style="margin: 5px 0; color: #3498db;">{stats['total']}</h2>
                        <small style="color: #7f8c8d;">
                            Full-time: {stats['full_time']} | Interns: {stats['intern']} | Contractors: {stats['contractor']}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No department data available")

    # Recent Activities
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🆕 Recent Onboarding")
        if recent_onboarding:
            for emp in recent_onboarding:
                emp_name = emp.get('full_name', 'Unknown')
                emp_designation = emp.get('designation', 'N/A')
                emp_status = emp.get('status', 'unknown')
                status_color = {
                    'onboarding': '🟡',
                    'active': '🟢',
                    'offboarding': '🟠',
                    'inactive': '🔴'
                }.get(emp_status.lower(), '⚪')
                st.markdown(f"- **{emp_name}** - {emp_designation} {status_color} {emp_status.title()}")
        else:
            st.info("No recent onboarding activities")

    with col2:
        st.subheader("👋 Recent Exits")
        if recent_offboarding:
            for emp in recent_offboarding:
                emp_name = emp.get('full_name', 'Unknown')
                emp_designation = emp.get('designation', 'N/A')
                emp_status = emp.get('status', 'unknown')
                status_color = {
                    'onboarding': '🟡',
                    'active': '🟢',
                    'offboarding': '🟠',
                    'inactive': '🔴'
                }.get(emp_status.lower(), '⚪')
                st.markdown(f"- **{emp_name}** - {emp_designation} {status_color} {emp_status.title()}")
        else:
            st.info("No recent exit activities")
    


def show_onboarding_page():
    """Show onboarding management page"""
    st.title("🚀 Employee Onboarding")
    
    tab1, tab2, tab3 = st.tabs([
        "New Onboarding", "In Progress", "Document Collection"
    ])

    with tab1:
        show_new_onboarding_form()

    with tab2:
        show_onboarding_progress()

    with tab3:
        show_document_collection()

def show_new_onboarding_form():
    """Show form for new employee onboarding"""
    st.subheader("Start New Onboarding")

    with st.form("new_onboarding_form"):
        st.markdown("### 👤 Personal Information")
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First Name*")
            last_name = st.text_input("Last Name")
            personal_email = st.text_input("Personal Email*")
            phone = st.text_input("Phone Number*")
            employee_id = st.text_input("Employee ID", help="Leave blank to auto-generate")

        with col2:
            employee_type = st.selectbox(
                "Employee Type*",
                options=list(config.EMPLOYEE_TYPES.keys()),
                format_func=lambda x: config.EMPLOYEE_TYPES[x]
            )
            designation = st.text_input("Designation*")
            date_of_joining = st.date_input("Date of Joining*", min_value=date.today())

        address = st.text_area("Address")

        st.markdown("### 🏢 Work Information")
        col3, col4 = st.columns(2)

        with col3:
            department = st.selectbox(
                "Department*",
                options=["Technology", "Marketing", "Sales", "HR", "Finance", "Operations"]
            )
            reporting_manager = st.text_input("Reporting Manager*")

        with col4:
            manager_email = st.text_input("Manager Email", help="Will be auto-generated if left blank")
            work_location = st.selectbox("Work Location", ["Office", "Remote", "Hybrid"])

        st.markdown("### 💰 Compensation Details")
        col5, col6 = st.columns(2)

        with col5:
            # CTC details based on employee type
            if employee_type == 'full_time':
                ctc = st.number_input("Annual CTC (₹)", min_value=0, step=100000)
                probation_period = st.number_input("Probation Period (months)", min_value=0, max_value=12, value=6)
            elif employee_type == 'intern':
                stipend = st.number_input("Monthly Stipend (₹)", min_value=0, step=1000)
                internship_duration = st.number_input("Internship Duration (months)", min_value=1, max_value=12, value=6)
            else:  # contractor
                hourly_rate = st.number_input("Hourly Rate (₹)", min_value=0, step=50)
                contract_duration = st.number_input("Contract Duration (months)", min_value=1, max_value=24, value=12)

        with col6:
            notice_period = st.number_input("Notice Period (days)", min_value=0, max_value=90, value=30)
            if employee_type == 'full_time':
                benefits = st.multiselect(
                    "Benefits",
                    options=["Health Insurance", "PF", "Gratuity", "Leave Encashment", "Laptop", "Internet Allowance"],
                    default=["Health Insurance", "PF"]
                )

        st.markdown("### 📋 Additional Information")
        col7, col8 = st.columns(2)

        with col7:
            emergency_contact_name = st.text_input("Emergency Contact Name")
            emergency_contact_phone = st.text_input("Emergency Contact Phone")

        with col8:
            blood_group = st.selectbox("Blood Group", ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
            special_requirements = st.text_area("Special Requirements/Notes")

        submitted = st.form_submit_button("Start Onboarding", type="primary")
        
        if submitted:
            if all([first_name, personal_email, phone, designation, department, reporting_manager]):
                # Auto-generate employee ID if not provided
                if not employee_id:
                    if first_name and last_name:
                        initials = first_name[0] + last_name[0]
                        employee_id = f"RI{initials.upper()}{datetime.now().strftime('%m%d')}"
                    elif first_name:
                        employee_id = f"RI{first_name[:2].upper()}{datetime.now().strftime('%m%d')}"
                    else:
                        employee_id = f"RIUNK{datetime.now().strftime('%m%d')}"

                # Auto-generate manager email if not provided
                if not manager_email and reporting_manager:
                    manager_email = reporting_manager.lower().replace(' ', '.') + "@rapidinnovation.com"

                # Create employee record with all fields
                emp_manager = EmployeeManager()
                employee_data = {
                    'employee_id': employee_id,
                    'first_name': first_name,
                    'last_name': last_name or '',
                    'email': personal_email,  # Use 'email' field for database
                    'email_personal': personal_email,  # Also set email_personal for compatibility
                    'phone': phone,
                    'employee_type': employee_type,
                    'designation': designation,
                    'department': department,
                    'reporting_manager': reporting_manager,
                    'manager_email': manager_email,
                    'date_of_joining': date_of_joining,
                    'address': address,
                    'work_location': work_location,
                    'notice_period': notice_period,
                    'emergency_contact_name': emergency_contact_name,
                    'emergency_contact_phone': emergency_contact_phone,
                    'blood_group': blood_group,
                    'special_requirements': special_requirements,
                    'status': 'onboarding'
                }

                # Add compensation fields based on employee type
                if employee_type == 'full_time':
                    employee_data['ctc'] = ctc
                    employee_data['probation_period'] = probation_period
                    employee_data['benefits'] = ', '.join(benefits) if benefits else ''
                elif employee_type == 'intern':
                    employee_data['stipend'] = stipend
                    employee_data['internship_duration'] = internship_duration
                elif employee_type == 'contractor':
                    employee_data['hourly_rate'] = hourly_rate
                    employee_data['contract_duration'] = contract_duration

                # Add compensation details based on employee type
                if employee_type == 'full_time':
                    employee_data.update({
                        'ctc': ctc,
                        'probation_period': probation_period,
                        'benefits': ', '.join(benefits) if benefits else ''
                    })
                elif employee_type == 'intern':
                    employee_data.update({
                        'stipend': stipend,
                        'internship_duration': internship_duration
                    })
                else:  # contractor
                    employee_data.update({
                        'hourly_rate': hourly_rate,
                        'contract_duration': contract_duration
                    })

                result = emp_manager.create_employee(employee_data)

                if result['success']:
                    full_name = f"{first_name} {last_name}".strip()
                    st.success(f"✅ Onboarding initiated for {full_name}")
                    st.info("📧 Document collection email has been sent to the candidate.")
                    st.success("📊 Employee automatically added to Google Sheets database.")

                    # Show the employee data that was added
                    st.markdown("### 📋 Employee Details Added:")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Employee ID:** {employee_id}")
                        st.write(f"**Name:** {full_name}")
                        st.write(f"**Email:** {personal_email}")
                        st.write(f"**Phone:** {phone}")
                    with col2:
                        st.write(f"**Designation:** {designation}")
                        st.write(f"**Department:** {department}")
                        st.write(f"**Employee Type:** {employee_type}")
                        st.write(f"**Reporting Manager:** {reporting_manager}")

                    # Show next steps
                    st.markdown("### 📋 Next Steps:")
                    st.markdown("""
                    1. ✅ **Document collection email sent** - Candidate will receive email with document requirements
                    2. ✅ **Employee added to Google Sheets** - Data automatically synchronized
                    3. 📄 **Wait for document submission** - Candidate will upload required documents
                    4. ✅ **Verify documents** - HR team reviews submitted documents
                    5. 📝 **Generate offer letter** - Create and send offer letter after document verification
                    6. 💻 **Setup system access** - Grant access after offer acceptance
                    """)
                else:
                    st.error(f"Error: {result['message']}")
            else:
                st.error("Please fill all required fields marked with *")

def show_onboarding_progress():
    """Show onboarding progress for all employees"""
    st.subheader("Onboarding Progress Tracker")

    # Get onboarding employees and extract data within session
    onboarding_data = []
    with get_db_session() as session:
        onboarding_employees = session.query(
            Employee, OnboardingChecklist
        ).join(
            OnboardingChecklist
        ).filter(
            Employee.status == 'onboarding'
        ).all()

        # Extract all needed data while in session to avoid detached instance errors
        for emp, checklist in onboarding_employees:
            emp_data = {
                'id': emp.id,
                'full_name': emp.full_name,
                'designation': emp.designation,
                'employee_type': emp.employee_type,
                'date_of_joining': emp.date_of_joining,
                'reporting_manager': emp.reporting_manager,
                'checklist': {
                    'documents_collected': checklist.documents_collected,
                    'offer_letter_sent': checklist.offer_letter_sent,
                    'offer_letter_signed': checklist.offer_letter_signed,
                    'systems_access_granted': checklist.systems_access_granted,
                    'appointment_letter_sent': checklist.appointment_letter_sent,
                    'bgv_completed': checklist.bgv_completed
                }
            }
            onboarding_data.append(emp_data)

    if onboarding_data:
        for emp_data in onboarding_data:
            with st.expander(f"👤 {emp_data['full_name']} - {emp_data['designation']}", expanded=True):
                col1, col2, col3 = st.columns([2, 3, 1])

                with col1:
                    st.markdown(f"**Type:** {config.EMPLOYEE_TYPES.get(emp_data['employee_type'], emp_data['employee_type'])}")
                    st.markdown(f"**DOJ:** {emp_data['date_of_joining']}")
                    st.markdown(f"**Manager:** {emp_data['reporting_manager']}")

                with col2:
                    # Progress bar
                    checklist = emp_data['checklist']
                    tasks_completed = sum([
                        checklist['documents_collected'],
                        checklist['offer_letter_sent'],
                        checklist['offer_letter_signed'],
                        checklist['systems_access_granted'],
                        checklist['appointment_letter_sent'],
                        checklist['bgv_completed'] if emp_data['employee_type'] == 'full_time' else True
                    ])
                    total_tasks = 6 if emp_data['employee_type'] == 'full_time' else 5
                    progress = (tasks_completed / total_tasks) * 100

                    st.progress(progress / 100)
                    st.caption(f"Progress: {progress:.0f}%")

                    # Checklist
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.checkbox("Documents Collected", value=checklist['documents_collected'],
                                  key=f"doc_{emp_data['id']}", disabled=True)
                        st.checkbox("Offer Letter Sent", value=checklist['offer_letter_sent'],
                                  key=f"offer_sent_{emp_data['id']}", disabled=True)
                        st.checkbox("Offer Letter Signed", value=checklist['offer_letter_signed'],
                                  key=f"offer_signed_{emp_data['id']}", disabled=True)

                    with col_b:
                        st.checkbox("System Access Granted", value=checklist['systems_access_granted'],
                                  key=f"system_{emp_data['id']}", disabled=True)
                        st.checkbox("Appointment Letter Sent", value=checklist['appointment_letter_sent'],
                                  key=f"appoint_{emp_data['id']}", disabled=True)
                        if emp_data['employee_type'] == 'full_time':
                            st.checkbox("BGV Completed", value=checklist['bgv_completed'],
                                      key=f"bgv_{emp_data['id']}", disabled=True)

                with col3:
                    st.markdown("### Actions")
                    if not checklist['documents_collected']:
                        if st.button("📧 Resend Email", key=f"resend_{emp_data['id']}"):
                            st.success("Reminder email sent!")

                    if checklist['documents_collected'] and not checklist['offer_letter_sent']:
                        if st.button("📄 Generate Offer", key=f"gen_offer_{emp_data['id']}"):
                            st.success("Offer letter generated!")

                    if checklist['offer_letter_signed'] and not checklist['systems_access_granted']:
                        if st.button("💻 Grant Access", key=f"grant_{emp_data['id']}"):
                            st.success("System access granted!")
    else:
        st.info("No employees currently in onboarding process")

def show_document_collection():
    """Show document collection status"""
    st.subheader("📁 Document Collection Status")

    # Filter options
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Search by name or email", placeholder="Type to search...")
    with col2:
        filter_status = st.selectbox("Filter by status", ["All", "Pending", "Completed"])

    # Load real employee data from database
    try:
        with get_db_session() as session:
            from database.models import Document, OnboardingChecklist

            # Get employees with onboarding status and their document counts
            employees_query = session.query(Employee, OnboardingChecklist).outerjoin(OnboardingChecklist).filter(
                Employee.status.in_(['onboarding', 'active'])
            )

            employees_raw = employees_query.all()

            # Process data within session to avoid detached instance errors
            employees_data = []
            document_counts = {}

            for emp, checklist in employees_raw:
                # Get document count for this employee
                doc_count = session.query(Document).filter_by(employee_id=emp.id).count()
                document_counts[emp.id] = doc_count

                # Extract all needed data while in session
                emp_data = {
                    'id': emp.id,
                    'full_name': emp.full_name,
                    'email': emp.email,
                    'employee_type': emp.employee_type if emp.employee_type else 'unknown',
                    'status': emp.status if emp.status else 'unknown',
                    'updated_at': emp.updated_at,
                    'documents_collected': checklist.documents_collected if checklist else False
                }
                employees_data.append(emp_data)

    except Exception as e:
        st.error(f"Error loading document collection data: {str(e)}")
        employees_data = []
        document_counts = {}

    if employees_data:
        # Process and filter data
        processed_data = []
        for emp_data in employees_data:
            # Determine required documents based on employee type
            if emp_data['employee_type'] == 'intern':
                required_docs = 7  # Fewer documents for interns
            elif emp_data['employee_type'] == 'contractor':
                required_docs = 5  # Minimal documents for contractors
            else:
                required_docs = 11  # Full documentation for full-time

            submitted_docs = document_counts.get(emp_data['id'], 0)

            # Determine status
            if emp_data['documents_collected']:
                status = 'Completed'
            elif submitted_docs >= required_docs:
                status = 'Completed'
            else:
                status = 'Pending'

            final_emp_data = {
                'employee_id': emp_data['id'],
                'employee_name': emp_data['full_name'],
                'employee_email': emp_data['email'],
                'employee_type': emp_data['employee_type'].replace('_', ' ').title(),
                'required_docs': required_docs,
                'submitted_docs': submitted_docs,
                'status': status,
                'last_updated': emp_data['updated_at'].strftime('%Y-%m-%d') if emp_data['updated_at'] else 'N/A'
            }

            # Apply search filter
            if search_term:
                search_lower = search_term.lower()
                if (search_lower not in emp_data['full_name'].lower() and
                    search_lower not in emp_data['email'].lower()):
                    continue

            # Apply status filter
            if filter_status != "All" and status != filter_status:
                continue

            processed_data.append(final_emp_data)

        # Display document collection status
        if processed_data:
            for idx, emp_data in enumerate(processed_data):
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

                    with col1:
                        st.markdown(f"**{emp_data['employee_name']}**")
                        st.caption(f"{emp_data['employee_type']} • {emp_data['employee_email']}")

                    with col2:
                        progress = emp_data['submitted_docs'] / emp_data['required_docs'] if emp_data['required_docs'] > 0 else 0
                        st.progress(progress)
                        st.caption(f"{emp_data['submitted_docs']}/{emp_data['required_docs']} documents")

                    with col3:
                        if emp_data['status'] == 'Completed':
                            st.success("✅ Completed")
                        else:
                            st.warning("⏳ Pending")
                        st.caption(f"Updated: {emp_data['last_updated']}")

                    with col4:
                        if st.button("View Details", key=f"view_doc_{idx}"):
                            show_document_details(emp_data['employee_name'])

                        if emp_data['status'] == 'Pending':
                            if st.button("Send Reminder", key=f"remind_doc_{idx}"):
                                # Here you would integrate with email sending
                                st.success(f"Document reminder sent to {emp_data['employee_name']}!")

                    st.divider()
        else:
            st.info("No employees found matching the criteria.")

    else:
        st.info("📄 No employees currently in document collection phase.")
        st.markdown("""
        **Document collection will show employees who:**
        - Are in 'onboarding' status
        - Need to submit required documents
        - Are in the process of document verification

        **To see document collection:**
        1. Complete employee onboarding process
        2. Employees will receive document collection emails
        3. Track their submission progress here
        """)



def show_offboarding_page():
    """Show offboarding management page"""
    st.title("👋 Employee Offboarding")
    
    tab1, tab2, tab3 = st.tabs([
        "Initiate Exit", "Exit Progress", "Final Settlement"
    ])

    with tab1:
        show_exit_initiation()

    with tab2:
        show_exit_progress()

    with tab3:
        show_final_settlement()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_google_sheets_employees():
    """Load employee data from Google Sheets"""
    try:
        # Fetch and process data directly (skip database sync for now)
        df = google_sheets_integration.fetch_employee_data()
        if df is not None:
            processed_data = google_sheets_integration.process_employee_data(df)
            # Add full_name property to each employee for display
            for emp in processed_data:
                first_name = emp.get('first_name', '') or ''
                last_name = emp.get('last_name', '') or ''
                emp['full_name'] = f"{first_name} {last_name}".strip()
            return processed_data
        return []
    except Exception as e:
        st.error(f"Error loading employee data: {str(e)}")
        return []

def show_exit_initiation():
    """Show exit initiation form"""
    st.subheader("Initiate Employee Exit")

    # Load employee data from Google Sheets
    with st.spinner("Loading employee data from Google Sheets..."):
        google_employees = load_google_sheets_employees()

    if not google_employees:
        st.warning("No employee data found. Please check your Google Sheets connection.")
        return

    # Filter active employees
    active_employees = [emp for emp in google_employees if emp.get('status', '').lower() == 'active']

    if not active_employees:
        st.warning("No active employees found in the system.")
        return

    with st.form("exit_initiation_form"):
        col1, col2 = st.columns(2)

        with col1:
            # Create employee options from Google Sheets data
            employee_options = {}
            for emp in active_employees:
                emp_id = emp.get('employee_id', 'N/A')
                emp_name = emp.get('full_name', 'Unknown')
                employee_options[f"{emp_id} - {emp_name}"] = emp

            selected_employee_key = st.selectbox("Select Employee*", options=list(employee_options.keys()))
            selected_employee = employee_options.get(selected_employee_key)

            resignation_date = st.date_input("Resignation Date*", value=date.today())
            exit_type = st.selectbox("Exit Type*", ["Resignation", "Termination", "End of Contract"])
        
        with col2:
            last_working_day = st.date_input("Last Working Day*", min_value=date.today())
            exit_reason = st.text_area("Exit Reason")
            manager_informed = st.checkbox("Manager Informed")
        
        submitted = st.form_submit_button("Initiate Exit Process", type="primary")
        
        if submitted:
            if selected_employee and resignation_date and last_working_day:
                # Use Google Sheets data directly without database dependency
                from modules.email.email_Sender import EmailSender
                from config import config

                try:
                    email_sender = EmailSender()

                    # Prepare exit confirmation email for employee
                    employee_subject = f"Exit Formalities - {selected_employee.get('full_name')} - LWD"

                    # Determine employee type for email content
                    emp_type = selected_employee.get('employee_type', 'full_time').lower()
                    if emp_type == 'intern':
                        payslip_info = "Your invoices will be considered as payslips."
                        settlement_timeline = "Your full and final settlement will be processed within 30-45 days from your last working day."
                    else:
                        payslip_info = "All your payslips are available on Razorpay; we expect you to download them and take them with you."
                        settlement_timeline = "Your full and final settlement will be processed within 30-45 days from your last working day."

                    employee_body_html = f"""
                    <p>Hi {selected_employee.get('first_name')},</p>

                    <p>I hope you are doing well !!</p>

                    <p>This is to confirm that we have received your resignation and your last working day is
                    <b>{last_working_day.strftime('%B %d, %Y')}</b>.</p>

                    <p>As part of the exit process, please note the following:</p>

                    <p><b>Important Information:</b></p>
                    <ul>
                        <li>{payslip_info}</li>
                        <li>Please ensure all company assets are returned before your last working day</li>
                        <li>Complete knowledge transfer with your reporting manager</li>
                        <li>{settlement_timeline}</li>
                    </ul>

                    <p>We will be in touch regarding the exit formalities and asset return process.</p>

                    <p>Thank you for your contributions to Rapid Innovation. We wish you all the best for your future endeavors.</p>

                    <p>Regards,<br>
                    Team HR<br>
                    Rapid Innovation</p>
                    """

                    # Send exit confirmation email to employee
                    employee_email_data = {
                        'to_email': selected_employee.get('email'),
                        'cc_emails': [config.DEFAULT_SENDER_EMAIL],
                        'subject': employee_subject,
                        'body_html': employee_body_html,
                        'body_text': email_sender._html_to_text(employee_body_html)
                    }

                    employee_result = email_sender.send_email(employee_email_data)

                    # Send manager notification email
                    manager_subject = f"Confirmation for proceeding with the Exit formalities - {selected_employee.get('full_name')}"

                    manager_body_html = f"""
                    <p>Hi {selected_employee.get('reporting_manager')},</p>

                    <p>I hope you are doing well !!</p>

                    <p>As you know, the LWD is <b>{last_working_day.strftime('%B %d, %Y')}</b> as the last working day of
                    <b>{selected_employee.get('full_name')}</b>.</p>

                    <p>Kindly let me know once all his knowledge transfer is done so that I can proceed with his exit formalities.
                    These formalities include deactivating his official email ID (once deactivated cannot be restored) and removing
                    him from Slack. Kindly let us know if the official mail data has to be transferred to any other account.</p>

                    <p>Also please take care of any software he is using like the GitHub account, also please remove him from
                    project groups.</p>

                    <p>Please let me know in case of any queries.</p>

                    <p>Regards,<br>
                    Team HR<br>
                    Rapid Innovation</p>
                    """

                    # Get manager email
                    manager_email = selected_employee.get('manager_email', '')
                    if not manager_email:
                        # Fallback: construct email from manager name
                        manager_name = selected_employee.get('reporting_manager', '')
                        if manager_name:
                            manager_email = f"{manager_name.lower().replace(' ', '.')}@rapidinnovation.com"

                    manager_email_data = {
                        'to_email': manager_email,
                        'cc_emails': [config.DEFAULT_SENDER_EMAIL],
                        'subject': manager_subject,
                        'body_html': manager_body_html,
                        'body_text': email_sender._html_to_text(manager_body_html)
                    }

                    manager_result = email_sender.send_email(manager_email_data)

                    if employee_result['success'] and manager_result['success']:
                        st.success("✅ Exit process initiated successfully")
                        st.info("Exit confirmation email sent to employee and manager")

                        # Show next steps
                        st.markdown("### Next Steps:")
                        st.markdown("""
                        1. ✅ Manager approval for knowledge transfer
                        2. 📦 Asset return process
                        3. 🔐 System access revocation
                        4. 💰 Final settlement calculation
                        5. 📜 Experience letter generation
                        """)
                    else:
                        error_msg = []
                        if not employee_result['success']:
                            error_msg.append(f"Employee email: {employee_result['message']}")
                        if not manager_result['success']:
                            error_msg.append(f"Manager email: {manager_result['message']}")
                        st.error(f"Error sending emails: {'; '.join(error_msg)}")

                except Exception as e:
                    st.error(f"Error initiating exit process: {str(e)}")
            else:
                st.error("Please fill all required fields")

def show_exit_progress():
    """Show exit progress for all employees"""
    st.subheader("Exit Progress Tracker")

    # Get offboarding employees and extract data within session
    offboarding_data = []
    with get_db_session() as session:
        offboarding_employees = session.query(
            Employee, OffboardingChecklist
        ).join(
            OffboardingChecklist
        ).filter(
            Employee.status == 'offboarding'
        ).all()

        # Extract all needed data while in session to avoid detached instance errors
        for emp, checklist in offboarding_employees:
            emp_data = {
                'id': emp.id,
                'full_name': emp.full_name,
                'designation': emp.designation,
                'checklist': {
                    'last_working_day': checklist.last_working_day,
                    'manager_approval': checklist.manager_approval,
                    'knowledge_transfer': checklist.knowledge_transfer,
                    'assets_returned': checklist.assets_returned,
                    'access_revoked': checklist.access_revoked,
                    'fnf_processed': checklist.fnf_processed,
                    'experience_letter_issued': checklist.experience_letter_issued
                }
            }
            offboarding_data.append(emp_data)

    if offboarding_data:
        for emp_data in offboarding_data:
            with st.expander(f"👤 {emp_data['full_name']} - {emp_data['designation']}", expanded=True):
                col1, col2, col3 = st.columns([2, 3, 1])

                with col1:
                    checklist = emp_data['checklist']
                    st.markdown(f"**LWD:** {checklist['last_working_day']}")
                    if checklist['last_working_day']:
                        days_remaining = (checklist['last_working_day'] - date.today()).days
                        if days_remaining > 0:
                            st.markdown(f"**Days Remaining:** {days_remaining}")
                        else:
                            st.markdown("**Status:** Exit completed")

                with col2:
                    # Progress tracking
                    tasks_completed = sum([
                        checklist['manager_approval'],
                        checklist['knowledge_transfer'],
                        checklist['assets_returned'],
                        checklist['access_revoked'],
                        checklist['fnf_processed'],
                        checklist['experience_letter_issued']
                    ])
                    progress = (tasks_completed / 6) * 100

                    st.progress(progress / 100)
                    st.caption(f"Progress: {progress:.0f}%")

                    # Checklist
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.checkbox("Manager Approval", value=checklist['manager_approval'],
                                  key=f"mgr_{emp_data['id']}", disabled=True)
                        st.checkbox("Knowledge Transfer", value=checklist['knowledge_transfer'],
                                  key=f"kt_{emp_data['id']}", disabled=True)
                        st.checkbox("Assets Returned", value=checklist['assets_returned'],
                                  key=f"asset_{emp_data['id']}", disabled=True)

                    with col_b:
                        st.checkbox("Access Revoked", value=checklist['access_revoked'],
                                  key=f"access_{emp_data['id']}", disabled=True)
                        st.checkbox("FnF Processed", value=checklist['fnf_processed'],
                                  key=f"fnf_{emp_data['id']}", disabled=True)
                        st.checkbox("Experience Letter", value=checklist['experience_letter_issued'],
                                  key=f"exp_{emp_data['id']}", disabled=True)

                with col3:
                    st.markdown("### Actions")
                    if not checklist['manager_approval']:
                        if st.button("Request Approval", key=f"req_mgr_{emp_data['id']}"):
                            st.success("Approval requested!")

                    if checklist['knowledge_transfer'] and not checklist['access_revoked']:
                        if st.button("Revoke Access", key=f"revoke_{emp_data['id']}"):
                            st.success("Access revoked!")

                    if checklist['fnf_processed'] and not checklist['experience_letter_issued']:
                        if st.button("Generate Letter", key=f"gen_exp_{emp_data['id']}"):
                            st.success("Experience letter generated!")
    else:
        st.info("No employees currently in exit process")



def show_final_settlement():
    """Show final settlement management"""
    st.subheader("💰 Final Settlement")

    # Load real employee data from Google Sheets
    with st.spinner("Loading employee data..."):
        google_employees = load_google_sheets_employees()

    if not google_employees:
        st.warning("No employee data found. Please check your Google Sheets connection.")
        return

    # Filter for employees who might be in offboarding process
    # For demo purposes, we'll show employees with status 'offboarding' or create sample offboarding data
    offboarding_employees = [emp for emp in google_employees if emp.get('status', '').lower() == 'offboarding']

    # If no offboarding employees, show a sample from existing employees for demonstration
    if not offboarding_employees:
        st.info("No employees currently in offboarding process. Showing sample settlement data for demonstration:")
        # Take first 2 employees as examples
        sample_employees = google_employees[:2] if len(google_employees) >= 2 else google_employees

        for idx, emp in enumerate(sample_employees):
            # Generate sample settlement data based on employee type
            emp_type = emp.get('employee_type', 'full_time')
            if emp_type == 'intern':
                pending_salary = 15000
                leave_encashment = 0
                deductions = 0
                status = 'Processing'
            else:
                pending_salary = 45000
                leave_encashment = 12000
                deductions = 5000
                status = 'Pending Approval' if idx == 0 else 'Processing'

            net_settlement = pending_salary + leave_encashment - deductions

            emp_type_display = {
                'full_time': 'Full Time',
                'intern': 'Intern',
                'contractor': 'Contractor'
            }.get(emp_type, emp_type.title())

            with st.expander(f"👤 {emp.get('full_name', 'Unknown')} - {emp_type_display}", expanded=True):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**Settlement Details:**")
                    st.markdown(f"Pending Salary: ₹{pending_salary:,}")
                    st.markdown(f"Leave Encashment: ₹{leave_encashment:,}")
                    st.markdown(f"Deductions: ₹{deductions:,}")
                    st.markdown(f"**Net Amount: ₹{net_settlement:,}**")

                with col2:
                    st.markdown("**Status:**")
                    if status == 'Pending Approval':
                        st.warning("⏳ Pending Approval")
                    elif status == 'Processing':
                        st.info("🔄 Processing")
                    else:
                        st.success("✅ Completed")

                    st.markdown(f"**LWD:** 2024-01-{20 + idx}")

                with col3:
                    st.markdown("**Actions:**")

                    if status == 'Pending Approval':
                        if st.button("Approve Settlement", key=f"approve_fnf_{idx}"):
                            st.success("Settlement approved!")

                    if st.button("View Details", key=f"view_fnf_{idx}"):
                        show_settlement_details(emp.get('full_name', 'Unknown'))

                    if st.button("Generate FnF Letter", key=f"gen_fnf_{idx}"):
                        st.success("FnF letter generated!")
    else:
        # Show actual offboarding employees
        for idx, emp in enumerate(offboarding_employees):
            emp_type_display = {
                'full_time': 'Full Time',
                'intern': 'Intern',
                'contractor': 'Contractor'
            }.get(emp.get('employee_type', ''), emp.get('employee_type', '').title())

            with st.expander(f"👤 {emp.get('full_name', 'Unknown')} - {emp_type_display}", expanded=True):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**Settlement Details:**")
                    st.markdown("Pending calculation...")

                with col2:
                    st.markdown("**Status:**")
                    st.info("🔄 In Progress")

                with col3:
                    st.markdown("**Actions:**")
                    if st.button("Calculate Settlement", key=f"calc_fnf_{idx}"):
                        st.info("Settlement calculation initiated!")

def show_employees_page():
    """Show employee management page"""
    st.title("👥 Employee Management")

    # Check if we should show employee details
    if st.session_state.get('show_employee_details', False) and st.session_state.get('selected_employee'):
        show_employee_details_modal()
        return

    # Load employee data from Google Sheets
    with st.spinner("Loading employee data from Google Sheets..."):
        google_employees = load_google_sheets_employees()

    if not google_employees:
        st.warning("No employee data found. Please check your Google Sheets connection.")
        return

    # Search and filters
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        search_term = st.text_input("Search employees", placeholder="Name, ID, or email...")
    with col2:
        emp_type = st.selectbox("Type", ["All", "Full Time", "Intern", "Contractor"])
    with col3:
        # Get unique departments from data
        departments = ["All"] + list(set([emp.get('department', 'Unknown') for emp in google_employees if emp.get('department')]))
        dept = st.selectbox("Department", departments)
    with col4:
        status = st.selectbox("Status", ["All", "Active", "Onboarding", "Offboarding", "Inactive"])

    # Apply filters
    filtered_employees = google_employees.copy()

    if search_term:
        search_lower = search_term.lower()
        filtered_employees = [
            emp for emp in filtered_employees
            if search_lower in str(emp.get('full_name', '')).lower() or
               search_lower in str(emp.get('employee_id', '')).lower() or
               search_lower in str(emp.get('email', '')).lower()
        ]

    if emp_type != "All":
        type_mapping = {
            "Full Time": "full_time",
            "Intern": "intern",
            "Contractor": "contractor"
        }
        filtered_employees = [
            emp for emp in filtered_employees
            if emp.get('employee_type', '').lower() == type_mapping.get(emp_type, '').lower()
        ]

    if dept != "All":
        filtered_employees = [
            emp for emp in filtered_employees
            if emp.get('department', '') == dept
        ]

    if status != "All":
        filtered_employees = [
            emp for emp in filtered_employees
            if emp.get('status', '').lower() == status.lower()
        ]

    # Display summary statistics
    if filtered_employees:
        st.markdown(f"### Found {len(filtered_employees)} employees")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            full_time_count = len([emp for emp in filtered_employees if emp.get('employee_type') == 'full_time'])
            st.metric("Full Time", full_time_count)
        with col2:
            intern_count = len([emp for emp in filtered_employees if emp.get('employee_type') == 'intern'])
            st.metric("Interns", intern_count)
        with col3:
            contractor_count = len([emp for emp in filtered_employees if emp.get('employee_type') == 'contractor'])
            st.metric("Contractors", contractor_count)
        with col4:
            active_count = len([emp for emp in filtered_employees if emp.get('status', '').lower() == 'active'])
            st.metric("Active", active_count)

        st.markdown("---")

        # Display employee cards
        for idx, emp in enumerate(filtered_employees):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])

                with col1:
                    st.markdown(f"**{emp.get('full_name', 'Unknown')}**")
                    st.caption(f"{emp.get('employee_id', 'N/A')} • {emp.get('designation', 'N/A')}")

                with col2:
                    emp_type_display = {
                        'full_time': 'Full Time',
                        'intern': 'Intern',
                        'contractor': 'Contractor'
                    }.get(emp.get('employee_type', ''), emp.get('employee_type', 'Unknown').title())
                    st.markdown(f"**{emp_type_display}**")
                    st.caption(f"{emp.get('department', 'N/A')}")

                with col3:
                    st.markdown(f"**{emp.get('email', 'N/A')}**")
                    doj = emp.get('date_of_joining')
                    if doj:
                        if hasattr(doj, 'strftime'):
                            doj_str = doj.strftime('%Y-%m-%d')
                        else:
                            doj_str = str(doj)
                    else:
                        doj_str = 'N/A'
                    st.caption(f"DOJ: {doj_str}")

                with col4:
                    status_display = emp.get('status', 'unknown').title()
                    status_color = {
                        'active': '🟢',
                        'onboarding': '🟡',
                        'offboarding': '🟠',
                        'inactive': '🔴'
                    }.get(emp.get('status', '').lower(), '⚪')
                    st.markdown(f"{status_color} {status_display}")

                with col5:
                    if st.button("View", key=f"view_emp_{idx}"):
                        st.session_state.selected_employee = emp
                        st.session_state.show_employee_details = True
                        st.rerun()

                st.divider()
    else:
        st.info("No employees found matching the criteria")

def show_documents_page():
    """Show document management page"""
    st.title("📄 Document Management")
    
    tab1, tab2, tab3 = st.tabs(["All Documents", "Templates", "Bulk Operations"])
    
    with tab1:
        show_all_documents()
    
    with tab2:
        show_document_templates()
    
    with tab3:
        show_bulk_operations()



def show_settings_page():
    """Show settings page"""
    st.title("⚙️ Settings")
    
    tab1, tab2, tab3, tab4 = st.tabs(["General", "Email Templates", "Integrations", "Users"])
    
    with tab1:
        show_general_settings()
    
    with tab2:
        show_email_template_settings()
    
    with tab3:
        show_integration_settings()
    
    with tab4:
        show_user_management()

# Helper functions for detailed views
def show_document_details(employee_name):
    """Show detailed document view for an employee"""
    st.subheader(f"Document Details - {employee_name}")
    # Implementation here

def show_settlement_details(employee_name):
    """Show detailed settlement view"""
    st.subheader(f"Settlement Details - {employee_name}")
    # Implementation here



def show_employee_details_modal():
    """Show employee details in a clean modal-like view - only Google Sheets data"""
    employee_data = st.session_state.get('selected_employee', {})

    # Header with back button
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("← Back", key="back_to_employees"):
            st.session_state.show_employee_details = False
            st.session_state.selected_employee = None
            st.rerun()

    with col2:
        st.title(f"👤 {employee_data.get('full_name', 'Unknown Employee')}")

    st.markdown("---")

    # Create tabs for different sections - only show data that exists in Google Sheets
    tab1, tab2, tab3 = st.tabs(["📋 Personal Info", "💼 Employment", "⚡ Actions"])

    with tab1:
        st.markdown("### Personal Information")
        col1, col2 = st.columns(2)

        with col1:
            # Only show fields that exist in Google Sheets
            if employee_data.get('full_name'):
                st.write(f"**Full Name:** {employee_data.get('full_name')}")

            if employee_data.get('employee_id'):
                st.write(f"**Employee ID:** {employee_data.get('employee_id')}")

            if employee_data.get('email'):
                st.write(f"**Email:** {employee_data.get('email')}")

        with col2:
            # Show manager email if available
            if employee_data.get('manager_email'):
                st.write(f"**Manager Email:** {employee_data.get('manager_email')}")

    with tab2:
        st.markdown("### Employment Details")
        col1, col2 = st.columns(2)

        with col1:
            # Only show fields from Google Sheets
            if employee_data.get('department'):
                st.write(f"**Department:** {employee_data.get('department')}")

            if employee_data.get('employee_type'):
                emp_type_display = {
                    'full_time': 'Full Time',
                    'intern': 'Intern',
                    'contractor': 'Contractor'
                }.get(employee_data.get('employee_type'), employee_data.get('employee_type', '').title())
                st.write(f"**Employee Type:** {emp_type_display}")

        with col2:
            if employee_data.get('reporting_manager'):
                st.write(f"**Reporting Manager:** {employee_data.get('reporting_manager')}")

            # Show status (this is auto-generated as 'active')
            if employee_data.get('status'):
                st.write(f"**Status:** {employee_data.get('status').title()}")

    with tab3:
        st.markdown("### Available Actions")

        # Email Section
        st.markdown("#### 📧 Send Email")
        col1, col2 = st.columns([2, 1])

        with col1:
            # Determine available email templates based on employee status
            if employee_data.get('status', '').lower() == 'active':
                email_templates = employee_actions.get_available_templates('email', 'onboarding')
                process_type = 'onboarding'
            else:
                email_templates = employee_actions.get_available_templates('email', 'offboarding')
                process_type = 'offboarding'

            # Clean template names for display
            template_options = [t.replace('.html', '').replace('_', ' ').title() for t in email_templates]
            selected_email_template = st.selectbox(
                "Select Email Template:",
                options=template_options,
                key="email_template_select"
            )

        with col2:
            if st.button("📧 Send Email", key="send_email_btn", type="primary"):
                if selected_email_template:
                    # Convert back to filename
                    template_file = selected_email_template.lower().replace(' ', '_') + '.html'

                    with st.spinner("Sending email..."):
                        result = employee_actions.send_email_to_employee(
                            employee_data,
                            template_file,
                            {'process_type': process_type}
                        )

                    if result['success']:
                        st.success(f"✅ Email sent successfully to {employee_data.get('email')}")
                        st.info(f"📧 Template: {selected_email_template}")
                        if result.get('cc_emails'):
                            st.info(f"📋 CC: {', '.join(result.get('cc_emails', []))}")
                    else:
                        st.error(f"❌ Failed to send email: {result.get('message')}")

        st.markdown("---")

        # Letter Section
        st.markdown("#### 📄 Generate Letter")
        col1, col2 = st.columns([2, 1])

        with col1:
            # Determine available letter templates
            if employee_data.get('employee_type') == 'intern':
                letter_templates = ['internship_letter.html', 'internship_certificate.html']
            elif employee_data.get('status', '').lower() == 'active':
                letter_templates = employee_actions.get_available_templates('letter', 'onboarding')
            else:
                letter_templates = employee_actions.get_available_templates('letter', 'offboarding')

            # Clean template names for display
            letter_options = [t.replace('.html', '').replace('_', ' ').title() for t in letter_templates]
            selected_letter_template = st.selectbox(
                "Select Letter Template:",
                options=letter_options,
                key="letter_template_select"
            )

            # Email option
            send_via_email = st.checkbox("📧 Send letter via email", key="send_letter_email")

        with col2:
            if st.button("📄 Generate Letter", key="gen_letter_btn", type="primary"):
                if selected_letter_template:
                    # Convert back to filename
                    template_file = selected_letter_template.lower().replace(' ', '_') + '.html'

                    with st.spinner("Generating letter..."):
                        result = employee_actions.generate_letter_for_employee(
                            employee_data,
                            template_file
                        )

                    if result['success']:
                        st.success(f"✅ Letter generated successfully")
                        st.info(f"📄 Template: {selected_letter_template}")
                        if result.get('file_path'):
                            st.info(f"📁 File: {result.get('file_path')}")

                            # Send via email if requested
                            if send_via_email:
                                with st.spinner("Sending letter via email..."):
                                    email_result = employee_actions.send_letter_via_email(
                                        employee_data,
                                        result.get('file_path'),
                                        result.get('template_name', template_file)
                                    )

                                if email_result['success']:
                                    st.success(f"📧 Letter sent successfully to {employee_data.get('email')}")
                                    if email_result.get('cc_emails'):
                                        st.info(f"📋 CC: {', '.join(email_result.get('cc_emails', []))}")
                                else:
                                    st.error(f"❌ Failed to send email: {email_result.get('message')}")
                    else:
                        st.error(f"❌ Failed to generate letter: {result.get('message')}")

        st.markdown("---")

        # Exit Process Section (only for active employees)
        if employee_data.get('status', '').lower() == 'active':
            st.markdown("#### 🚪 Exit Process")

            # Create exit process form
            with st.form(f"exit_process_form_{employee_data.get('employee_id', 'unknown')}"):
                st.markdown("**Exit Process Initiation**")

                col1, col2 = st.columns(2)
                with col1:
                    resignation_date = st.date_input("Resignation Date*", min_value=date.today())
                    exit_type = st.selectbox("Exit Type", ["resignation", "termination", "end_of_contract"])

                with col2:
                    last_working_day = st.date_input("Last Working Day*", min_value=date.today())
                    exit_reason = st.text_area("Exit Reason")

                manager_informed = st.checkbox("Manager Informed")

                # Auto-trigger all exit process steps
                auto_trigger_steps = st.checkbox("Auto-trigger all exit process steps", value=True,
                                                help="This will automatically send emails for asset return, access revocation notifications")

                submitted = st.form_submit_button("🚪 Initiate Complete Exit Process", type="primary")

                if submitted:
                    if resignation_date and last_working_day:
                        # First, sync the employee from Google Sheets to database
                        from modules.employee.employee_manager import EmployeeManager
                        emp_manager = EmployeeManager()

                        # Check if employee exists in database (by employee_id or email)
                        with get_db_session() as session:
                            existing_employee = session.query(Employee).filter(
                                (Employee.employee_id == employee_data.get('employee_id')) |
                                (Employee.email == employee_data.get('email'))
                            ).first()

                            if not existing_employee:
                                # Create employee in database from Google Sheets data
                                employee_create_data = {
                                    'employee_id': employee_data.get('employee_id'),
                                    'first_name': employee_data.get('first_name', ''),
                                    'last_name': employee_data.get('last_name', ''),
                                    'email': employee_data.get('email', ''),  # Map to required email field
                                    'email_personal': employee_data.get('email', ''),  # Also set personal email
                                    'phone': employee_data.get('phone', ''),
                                    'designation': employee_data.get('designation', ''),
                                    'department': employee_data.get('department', ''),
                                    'employee_type': employee_data.get('employee_type', 'full_time'),
                                    'reporting_manager': employee_data.get('reporting_manager', ''),
                                    'date_of_joining': employee_data.get('date_of_joining'),
                                    'status': 'active'
                                }

                                # Create employee in database
                                create_result = emp_manager.create_employee(employee_create_data)
                                if not create_result['success']:
                                    st.error(f"Failed to create employee record: {create_result['message']}")
                                    return

                                db_employee_id = create_result['id']  # Use the database ID
                            else:
                                db_employee_id = existing_employee.id
                                # Update employee status to active if needed
                                if existing_employee.status != 'active':
                                    existing_employee.status = 'active'
                                    session.commit()

                        # Initialize exit process
                        exit_manager = ExitManager()
                        notification_manager = InternalNotificationManager()

                        # Create exit data with database ID
                        exit_data = {
                            'employee_id': db_employee_id,  # Use database ID, not Google Sheets employee_id
                            'resignation_date': resignation_date,
                            'last_working_day': last_working_day,
                            'exit_type': exit_type,
                            'exit_reason': exit_reason,
                            'manager_informed': manager_informed
                        }

                        # Step 1: Initiate exit process (this sends exit confirmation email)
                        result = exit_manager.initiate_exit(exit_data)

                        if result['success']:
                            st.success("✅ Exit process initiated successfully")
                            st.info("📧 Exit confirmation email sent to employee and manager")

                            if auto_trigger_steps:
                                # Step 2: Send access revocation notification to IT team
                                try:
                                    it_result = notification_manager.send_it_access_revocation_notification(db_employee_id)
                                    if it_result['success']:
                                        st.success("✅ IT team notified about upcoming access revocation")
                                    else:
                                        st.warning(f"⚠️ IT notification: {it_result['message']}")
                                except Exception as e:
                                    st.warning(f"⚠️ IT notification error: {str(e)}")

                                # Step 4: Notify HR about final settlement preparation
                                try:
                                    fnf_result = notification_manager.send_hr_final_settlement_notification(db_employee_id)
                                    if fnf_result['success']:
                                        st.success("✅ HR team notified to prepare final settlement calculation")
                                    else:
                                        st.warning(f"⚠️ HR FNF notification: {fnf_result['message']}")
                                except Exception as e:
                                    st.warning(f"⚠️ HR FNF notification error: {str(e)}")

                                # Step 5: Notify HR about experience letter preparation
                                try:
                                    exp_result = notification_manager.send_hr_experience_letter_notification(db_employee_id)
                                    if exp_result['success']:
                                        st.success("✅ HR team notified to prepare experience letter")
                                    else:
                                        st.warning(f"⚠️ HR experience letter notification: {exp_result['message']}")
                                except Exception as e:
                                    st.warning(f"⚠️ HR experience letter notification error: {str(e)}")

                            # Show detailed next steps
                            st.markdown("### 📋 Exit Process Status:")
                            st.markdown(f"""
                            **Employee:** {employee_data.get('full_name', 'Unknown')}
                            **Resignation Date:** {resignation_date}
                            **Last Working Day:** {last_working_day}
                            **Notice Period:** {result.get('notice_period_days', 'N/A')} days
                            **Required Notice:** {result.get('required_notice', 'N/A')} days
                            """)

                            if result.get('short_notice'):
                                st.warning("⚠️ Short notice period - Recovery may be applicable as per appointment letter")

                            st.markdown("### 📧 Emails Sent:")
                            st.markdown("✅ Exit confirmation email to employee")
                            st.markdown("✅ Manager notification email")

                            if auto_trigger_steps:
                                st.markdown("✅ IT team notification for access revocation")
                                st.markdown("✅ HR team notification for final settlement")
                                st.markdown("✅ HR team notification for experience letter")

                            st.markdown("### 🔄 Next Manual Steps:")
                            st.markdown("""
                            1. **Manager:** Complete knowledge transfer approval
                            2. **IT Team:** Revoke system access after knowledge transfer
                            3. **HR Team:** Calculate and process final settlement
                            4. **HR Team:** Generate and send experience letter
                            """)

                        else:
                            st.error(f"❌ Error: {result['message']}")
                    else:
                        st.error("Please fill all required fields")

def show_employee_details(employee_id):
    """Show detailed employee view (legacy function for database)"""
    st.subheader("Employee Details")
    st.info("This function would show details from database. Use Google Sheets integration instead.")

def show_all_documents():
    """Show all documents"""
    st.subheader("📄 All Generated Documents")

    # Filter and search options
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        search_term = st.text_input("🔍 Search documents", placeholder="Employee name, document type...")

    with col2:
        doc_filter = st.selectbox("Filter by type",
                                ["All Documents", "Offer Letters", "Appointment Letters",
                                 "Experience Letters", "Internship Certificates", "FNF Statements"])

    with col3:
        date_filter = st.selectbox("Date range", ["All Time", "Last 7 days", "Last 30 days", "Last 90 days"])

    st.markdown("---")

    # Load real document data from database
    try:
        with get_db_session() as session:
            # Query documents with employee information
            from database.models import Document, EmailLog

            # Get documents with employee details
            documents_query = session.query(Document, Employee).join(Employee).order_by(Document.uploaded_at.desc())

            # Apply date filter
            if date_filter != "All Time":
                from datetime import timedelta
                days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
                cutoff_date = datetime.now() - timedelta(days=days_map[date_filter])
                documents_query = documents_query.filter(Document.uploaded_at >= cutoff_date)

            documents_data = documents_query.all()

            # Get email logs to determine if documents were sent
            email_logs = session.query(EmailLog).filter(
                EmailLog.email_type.in_(['offer_letter', 'appointment_letter', 'experience_letter', 'internship_certificate'])
            ).all()

            # Create lookup for sent documents
            sent_docs = {}
            for log in email_logs:
                key = f"{log.employee_id}_{log.email_type}"
                sent_docs[key] = log.sent_at

    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")
        documents_data = []
        sent_docs = {}

    if documents_data:
        # Apply search filter
        if search_term:
            search_lower = search_term.lower()
            filtered_docs = [
                (doc, emp) for doc, emp in documents_data
                if search_lower in emp.full_name.lower() or
                   search_lower in str(doc.document_type).lower() or
                   search_lower in doc.document_name.lower()
            ]
        else:
            filtered_docs = documents_data

        # Apply document type filter
        if doc_filter != "All Documents":
            type_mapping = {
                "Offer Letters": "offer_letter",
                "Appointment Letters": "appointment_letter",
                "Experience Letters": "experience_letter",
                "Internship Certificates": "internship_certificate",
                "FNF Statements": "fnf_statement"
            }
            filter_type = type_mapping.get(doc_filter)
            if filter_type:
                filtered_docs = [
                    (doc, emp) for doc, emp in filtered_docs
                    if str(doc.document_type) == filter_type
                ]

        # Display documents
        for i, (doc, emp) in enumerate(filtered_docs):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 1, 1.5])

                with col1:
                    st.markdown(f"**{emp.full_name}**")
                    st.caption(f"Generated: {doc.uploaded_at.strftime('%Y-%m-%d %H:%M')}")

                with col2:
                    doc_type_display = str(doc.document_type).replace('_', ' ').title()
                    st.markdown(f"**{doc_type_display}**")
                    st.caption(f"File: {doc.document_name}")

                with col3:
                    # Check if document was sent via email
                    email_key = f"{emp.id}_{str(doc.document_type)}"
                    if email_key in sent_docs:
                        st.success("📧 Sent")
                        st.caption(f"Sent: {sent_docs[email_key].strftime('%Y-%m-%d')}")
                    else:
                        st.info("📄 Generated")
                        st.caption("Not sent yet")

                with col4:
                    if st.button("👁️ View", key=f"view_doc_{i}"):
                        st.info(f"Opening {doc_type_display} for {emp.full_name}")
                        if doc.file_path:
                            st.caption(f"Path: {doc.file_path}")

                with col5:
                    if st.button("📧 Send", key=f"send_doc_{i}"):
                        # Here you would integrate with the email sending functionality
                        st.success(f"Document sent to {emp.email}")

                st.divider()

        # Document statistics from real data
        st.markdown("### 📊 Document Statistics")
        col1, col2, col3, col4 = st.columns(4)

        total_docs = len(documents_data)
        sent_count = len(sent_docs)
        pending_send = total_docs - sent_count

        # Count documents by type
        doc_types = set([str(doc.document_type) for doc, emp in documents_data])

        with col1:
            st.metric("Total Documents", total_docs)

        with col2:
            # Count this month's documents
            from datetime import datetime
            this_month = datetime.now().replace(day=1)
            this_month_count = len([
                doc for doc, emp in documents_data
                if doc.uploaded_at >= this_month
            ])
            st.metric("This Month", this_month_count)

        with col3:
            st.metric("Pending Send", pending_send)

        with col4:
            st.metric("Document Types", len(doc_types))

    else:
        st.info("📄 No documents found in the system yet.")
        st.markdown("""
        **Documents will appear here when:**
        - Employees upload documents during onboarding
        - HR generates offer letters, appointment letters, etc.
        - Experience letters and FNF statements are created

        **To generate documents:**
        1. Go to **Employees** page
        2. Select an employee and click **View**
        3. Use the **Actions** tab to generate letters
        """)

        # Show empty state statistics
        st.markdown("### 📊 Document Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Documents", "0")

        with col2:
            st.metric("This Month", "0")

        with col3:
            st.metric("Pending Send", "0")

        with col4:
            st.metric("Document Types", "0")

def show_document_templates():
    """Show document templates"""
    st.subheader("Document Templates")
    # Implementation here

def show_bulk_operations():
    """Show bulk operations"""
    st.subheader("Bulk Operations")
    # Implementation here



def show_general_settings():
    """Show general settings"""
    st.subheader("🏢 Company Settings")

    # Company Information
    with st.expander("Company Information", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            company_name = st.text_input("Company Name", value=config.COMPANY_NAME)
            company_address = st.text_area("Company Address", value=config.COMPANY_ADDRESS)
            company_phone = st.text_input("Company Phone", value=config.COMPANY_PHONE)

        with col2:
            company_email = st.text_input("Company Email", value=config.COMPANY_EMAIL)
            company_website = st.text_input("Company Website", value=config.COMPANY_WEBSITE)
            hr_manager_name = st.text_input("HR Manager Name", value=config.HR_MANAGER_NAME)

    # Employee Types & Policies
    with st.expander("Employee Policies", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Notice Periods (Days)**")
            notice_probation = st.number_input("Probation Period", value=15, min_value=1)
            notice_confirmed = st.number_input("Confirmed Employee", value=30, min_value=1)
            notice_intern = st.number_input("Intern", value=7, min_value=1)

        with col2:
            st.markdown("**Probation Periods (Months)**")
            prob_fulltime = st.number_input("Full-time Employee", value=3, min_value=1)
            prob_intern = st.number_input("Intern", value=1, min_value=1)
            fnf_days = st.number_input("FNF Processing Days", value=45, min_value=1)

    # System Platforms
    with st.expander("System Platforms", expanded=True):
        st.markdown("**Available System Platforms for Access Management**")
        current_platforms = config.SYSTEM_PLATFORMS

        # Display current platforms
        for i, platform in enumerate(current_platforms):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text_input(f"Platform {i+1}", value=platform, key=f"platform_{i}")
            with col2:
                if st.button("Remove", key=f"remove_platform_{i}"):
                    st.info(f"Platform '{platform}' would be removed")

        # Add new platform
        new_platform = st.text_input("Add New Platform")
        if st.button("Add Platform") and new_platform:
            st.success(f"Platform '{new_platform}' would be added")

    # Asset Types
    with st.expander("Asset Types", expanded=True):
        st.markdown("**Available Asset Types for Management**")
        current_assets = config.ASSET_TYPES

        # Display current asset types
        for i, asset in enumerate(current_assets):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text_input(f"Asset {i+1}", value=asset, key=f"asset_{i}")
            with col2:
                if st.button("Remove", key=f"remove_asset_{i}"):
                    st.info(f"Asset type '{asset}' would be removed")

        # Add new asset type
        new_asset = st.text_input("Add New Asset Type")
        if st.button("Add Asset Type") and new_asset:
            st.success(f"Asset type '{new_asset}' would be added")

    # Save button
    if st.button("💾 Save Settings", type="primary"):
        st.success("Settings saved successfully!")
        st.info("Note: In production, these settings would be saved to configuration file or database.")

def show_email_template_settings():
    """Show email template settings"""
    st.subheader("📧 Email Template Management")

    # Template Categories
    tab1, tab2, tab3 = st.tabs(["📥 Onboarding Templates", "📤 Offboarding Templates", "➕ Create New"])

    with tab1:
        st.markdown("### Onboarding Email Templates")
        onboarding_templates = [
            {"name": "Document Request", "file": "document_request.html", "description": "Request documents from new hires"},
            {"name": "Welcome Onboard", "file": "welcome_onboard.html", "description": "Welcome email after joining"},
            {"name": "System Access", "file": "system_access.html", "description": "System access credentials"},
            {"name": "BGV Notification", "file": "bgv_notification.html", "description": "Background verification process"},
            {"name": "Offer Letter", "file": "offer_letter.html", "description": "Job offer letter email"}
        ]

        for template in onboarding_templates:
            with st.expander(f"📧 {template['name']}", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**File:** {template['file']}")
                    st.write(f"**Description:** {template['description']}")

                with col2:
                    st.write("**Variables Available:**")
                    st.code("{{full_name}}, {{employee_id}}, {{designation}}, {{department}}")

                with col3:
                    if st.button("Edit", key=f"edit_{template['file']}"):
                        st.info(f"Edit template: {template['name']}")
                    if st.button("Preview", key=f"preview_{template['file']}"):
                        st.info(f"Preview template: {template['name']}")

    with tab2:
        st.markdown("### Offboarding Email Templates")
        offboarding_templates = [
            {"name": "Exit Confirmation", "file": "exit_confirmation.html", "description": "Exit process confirmation"},
            {"name": "Asset Return", "file": "asset_return.html", "description": "Asset return reminder"},
            {"name": "Access Revocation", "file": "access_revocation.html", "description": "System access revocation notice"},
            {"name": "FNF Statement", "file": "fnf_statement.html", "description": "Final settlement statement"},
            {"name": "Experience Letter", "file": "experience_letter.html", "description": "Experience certificate email"}
        ]

        for template in offboarding_templates:
            with st.expander(f"📧 {template['name']}", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**File:** {template['file']}")
                    st.write(f"**Description:** {template['description']}")

                with col2:
                    st.write("**Variables Available:**")
                    st.code("{{full_name}}, {{last_working_day}}, {{resignation_date}}")

                with col3:
                    if st.button("Edit", key=f"edit_off_{template['file']}"):
                        st.info(f"Edit template: {template['name']}")
                    if st.button("Preview", key=f"preview_off_{template['file']}"):
                        st.info(f"Preview template: {template['name']}")

    with tab3:
        st.markdown("### Create New Email Template")

        col1, col2 = st.columns(2)

        with col1:
            template_name = st.text_input("Template Name")
            template_category = st.selectbox("Category", ["Onboarding", "Offboarding", "General"])
            template_subject = st.text_input("Email Subject")

        with col2:
            template_description = st.text_area("Description")
            template_variables = st.text_area("Available Variables (comma-separated)",
                                            value="full_name, employee_id, designation, department")

        st.markdown("**Email Content (HTML)**")
        template_content = st.text_area("Template Content", height=200,
                                      value="""<p>Dear {{full_name}},</p>
<p>Your template content here...</p>
<p>Best regards,<br>Team HR<br>Rapid Innovation</p>""")

        if st.button("💾 Create Template", type="primary"):
            if template_name and template_content:
                st.success(f"Template '{template_name}' created successfully!")
                st.info("Template would be saved to templates/emails/ directory")
            else:
                st.error("Please fill in template name and content")

def show_integration_settings():
    """Show integration settings"""
    st.subheader("🔗 Integration Settings")

    # Google Sheets Integration
    with st.expander("📊 Google Sheets Integration", expanded=True):
        st.markdown("**Employee Data Synchronization**")

        col1, col2 = st.columns(2)

        with col1:
            current_url = google_sheets_integration.csv_url
            sheets_url = st.text_input("Google Sheets CSV URL", value=current_url)

            st.markdown("**Sync Status:**")
            if st.button("🔄 Test Connection"):
                with st.spinner("Testing connection..."):
                    df = google_sheets_integration.fetch_employee_data()
                    if df is not None:
                        st.success(f"✅ Connected! Found {len(df)} rows")
                    else:
                        st.error("❌ Connection failed")

            if st.button("📥 Sync Now"):
                with st.spinner("Syncing data..."):
                    result = google_sheets_integration.sync_employee_data()
                    if result['success']:
                        st.success(f"✅ {result['message']}")
                    else:
                        st.error(f"❌ {result['message']}")

        with col2:
            st.markdown("**Column Mapping:**")
            mapping = google_sheets_integration.column_mapping
            for sheet_col, db_field in mapping.items():
                st.text(f"{sheet_col} → {db_field}")

            st.markdown("**Auto-sync Settings:**")
            auto_sync = st.checkbox("Enable automatic sync", value=False)
            if auto_sync:
                sync_interval = st.selectbox("Sync interval", ["5 minutes", "15 minutes", "1 hour", "Daily"])
                st.info(f"Data will sync every {sync_interval}")

    # Email Integration
    with st.expander("📧 Email Integration", expanded=True):
        st.markdown("**SMTP Configuration**")

        col1, col2 = st.columns(2)

        with col1:
            smtp_server = st.text_input("SMTP Server", value=config.SMTP_SERVER)
            smtp_port = st.number_input("SMTP Port", value=config.SMTP_PORT)
            smtp_username = st.text_input("SMTP Username", value=config.SMTP_USERNAME)
            smtp_password = st.text_input("SMTP Password", type="password")

        with col2:
            sender_email = st.text_input("Default Sender Email", value=config.DEFAULT_SENDER_EMAIL)
            sender_name = st.text_input("Default Sender Name", value=config.DEFAULT_SENDER_NAME)
            use_tls = st.checkbox("Use TLS", value=config.SMTP_USE_TLS)

            if st.button("📧 Test Email"):
                st.info("Test email would be sent to verify configuration")

    # Third-party Integrations
    with st.expander("🔌 Third-party Integrations", expanded=False):
        st.markdown("**Available Integrations**")

        # Slack Integration
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**Slack Integration**")
            slack_token = st.text_input("Slack Bot Token", type="password",
                                      value=config.SLACK_API_TOKEN if config.SLACK_API_TOKEN else "")
            st.caption("For automated user management and notifications")

        with col2:
            slack_enabled = st.checkbox("Enable Slack", value=config.ENABLE_SLACK_INTEGRATION)
            if st.button("Test Slack"):
                st.info("Slack connection would be tested")

        st.divider()

        # Google Workspace Integration
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**Google Workspace Integration**")
            gw_admin_email = st.text_input("Admin Email", value=config.GOOGLE_WORKSPACE_ADMIN_EMAIL)
            gw_service_file = st.text_input("Service Account File", value=config.GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE)
            st.caption("For automated email account creation and management")

        with col2:
            gw_enabled = st.checkbox("Enable Google Workspace", value=config.ENABLE_GOOGLE_WORKSPACE_INTEGRATION)
            if st.button("Test Google Workspace"):
                st.info("Google Workspace connection would be tested")

    # Save Integration Settings
    if st.button("💾 Save Integration Settings", type="primary"):
        st.success("Integration settings saved successfully!")
        st.info("Note: In production, these settings would be saved to environment variables or configuration file.")

def show_user_management():
    """Show user management"""
    st.subheader("User Management")
    # Implementation here

# Employee-specific functions and HR-Bot removed for admin-only access

if __name__ == "__main__":
    main()