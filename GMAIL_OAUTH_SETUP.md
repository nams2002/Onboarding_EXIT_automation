# Gmail OAuth Setup Guide

## Issue Resolution: "unauthorized_client" Error

The Gmail integration is failing with an "unauthorized_client" error. This guide provides step-by-step instructions to resolve this issue.

## Root Cause
The service account lacks proper domain-wide delegation and OAuth scopes for Google Workspace Admin SDK.

## Solution Steps

### 1. Google Cloud Console Setup

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Select your project**: `careergig`
3. **Enable Required APIs**:
   - Go to "APIs & Services" > "Library"
   - Enable the following APIs:
     - Admin SDK API
     - Gmail API
     - Google Workspace Admin SDK

### 2. Service Account Configuration

1. **Go to "IAM & Admin" > "Service Accounts"**
2. **Find your service account**: `hr-automation@careergig.iam.gserviceaccount.com`
3. **Click on the service account email**
4. **Go to "Details" tab**
5. **Copy the "Unique ID" (Client ID)**: `100704378063801142841`

### 3. Google Workspace Admin Console Setup

1. **Go to Google Workspace Admin Console**: https://admin.google.com/
2. **Navigate to Security > API Controls**
3. **Click "Domain-wide Delegation"**
4. **Click "Add new"**
5. **Enter the following details**:
   - **Client ID**: `100704378063801142841`
   - **OAuth Scopes** (comma-separated):
     ```
     https://www.googleapis.com/auth/admin.directory.user,
     https://www.googleapis.com/auth/admin.directory.group,
     https://www.googleapis.com/auth/admin.directory.orgunit,
     https://www.googleapis.com/auth/gmail.settings.basic,
     https://www.googleapis.com/auth/gmail.settings.sharing
     ```
6. **Click "Authorize"**

### 4. Verify Admin Email Permissions

1. **Ensure the admin email `hrms@rapidinnovation.dev` has Super Admin privileges**
2. **If not, grant Super Admin access**:
   - Go to "Directory" > "Users"
   - Find `hrms@rapidinnovation.dev`
   - Click on the user
   - Go to "Admin roles and privileges"
   - Assign "Super Admin" role

### 5. Update Service Account Scopes

The service account needs these specific scopes:

```python
scopes = [
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/admin.directory.group', 
    'https://www.googleapis.com/auth/admin.directory.orgunit',
    'https://www.googleapis.com/auth/gmail.settings.basic',
    'https://www.googleapis.com/auth/gmail.settings.sharing'
]
```

### 6. Test the Configuration

Run the following test to verify the setup:

```python
from modules.mcp.gmail_mcp_server import GmailMCPServer
import asyncio

async def test_gmail_connection():
    config = {
        'service_account_file': 'service-account.json',
        'admin_email': 'hrms@rapidinnovation.dev',
        'domain': 'rapidinnovation.dev',
        'default_ou': '/Employees'
    }
    
    gmail_server = GmailMCPServer(config)
    result = await gmail_server.connect()
    print(f"Connection result: {result}")

# Run the test
asyncio.run(test_gmail_connection())
```

### 7. Common Issues and Solutions

#### Issue: "Client is unauthorized"
- **Solution**: Ensure domain-wide delegation is properly configured
- **Check**: Client ID matches the service account's Unique ID
- **Verify**: All required scopes are added

#### Issue: "Access denied"
- **Solution**: Verify the admin email has Super Admin privileges
- **Check**: The admin email exists in the Google Workspace domain

#### Issue: "API not enabled"
- **Solution**: Enable Admin SDK API and Gmail API in Google Cloud Console

### 8. Security Considerations

1. **Limit Service Account Permissions**: Only grant necessary scopes
2. **Regular Key Rotation**: Rotate service account keys periodically
3. **Monitor Usage**: Track API usage in Google Cloud Console
4. **Audit Access**: Regularly review domain-wide delegation settings

### 9. Environment Variables

Ensure these environment variables are correctly set:

```bash
MCP_GMAIL_SERVICE_ACCOUNT_FILE=service-account.json
MCP_GMAIL_ADMIN_EMAIL=hrms@rapidinnovation.dev
MCP_GMAIL_DOMAIN=rapidinnovation.dev
MCP_GMAIL_DEFAULT_OU=/Employees
```

### 10. Troubleshooting Commands

Test Gmail API access:
```bash
python -c "
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load credentials
with open('service-account.json', 'r') as f:
    creds_info = json.load(f)

credentials = service_account.Credentials.from_service_account_info(
    creds_info,
    scopes=['https://www.googleapis.com/auth/admin.directory.user']
)

# Delegate to admin user
delegated_credentials = credentials.with_subject('hrms@rapidinnovation.dev')

# Test connection
service = build('admin', 'directory_v1', credentials=delegated_credentials)
result = service.users().list(domain='rapidinnovation.dev', maxResults=1).execute()
print('Success! Found users:', len(result.get('users', [])))
"
```

## Next Steps

1. Follow the setup steps above
2. Test the Gmail connection
3. Verify email sending functionality
4. Monitor for any remaining issues

## Support

If issues persist:
1. Check Google Cloud Console logs
2. Verify Google Workspace audit logs
3. Contact Google Workspace support if needed
