# Installation & Setup Guide

## System Requirements

- **OS**: Windows 10/11 or Linux
- **Python**: 3.8 or higher
- **RAM**: Minimum 2GB, Recommended 4GB+
- **Storage**: 500MB for application and dependencies

## Pre-Installation Steps

### 1. Install Python
Download Python 3.8+ from [python.org](https://www.python.org)
Ensure "Add Python to PATH" is checked during installation

### 2. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create a new project named "PPMS"
3. Enable these services:
   - Firestore Database
   - Realtime Database
   - Authentication (Email/Password)

### 3. Download Service Account Key
1. Go to Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Save as `serviceAccountKey.json`

## Installation Steps

### Step 1: Clone/Download Project
```bash
cd d:\prog
git clone https://github.com/yourrepo/ppms.git
# Or extract the provided ZIP file
cd ppms
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Configure Environment
1. Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` with your Firebase credentials:
   ```
   FIREBASE_API_KEY=your_api_key_here
   FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
   FIREBASE_DATABASE_URL=https://your_project.firebaseio.com
   FIREBASE_PROJECT_ID=your_project_id
   FIREBASE_STORAGE_BUCKET=your_project.appspot.com
   FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   FIREBASE_APP_ID=your_app_id
   FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json
   ```

3. Place `serviceAccountKey.json` in project root

### Step 6: Setup Firebase Database Structure

Create Firestore collections in Firebase Console with indexes:

**Fuel Types:**
```
Document ID: auto
Fields: id, name, unit_price, tax_percentage, status, created_at, created_by
Index: status, created_at
```

**Tanks:**
```
Document ID: auto
Fields: id, name, fuel_type_id, capacity, current_stock, minimum_stock, location, last_reading_date
Index: status, fuel_type_id
```

**Users:**
```
Document ID: uid (from Firebase Auth)
Fields: email, name, role, status, department, phone, created_at
Index: role, status
```

Continue similarly for other collections (see `database-schema.md`)

### Step 7: Create Admin User

**Option A: Via Firebase Console**
1. Go to Authentication
2. Create user with email: `admin@ppms.com`, password: `Admin@123`
3. Go to Firestore → users collection
4. Add document with uid matching the user
5. Add fields: name: "Administrator", role: "admin", status: "active", department: "Management"

**Option B: Via Python Script**
```python
from src.services.auth_service import AuthenticationService
from src.config.firebase_config import FirebaseConfig

FirebaseConfig.initialize()
auth_service = AuthenticationService()
success, msg, uid = auth_service.create_user(
    "admin@ppms.com",
    "Admin@123",
    "Administrator",
    "admin",
    "Management"
)
print(f"Admin user created: {uid}")
```

## Running the Application

### Start Application
```bash
python src/main.py
```

### Default Login Credentials
- **Email**: admin@ppms.com
- **Password**: Admin@123

## Troubleshooting

### Issue: "serviceAccountKey.json not found"
**Solution**: Ensure the file is in project root directory

### Issue: "Firebase initialization failed"
**Solution**: 
1. Verify credentials in `.env` file
2. Check Firebase console for correct project
3. Ensure Firestore database is created

### Issue: "PyQt5 not found"
**Solution**: 
```bash
pip install PyQt5==5.15.9
```

### Issue: "Port already in use"
**Solution**: Change port in config or close conflicting application

### Issue: "Connection timeout"
**Solution**:
1. Check internet connection
2. Verify Firebase project is accessible
3. Check firewall/proxy settings

## Testing Setup

### Run Unit Tests
```bash
python -m pytest tests/ -v
```

### Run with Test Data
Test data is provided in `docs/sample-data.json`

## Database Backup

### Backup Firestore
```bash
firebase firestore:export ./backups/ppms_backup_$(date +%Y%m%d)
```

### Restore from Backup
```bash
firebase firestore:import ./backups/ppms_backup_20240101
```

## Performance Tuning

### Optimize Queries
1. Create indexes for frequently filtered fields
2. Use pagination for large datasets
3. Cache read-heavy data locally

### Database Limits
- Firestore: 1 write/second per document
- Batch operations: Max 500 writes per batch
- Document size: Max 1MB per document

## Security Hardening

### Change Admin Password
After first login, go to User Management and reset password

### Enable 2FA
Implement via Firebase Custom Claims

### Regular Backups
Schedule weekly exports:
```bash
# Add to Windows Task Scheduler or cron
firebase firestore:export ./backups/ppms_backup_weekly
```

### Access Logs
Review audit logs regularly in Admin Panel

## Deployment

### Windows EXE Generation
```bash
pyinstaller --onefile --windowed \
  --icon=assets/logo.ico \
  --name PPMS \
  --distpath ./dist \
  --buildpath ./build \
  src/main.py
```

### Distribution
1. Create MSI installer using NSIS
2. Include serviceAccountKey.json in installer
3. Auto-start on system login

## Support & Troubleshooting

For issues:
1. Check logs in `./logs/` directory
2. Review error messages in console
3. Consult Firebase documentation
4. Contact system administrator

## Next Steps

1. [Create test users for each role](USER_MANAGEMENT.md)
2. [Configure fuel types and tanks](FUEL_SETUP.md)
3. [Setup nozzles and machines](DISPENSER_SETUP.md)
4. [Load sample data](SAMPLE_DATA.md)
5. [Review security rules](SECURITY_RULES.md)

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Status**: Installation Complete
