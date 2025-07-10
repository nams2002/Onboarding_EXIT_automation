# HR Onboarding/Offboarding Automation System

A comprehensive HR automation system built with Streamlit for managing employee onboarding and offboarding processes at Rapid Innovation. **Admin-only access system.**

## Features

### Onboarding Module
- **Document Collection**: Automated email requests and tracking for required documents
- **Offer Letter Generation**: Dynamic PDF generation with CTC calculations
- **System Access Management**: Track and manage access to various platforms (Gmail, Slack, etc.)
- **Appointment Letter Generation**: Formal appointment letters after offer acceptance
- **Background Verification**: Automated BGV process for experienced hires
- **Progress Tracking**: Real-time status of onboarding tasks

### Offboarding Module
- **Exit Initiation**: Manager approval workflow and exit confirmation
- **Asset Management**: Track and manage company asset returns
- **Access Revocation**: Systematic removal of system access
- **Final Settlement**: FnF calculation and processing
- **Experience Letter**: Automated generation of experience certificates
- **Exit Checklist**: Comprehensive tracking of exit tasks

### Additional Features
- **Email Automation**: Template-based emails with tracking
- **Document Management**: Secure storage and verification of documents
- **Dashboard & Analytics**: Real-time metrics and insights
- **Multi-role Access**: Role-based access for HR Admin, Manager, and Employees
- **Audit Trail**: Complete logging of all actions
- **Report Generation**: Various HR reports and analytics

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.9+
- **Database**: PostgreSQL
- **PDF Generation**: ReportLab
- **Email**: SMTP/SendGrid
- **File Storage**: Local/AWS S3
- **Authentication**: Streamlit-Authenticator

## Installation

### Prerequisites

1. Python 3.9 or higher
2. PostgreSQL database
3. SMTP server access or SendGrid API key (for emails)
4. (Optional) AWS S3 credentials for cloud storage

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/hr-automation-system.git
cd hr-automation-system
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Unix or MacOS
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` file with your configuration:
```
DATABASE_URL=postgresql://username:password@localhost:5432/hr_automation
SECRET_KEY=your-secure-secret-key-here
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@company.com
SMTP_PASSWORD=your-email-password
# ... other configurations
```

### Step 5: Set Up Database

1. Create PostgreSQL database:
```sql
CREATE DATABASE hr_automation;
```

2. Run database initialization:
```bash
python -c "from database.connection import init_database, seed_initial_data; init_database(); seed_initial_data()"
```

### Step 6: Run the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Usage

### Default Login Credentials

For demo purposes, use these credentials:

**HR Admin:**
- Username: admin
- Password: admin123

**HR Manager:**
- Username: manager
- Password: manager123

**Employee:**
- Username: employee
- Password: employee123

⚠️ **Important**: Change these credentials in production!

### Basic Workflow

#### Onboarding Process:
1. **Start Onboarding**: HR initiates onboarding for new employee
2. **Document Collection**: System sends email requesting documents
3. **Document Upload**: Employee uploads required documents
4. **Verification**: HR verifies uploaded documents
5. **Offer Generation**: System generates offer letter
6. **Offer Acceptance**: Employee accepts and signs offer
7. **System Access**: IT/HR grants system access
8. **Appointment Letter**: Generate after offer acceptance
9. **BGV Process**: Initiate for experienced employees
10. **Completion**: Mark onboarding as complete

#### Offboarding Process:
1. **Exit Initiation**: Employee/Manager initiates exit
2. **Manager Approval**: Manager approves and plans knowledge transfer
3. **Knowledge Transfer**: Complete handover activities
4. **Asset Return**: Track and confirm asset returns
5. **Access Revocation**: Remove system access
6. **Final Settlement**: Calculate and process FnF
7. **Experience Letter**: Generate after settlement
8. **Exit Complete**: Mark offboarding as complete

## Project Structure

```
hr-automation-system/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── config.py                       # Configuration settings
├── .env                           # Environment variables
├── database/
│   ├── models.py                  # Database models
│   └── connection.py              # Database connection
├── modules/
│   ├── onboarding/               # Onboarding modules
│   ├── offboarding/              # Offboarding modules
│   ├── email/                    # Email functionality
│   ├── document_generation/      # PDF generation
│   └── employee/                 # Employee management
├── templates/
│   ├── emails/                   # Email templates
│   └── letters/                  # Letter templates
├── utils/                        # Utility functions
└── static/                       # Static files
```

## Configuration

### Email Templates

Email templates are stored in the database and can be customized through the Settings page. Default templates include:
- Document request emails
- Welcome onboard emails
- Exit confirmation emails
- System access notifications

### Letter Templates

Letter templates use HTML and can be customized in `templates/letters/`:
- Offer letters (Full-time, Intern, Contractor)
- Appointment letters
- Experience certificates
- Internship certificates

### Employee Types

The system supports three employee types:
- **Full-time**: Complete onboarding with BGV
- **Intern**: Simplified process with internship certificate
- **Contractor**: Contract-based with hourly billing

## API Integration

### Slack Integration

To enable Slack integration:
1. Create a Slack app
2. Add OAuth scopes: `users:write`, `users:read`
3. Add the token to `.env`:
```
SLACK_API_TOKEN=xoxb-your-token
ENABLE_SLACK_INTEGRATION=True
```

### Google Workspace

For Google Workspace integration:
1. Enable Admin SDK API
2. Create service account
3. Configure in `.env`:
```
GOOGLE_WORKSPACE_ADMIN_EMAIL=admin@company.com
GOOGLE_WORKSPACE_SERVICE_ACCOUNT_FILE=path/to/key.json
ENABLE_GOOGLE_WORKSPACE_INTEGRATION=True
```

## Security

- All passwords are hashed using bcrypt
- Session management with secure cookies
- Role-based access control (RBAC)
- Audit logging for all critical actions
- Encrypted document storage
- HTTPS recommended for production

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check PostgreSQL is running
   - Verify DATABASE_URL in .env
   - Ensure database exists

2. **Email Sending Failed**
   - Verify SMTP credentials
   - Check firewall/port settings
   - Enable "Less secure apps" for Gmail

3. **File Upload Issues**
   - Check upload folder permissions
   - Verify file size limits
   - Ensure allowed file types

4. **PDF Generation Error**
   - Install system fonts if needed
   - Check ReportLab dependencies
   - Verify template paths

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and queries:
- Email: teamhr@rapidinnovation.com
- Documentation: [Wiki](https://github.com/your-org/hr-automation/wiki)
- Issues: [GitHub Issues](https://github.com/your-org/hr-automation/issues)

## Acknowledgments

- Rapid Innovation HR Team for requirements and testing
- Streamlit community for the excellent framework
- All contributors who helped improve this system