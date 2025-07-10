# Email & Letter Generation System

## 🚀 **System Overview**

The HR Automation System now includes a comprehensive email and letter generation system that integrates with Google Sheets employee data and provides automated communication workflows.

## 📧 **Email Templates Available**

### **Onboarding Email Templates**
1. **welcome_onboard.html** - Welcome message for new employees
2. **initial_document_request.html** - Document requirements for joining

### **Offboarding Email Templates**
1. **exit_initiation.html** - Exit process initiation notification
2. **asset_return.html** - Asset return requirements

## 📄 **Letter Templates Available**

### **Onboarding Letter Templates**
1. **offer_letter.html** - Job offer letter
2. **appointment_letter.html** - Appointment confirmation letter
3. **contract_agreement.html** - Employment contract
4. **internship_letter.html** - Internship offer letter

### **Offboarding Letter Templates**
1. **experience_letter.html** - Experience certificate
2. **internship_certificate.html** - Internship completion certificate

## ⚙️ **System Features**

### **Smart Email Routing**
- **Primary Recipient**: Employee's email from Google Sheets
- **CC Recipients**: 
  - HR team (hrms@rapidinnovation.dev)
  - Reporting manager (if different from HR)
- **Automatic deduplication** of CC emails

### **Template Processing**
- **Dynamic content** based on employee data
- **Automatic subject line generation**
- **HTML and plain text versions**
- **Variable substitution** from Google Sheets data

### **Employee Type Handling**
- **Full-time employees**: All onboarding/offboarding templates
- **Interns**: Specialized internship templates
- **Contractors**: Standard templates with appropriate modifications

## 🔧 **Technical Implementation**

### **Key Components**

1. **EmployeeActions** (`modules/employee/employee_actions.py`)
   - Main orchestrator for email/letter operations
   - Template selection logic
   - Data preparation and routing

2. **EmailSender** (`modules/email/email_Sender.py`)
   - SMTP/SendGrid integration
   - Template rendering engine
   - Attachment handling

3. **Template System** (`templates/`)
   - Jinja2-based HTML templates
   - Base template inheritance
   - Variable substitution

### **Configuration**

```python
# Email Configuration (.env)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=hrms@rapidinnovation.dev
SMTP_PASSWORD=wgbo flwk vldd vqxg
DEFAULT_SENDER_EMAIL=hrms@rapidinnovation.dev
DEFAULT_SENDER_NAME=Rapid Innovation HR
```

## 📋 **Usage Instructions**

### **From Employee Details Modal**

1. **Navigate to Employee Management**
2. **Select an employee** from the list
3. **Go to Actions tab**
4. **Choose Email or Letter option**:

#### **Send Email**
- Select appropriate template from dropdown
- Click "Send Email" button
- System automatically:
  - Loads employee data from Google Sheets
  - Renders template with employee information
  - Sends to employee with HR and manager in CC
  - Shows success/failure notification

#### **Generate Letter**
- Select appropriate letter template
- Click "Generate Letter" button
- System generates formatted letter
- Downloads/saves letter file

### **Template Selection Logic**

```python
# Email Templates
if employee_status == 'active':
    templates = onboarding_email_templates
else:
    templates = offboarding_email_templates

# Letter Templates  
if employee_type == 'intern':
    templates = ['internship_letter.html', 'internship_certificate.html']
elif employee_status == 'active':
    templates = onboarding_letter_templates
else:
    templates = offboarding_letter_templates
```

## 🎯 **Data Integration**

### **Google Sheets Fields Used**
- `full_name` - Employee full name
- `email` - Primary recipient email
- `employee_id` - Unique identifier
- `department` - Employee department
- `employee_type` - full_time/intern/contractor
- `reporting_manager` - Manager name
- `manager_email` - Manager email for CC
- `status` - active/inactive

### **Template Variables Available**
```python
template_data = {
    'full_name': 'John Doe',
    'employee_id': 'RI001',
    'department': 'Engineering',
    'employee_type': 'full_time',
    'reporting_manager': 'Jane Smith',
    'company_name': 'Rapid Innovation Pvt. Ltd.',
    'hr_email': 'hrms@rapidinnovation.dev',
    'current_date': 'January 15, 2025'
}
```

## 🔒 **Security & Compliance**

### **Email Security**
- TLS encryption for SMTP
- Secure credential storage in environment variables
- No sensitive data in email logs

### **Data Privacy**
- Only Google Sheets data is used
- No additional personal information stored
- Audit trail for sent emails

## 🚀 **Future Enhancements**

### **Planned Features**
1. **Email scheduling** - Send emails at specific times
2. **Bulk email operations** - Send to multiple employees
3. **Email tracking** - Read receipts and delivery status
4. **Custom template editor** - Create new templates via UI
5. **Approval workflows** - Manager approval before sending
6. **Integration with calendar** - Schedule follow-ups

### **Advanced Templates**
1. **Performance review notifications**
2. **Birthday and anniversary wishes**
3. **Policy update announcements**
4. **Training completion certificates**
5. **Salary revision letters**

## 📊 **Monitoring & Logs**

### **Email Logs**
- All sent emails are logged
- Success/failure tracking
- Recipient and CC information
- Template used and timestamp

### **Error Handling**
- Graceful failure handling
- User-friendly error messages
- Detailed logging for troubleshooting
- Automatic retry mechanisms

## 🎉 **Benefits**

1. **Automated Communication** - Reduces manual email drafting
2. **Consistent Branding** - Professional templates with company branding
3. **Data Accuracy** - Direct integration with Google Sheets
4. **Audit Trail** - Complete record of all communications
5. **Time Savings** - Instant email/letter generation
6. **Scalability** - Handles growing employee base efficiently

The system is now fully operational and ready for production use!
