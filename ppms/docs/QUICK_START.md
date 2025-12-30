# Quick Start Guide

## 5-Minute Setup

### Prerequisites
- Python 3.8+ installed
- Firebase account with project created
- serviceAccountKey.json downloaded

### Quick Steps

**Step 1: Clone/Extract Project**
```bash
cd d:\prog\ppms
```

**Step 2: Setup Python Environment**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Step 3: Configure Firebase**
```bash
# Copy and edit .env
copy .env.example .env
# Edit .env with your Firebase credentials
# Place serviceAccountKey.json in project root
```

**Step 4: Run Application**
```bash
python src/main.py
```

**Step 5: Login**
- Email: `admin@ppms.com`
- Password: `Admin@123`

## First Day Operations

### Morning Startup
1. Start application
2. Create operator users (if needed)
3. Configure fuel types (Petrol, Diesel, CNG)
4. Setup tanks with stock levels
5. Assign operators to nozzles

### During Day
1. Record fuel sales
2. Submit meter readings
3. Process customer payments
4. Record expenses
5. Monitor stock levels

### Evening Closeout
1. Close operator shifts
2. Reconcile sales
3. Generate daily report
4. Backup data
5. Review for next day

## Key Features to Explore

### 1. Dashboard
- View real-time stock
- Check today's sales
- See low stock alerts
- Monitor pending credits

### 2. Record Sales
- Quick sale entry
- Multiple payment methods
- Customer credit support
- Automatic tax calculation

### 3. View Reports
- Daily sales summary
- Monthly profit & loss
- Stock levels
- Customer outstanding
- Operator performance

### 4. Manage Settings (Admin Only)
- Create users
- Configure fuel types
- Manage tanks
- Track expenses
- View audit logs

## User Roles Quick Reference

| Role | Can Do | Cannot Do |
|------|--------|-----------|
| **Admin** | Everything | Nothing - Full access |
| **Manager** | Manage operations, view reports | Cannot create/delete users |
| **Operator** | Record sales, submit readings | Cannot access other menus |
| **Accountant** | View finances, generate reports | Cannot record sales |

## Common Tasks

### Record a Sale
1. Go to Dashboard
2. Click "Record Sale"
3. Select nozzle
4. Enter quantity
5. Choose payment method
6. Click Save

### View Daily Report
1. Go to Dashboard
2. Click "View Reports"
3. Select "Daily Sales"
4. Choose date
5. Click "Generate"

### Close Operator Shift
1. Go to Dashboard
2. Click "Shift Management"
3. Click "End Shift"
4. Enter closing cash amount
5. Review reconciliation
6. Confirm

### Add New Customer
1. Go to Dashboard
2. Click "Manage Customers"
3. Click "Add Customer"
4. Enter details
5. Set credit limit
6. Save

### Record Expense
1. Go to Dashboard
2. Click "Manage Expenses"
3. Click "Add Expense"
4. Select category
5. Enter amount
6. Save

## Troubleshooting Quick Help

### App Won't Start
```bash
# Check logs
dir logs\

# Verify Python installation
python --version

# Reinstall dependencies
pip install -r requirements.txt
```

### Login Failed
- Verify email is correct (case-sensitive)
- Check internet connection
- Ensure Firebase project is active
- Try password reset

### Firebase Connection Error
- Check `.env` file for correct credentials
- Verify `serviceAccountKey.json` exists
- Check internet connectivity
- Verify Firebase project exists

### Slow Performance
- Check internet speed
- Clear browser cache
- Restart application
- Check database quotas

## Support Resources

### Documentation
- `docs/INSTALLATION.md` - Detailed installation
- `docs/USER_MANAGEMENT.md` - User guide
- `docs/DATABASE_SCHEMA.md` - Data structure
- `docs/API_REFERENCE.md` - Developer docs
- `docs/DEPLOYMENT_GUIDE.md` - Production setup

### Database Initialization

**Sample data is provided in** `docs/SAMPLE_DATA.json`

To load sample data:
1. Open Firebase Console
2. Go to Firestore Database
3. Import the sample data
4. Or manually add documents

### Getting Help

1. **Check Documentation** - Most answers in docs/
2. **Review Logs** - Check logs/ directory
3. **Test Manually** - Verify connectivity
4. **Contact Admin** - For account issues

## Default Credentials

**Admin Account**
- Email: `admin@ppms.com`
- Password: `Admin@123`

⚠️ **IMPORTANT**: Change these immediately after first login!

## System Architecture Overview

```
PPMS Desktop App (PyQt5)
         ↓
  Services Layer
  ├── Authentication
  ├── Database
  ├── Business Logic
  └── Reporting
         ↓
  Firebase Backend
  ├── Firestore (Data)
  ├── Authentication
  ├── Realtime DB
  └── Storage
```

## Performance Tips

1. **Keep Internet Fast**
   - Use stable WiFi
   - Regular bandwidth tests
   - Dedicated connection for app

2. **Regular Backups**
   - Daily automated backups
   - Weekly manual exports
   - Monthly archive copies

3. **Data Cleanup**
   - Archive old reports monthly
   - Delete test data after testing
   - Archive historical data yearly

4. **Security**
   - Change passwords monthly
   - Use strong passwords (12+ chars)
   - Enable audit logging
   - Review access logs regularly

## Next Steps After Setup

1. ✅ **Customize Fuel Types** - Add actual prices
2. ✅ **Setup Tanks** - Configure storage tanks
3. ✅ **Create Users** - Add operators and staff
4. ✅ **Configure Nozzles** - Setup pump machines
5. ✅ **Load Historical Data** - If migrating
6. ✅ **Train Users** - Ensure staff knowledge
7. ✅ **Schedule Backups** - Automated daily
8. ✅ **Monitor Performance** - First week focus

## Useful Shortcuts

| Action | Method |
|--------|--------|
| Logout | Click Logout button |
| Refresh Dashboard | Press F5 |
| Save | Ctrl+S or Click Save |
| Clear Form | Ctrl+N or Click Cancel |

## Emergency Procedures

### If System Crashes
1. Note last successful action
2. Restart application
3. Check logs for errors
4. Contact administrator
5. Restore from backup if needed

### If Firebase Unavailable
1. Check internet connection
2. Verify Firebase status page
3. Wait 5-10 minutes for recovery
4. Try again
5. Contact Firebase support if persists

### Data Loss Prevention
- Never force-quit application
- Always use proper shutdown
- Enable auto-backup
- Export critical data regularly
- Maintain offline copies

## Health Check (Daily)

```
□ Application starts normally
□ Can login with credentials
□ Dashboard displays data
□ Can record test sale
□ Can view reports
□ Internet connection stable
□ No error messages
□ All menus accessible
```

## Maintenance Checklist (Weekly)

```
□ Review error logs
□ Check low stock alerts
□ Verify payment reconciliation
□ Generate backup
□ Test report generation
□ Monitor performance metrics
□ Update user permissions if needed
□ Review access logs
```

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Status**: Ready to Deploy
