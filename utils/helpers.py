import streamlit as st
from datetime import datetime, date, timedelta
import hashlib
import secrets
import string
import re
from typing import Dict, Any, List, Optional
import pandas as pd
from io import BytesIO
import base64

def init_session_state():
    """Initialize Streamlit session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Dashboard'
    
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}

def get_employee_status_badge(status: str) -> str:
    """Get HTML badge for employee status"""
    status_colors = {
        'active': '#28a745',
        'onboarding': '#17a2b8',
        'offboarding': '#ffc107',
        'exited': '#6c757d'
    }
    
    color = status_colors.get(status.lower(), '#6c757d')
    return f'<span style="background-color: {color}; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.875rem;">{status.upper()}</span>'

def format_date(date_obj: Any) -> str:
    """Format date for display"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d')
        except:
            return date_obj
    
    if isinstance(date_obj, (date, datetime)):
        return date_obj.strftime('%d %b %Y')
    
    return str(date_obj)

def format_currency(amount: float) -> str:
    """Format currency for display"""
    if amount is None:
        return "₹0"
    return f"₹{amount:,.2f}"

def calculate_days_between(start_date: date, end_date: date) -> int:
    """Calculate days between two dates"""
    if not start_date or not end_date:
        return 0
    return (end_date - start_date).days

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove spaces and hyphens
    phone = phone.replace(' ', '').replace('-', '')
    # Check if it's a valid Indian phone number
    pattern = r'^[6-9]\d{9}$'
    return re.match(pattern, phone) is not None

def validate_pan(pan: str) -> bool:
    """Validate PAN card format"""
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    return re.match(pattern, pan.upper()) is not None

def validate_aadhaar(aadhaar: str) -> bool:
    """Validate Aadhaar number format"""
    # Remove spaces
    aadhaar = aadhaar.replace(' ', '')
    pattern = r'^\d{12}$'
    return re.match(pattern, aadhaar) is not None

def generate_password(length: int = 12) -> str:
    """Generate a secure random password"""
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def calculate_ctc_breakdown(annual_ctc: float) -> Dict[str, float]:
    """Calculate CTC breakdown for full-time employees"""
    # Sample breakdown - adjust as per company policy
    basic = annual_ctc * 0.40
    hra = basic * 0.50
    special_allowance = annual_ctc * 0.25
    medical_allowance = 15000  # Fixed
    books_periodical = 12000  # Fixed
    health_club = 6000  # Fixed
    internet_telephone = 24000  # Fixed
    
    # Calculate remaining as special allowance
    total_fixed = basic + hra + medical_allowance + books_periodical + health_club + internet_telephone
    pf_employer = basic * 0.12  # 12% of basic
    special_allowance = annual_ctc - total_fixed - pf_employer
    
    return {
        'basic_salary': round(basic, 2),
        'hra': round(hra, 2),
        'special_allowance': round(special_allowance, 2),
        'medical_allowance': medical_allowance,
        'books_periodical': books_periodical,
        'health_club': health_club,
        'internet_telephone': internet_telephone,
        'pf_employer': round(pf_employer, 2),
        'gross_ctc': round(annual_ctc - pf_employer, 2),
        'total_ctc': round(annual_ctc, 2)
    }

def calculate_fnf(employee_data: Dict[str, Any], exit_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate Full and Final settlement"""
    fnf_components = {}
    
    # Basic calculations
    monthly_salary = employee_data.get('ctc', 0) / 12
    daily_salary = monthly_salary / 30
    
    # Calculate pending salary
    last_working_day = exit_data.get('last_working_day')
    last_salary_date = exit_data.get('last_salary_date')
    
    if last_working_day and last_salary_date:
        pending_days = (last_working_day - last_salary_date).days
        fnf_components['pending_salary'] = round(daily_salary * pending_days, 2)
    else:
        fnf_components['pending_salary'] = 0
    
    # Leave encashment (if applicable)
    leave_balance = exit_data.get('leave_balance', 0)
    if employee_data.get('employee_type') == 'full_time' and leave_balance > 0:
        fnf_components['leave_encashment'] = round(daily_salary * leave_balance, 2)
    else:
        fnf_components['leave_encashment'] = 0
    
    # Gratuity (if applicable - for employees with 5+ years of service)
    years_of_service = exit_data.get('years_of_service', 0)
    if years_of_service >= 5:
        basic_salary = employee_data.get('ctc', 0) * 0.4 / 12  # 40% of CTC as basic
        fnf_components['gratuity'] = round((basic_salary * 15 * years_of_service) / 26, 2)
    else:
        fnf_components['gratuity'] = 0
    
    # Deductions
    fnf_components['notice_period_recovery'] = exit_data.get('notice_period_recovery', 0)
    fnf_components['other_deductions'] = exit_data.get('other_deductions', 0)
    
    # Calculate total
    total_earnings = (fnf_components['pending_salary'] + 
                     fnf_components['leave_encashment'] + 
                     fnf_components['gratuity'])
    
    total_deductions = (fnf_components['notice_period_recovery'] + 
                       fnf_components['other_deductions'])
    
    fnf_components['total_earnings'] = round(total_earnings, 2)
    fnf_components['total_deductions'] = round(total_deductions, 2)
    fnf_components['net_amount'] = round(total_earnings - total_deductions, 2)
    
    return fnf_components

def export_to_excel(dataframes: Dict[str, pd.DataFrame], filename: str = "hr_export.xlsx") -> bytes:
    """Export multiple dataframes to Excel file"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Format header
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0066CC',
                'font_color': 'white',
                'border': 1
            })
            
            # Write header
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Auto-fit columns
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.set_column(col_idx, col_idx, column_width + 2)
    
    output.seek(0)
    return output.getvalue()

def create_download_link(data: bytes, filename: str, text: str) -> str:
    """Create a download link for binary data"""
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{text}</a>'

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return filename.split('.')[-1].lower() if '.' in filename else ''

def is_valid_file_type(filename: str, allowed_extensions: set) -> bool:
    """Check if file type is allowed"""
    extension = get_file_extension(filename)
    return extension in allowed_extensions

def format_file_size(size_bytes: int) -> str:
    """Format file size for display"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def calculate_probation_end_date(joining_date: date, probation_months: int) -> date:
    """Calculate probation end date"""
    # Add months to date
    month = joining_date.month - 1 + probation_months
    year = joining_date.year + month // 12
    month = month % 12 + 1
    day = min(joining_date.day, [31, 29 if year % 4 == 0 and year % 100 != 0 or year % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    
    return date(year, month, day)

def get_notification_icon(notification_type: str) -> str:
    """Get icon for notification type"""
    icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'onboarding': '🚀',
        'offboarding': '👋',
        'document': '📄',
        'system': '💻',
        'reminder': '🔔'
    }
    return icons.get(notification_type, '📌')

def add_notification(message: str, notification_type: str = 'info'):
    """Add notification to session state"""
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    
    notification = {
        'message': message,
        'type': notification_type,
        'icon': get_notification_icon(notification_type),
        'timestamp': datetime.now(),
        'read': False
    }
    
    st.session_state.notifications.insert(0, notification)
    
    # Keep only last 50 notifications
    if len(st.session_state.notifications) > 50:
        st.session_state.notifications = st.session_state.notifications[:50]

def show_notifications():
    """Display notifications in Streamlit"""
    if 'notifications' in st.session_state and st.session_state.notifications:
        with st.expander(f"🔔 Notifications ({len(st.session_state.notifications)})", expanded=False):
            for idx, notif in enumerate(st.session_state.notifications[:10]):  # Show last 10
                col1, col2 = st.columns([10, 1])
                with col1:
                    st.markdown(f"{notif['icon']} **{notif['message']}**")
                    st.caption(f"{format_date(notif['timestamp'])} at {notif['timestamp'].strftime('%H:%M')}")
                with col2:
                    if st.button("✖️", key=f"notif_close_{idx}"):
                        st.session_state.notifications.pop(idx)
                        st.rerun()
                
                if idx < len(st.session_state.notifications) - 1:
                    st.divider()

def create_audit_log(user_id: str, action: str, entity_type: str, 
                    entity_id: int = None, details: Dict[str, Any] = None):
    """Create audit log entry"""
    from database.connection import get_db_session
    from database.models import AuditLog
    import json
    
    try:
        with get_db_session() as session:
            audit_log = AuditLog(
                user_id=user_id,
                user_name=st.session_state.get('user', {}).get('name', 'System'),
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                new_values=json.dumps(details) if details else None
            )
            session.add(audit_log)
            session.commit()
    except Exception as e:
        print(f"Error creating audit log: {str(e)}")

def get_report_date_range(report_type: str) -> tuple:
    """Get default date range for reports"""
    today = date.today()
    
    if report_type == 'daily':
        return today, today
    elif report_type == 'weekly':
        start = today - timedelta(days=today.weekday())
        return start, today
    elif report_type == 'monthly':
        start = today.replace(day=1)
        return start, today
    elif report_type == 'quarterly':
        quarter = (today.month - 1) // 3
        start_month = quarter * 3 + 1
        start = date(today.year, start_month, 1)
        return start, today
    elif report_type == 'yearly':
        start = date(today.year, 1, 1)
        return start, today
    else:
        # Last 30 days
        return today - timedelta(days=30), today

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove special characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    if len(name) > 100:
        name = name[:100]
    
    return f"{name}.{ext}" if ext else name

def parse_salary_components(ctc_text: str) -> Dict[str, float]:
    """Parse salary components from text (for BGV or offer letters)"""
    components = {}
    
    # Common patterns
    patterns = {
        'basic': r'basic.*?₹?\s*([\d,]+)',
        'hra': r'hra.*?₹?\s*([\d,]+)',
        'special_allowance': r'special.*?allowance.*?₹?\s*([\d,]+)',
        'ctc': r'ctc.*?₹?\s*([\d,]+)',
        'gross': r'gross.*?₹?\s*([\d,]+)'
    }
    
    for component, pattern in patterns.items():
        match = re.search(pattern, ctc_text.lower())
        if match:
            value = match.group(1).replace(',', '')
            components[component] = float(value)
    
    return components