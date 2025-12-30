# User Management Guide

## Creating Users

### Via Firebase Console

1. **Authentication Setup**:
   - Go to Firebase Console → Authentication
   - Enable "Email/Password" provider
   - Click "Add user"
   - Enter email and password

2. **User Profile Creation**:
   - Go to Firestore → users collection
   - Create new document with ID = Firebase UID
   - Add required fields

### Via Application

```python
from src.services.auth_service import AuthenticationService
from src.config.firebase_config import FirebaseConfig

FirebaseConfig.initialize()
auth_service = AuthenticationService()

# Create new user
success, msg, uid = auth_service.create_user(
    email="newuser@ppms.com",
    password="SecurePass@123",
    name="John Doe",
    role="manager",
    department="Operations"
)

if success:
    print(f"User created: {uid}")
else:
    print(f"Error: {msg}")
```

## User Roles & Permissions

### 1. Admin
**Permissions**: Full system control

**Features**:
- Create/manage all users
- Access all reports
- Configure system settings
- View audit logs
- Manage fuel types
- Manage tanks
- Manage nozzles
- Override any operation

**Login**: admin@ppms.com / Admin@123

### 2. Manager
**Permissions**: Daily operations & reports

**Features**:
- View dashboard
- Manage fuel purchases
- Monitor tank levels
- Record expenses
- Generate reports
- Manage shifts
- View all sales records
- Cannot delete or modify other manager's data

**Typical Users**: Shift supervisors, Station managers

### 3. Operator
**Permissions**: Fuel sales entry only

**Features**:
- Record fuel sales
- Submit nozzle readings
- View own shift data
- Cannot access other operators' records
- Cannot view reports
- Cannot manage system settings

**Typical Users**: Pump attendants, Fuel dispensers

### 4. Accountant
**Permissions**: Ledger, expenses, and profit reports

**Features**:
- View ledger
- Manage expenses
- Generate financial reports
- View customer outstanding
- Cannot record sales
- Cannot manage fuel operations
- Cannot create users

**Typical Users**: Finance staff, Accounts officers

## User Deactivation

### Disable User Account

```python
auth_service.disable_user("user_uid")
```

**Process**:
1. User status set to "inactive"
2. Firebase Auth account disabled
3. User cannot login
4. Historical data retained
5. Can be reactivated

## Password Management

### Change Password

```python
auth_service.change_password("user_uid", "new_password")
```

**Requirements**:
- Minimum 6 characters
- Can contain special characters
- Case-sensitive

### Reset Password

**Via Firebase Console**:
1. Select user
2. Click "..." menu
3. "Reset password"
4. Email sent to user

**Via Email**:
- Firebase sends reset link
- User clicks and creates new password
- Link valid for 24 hours

## User Login

### First Login
1. Navigate to PPMS application
2. Enter email address
3. Enter password
4. Click "Login"

### Remember Device
- Check "Remember me" option
- Application stores credential locally (encrypted)

### Session Management
- Sessions expire after 30 minutes of inactivity
- User can manually logout
- Only one active session per user

## Activity Monitoring

### View User Activity

**Admin View**:
```python
from src.services.database_service import DatabaseService

db_service = DatabaseService()

# Get user's recent activity
logs = db_service.list_documents(
    'audit_logs',
    [('user_id', '==', user_id)]
)
```

**Audit Log Fields**:
- User ID
- Action (login, logout, create, update, delete)
- Entity modified
- Timestamp
- IP address
- Old and new values

## User Performance Metrics

### For Managers

View operator performance:
- Daily sales volume
- Customer interactions
- Shift reconciliation
- Error rates
- Performance trends

## Security Best Practices

1. **Strong Passwords**:
   - Use mixed case letters
   - Include numbers
   - Add special characters
   - Minimum 12 characters for admin accounts

2. **Regular Password Changes**:
   - Change password every 90 days
   - After team member departure
   - If account appears compromised

3. **Access Control**:
   - Only grant necessary permissions
   - Regular audit of user permissions
   - Deactivate unused accounts
   - Review access logs regularly

4. **Account Security**:
   - Never share login credentials
   - Use strong email passwords
   - Enable 2FA when available
   - Keep phone number updated

## Troubleshooting

### User Can't Login

**Check**:
1. Email address correct (case-sensitive in display)
2. Password correct
3. Account status is "active"
4. User exists in Firebase Auth
5. User exists in Firestore users collection

**Solution**:
1. Verify email in Firebase Auth
2. Check user document in Firestore
3. Ensure status = "active"
4. Try password reset
5. Check firewall/network access

### Lost Password

**For Users**:
1. Click "Forgot Password?" on login
2. Enter email address
3. Check email for reset link
4. Click link to reset password
5. Set new password
6. Login with new password

**For Admin**:
1. Go to Firebase Auth
2. Select user
3. Reset password
4. Send user the reset email

### Account Locked

**Cause**: Multiple failed login attempts

**Resolution**:
1. Admin can disable/re-enable account
2. Or wait 24 hours for auto-unlock
3. Reset password to secure

## User Reporting

### Generate User Activity Report

```python
# Example: Monthly user activity report
from datetime import datetime, timedelta

start_date = datetime.now() - timedelta(days=30)
logs = db_service.list_documents(
    'audit_logs',
    [('timestamp', '>=', start_date)]
)

# Group by user and count activities
```

### Export User List

1. Admin → User Management
2. Click "Export Users"
3. Choose format (CSV/Excel)
4. Data exported with:
   - User ID
   - Name
   - Email
   - Role
   - Status
   - Department
   - Last login

## Compliance & Audit

- All user creations logged
- All password changes logged
- All login attempts tracked
- Audit log retained 180 days
- Deletion tracked with user who deleted
- Regular compliance reports generated

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Status**: Production Ready
