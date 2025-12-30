# Deployment & Windows Distribution Guide

## Pre-Deployment Checklist

- [ ] All unit tests pass
- [ ] Code review completed
- [ ] Security audit done
- [ ] Documentation updated
- [ ] Backups configured
- [ ] Monitoring setup
- [ ] Support team trained
- [ ] Performance tested

## Building Windows Executable

### Step 1: Prepare Build Environment

```bash
# Activate virtual environment
venv\Scripts\activate

# Install PyInstaller
pip install pyinstaller==6.0.0

# Create build directory
mkdir build
mkdir dist
```

### Step 2: Create PyInstaller Spec

Create `ppms.spec` in project root:

```python
# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('.env', '.'),
        ('docs', 'docs'),
    ],
    hiddenimports=['firebase_admin', 'PyQt5'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PPMS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PPMS'
)
```

### Step 3: Build Executable

```bash
pyinstaller ppms.spec --distpath ./dist --buildpath ./build
```

### Step 4: Test Executable

```bash
# Test the built exe
dist\PPMS\PPMS.exe
```

## Creating MSI Installer

### Option 1: Using WiX Toolset (Professional)

1. Install WiX Toolset
2. Create `ppms.wxs`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
    <Product Id="*" Name="Petrol Pump Management System" 
             Language="1033" Version="1.0.0.0"
             Manufacturer="PPMS"
             UpgradeCode="GUID-HERE">

        <Package InstallerVersion="200" Compressed="yes" />
        <Media Id="1" Cabinet="PPMS.cab" EmbedCab="yes" />

        <Feature Id="ProductFeature" Title="PPMS" Level="1">
            <ComponentRef Id="MainExecutable" />
        </Feature>
    </Product>
</Wix>
```

3. Compile:
```bash
candle.exe ppms.wxs
light.exe ppms.wixobj -out ppms.msi
```

### Option 2: Using NSIS (Free)

1. Install NSIS
2. Create `ppms.nsi`:

```nsis
!include "MUI2.nsh"

; Version Information
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "Petrol Pump Management System"
VIAddVersionKey "FileVersion" "1.0.0.0"

; Installer settings
Name "Petrol Pump Management System"
OutFile "PPMS-Setup-1.0.0.exe"
InstallDir "$ProgramFiles\PPMS"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "dist\PPMS\*.*"
  
  CreateShortcut "$SMPROGRAMS\PPMS.lnk" "$INSTDIR\PPMS.exe"
  CreateShortcut "$DESKTOP\PPMS.lnk" "$INSTDIR\PPMS.exe"
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  Delete "$SMPROGRAMS\PPMS.lnk"
  Delete "$DESKTOP\PPMS.lnk"
SectionEnd
```

3. Build:
```bash
makensis ppms.nsi
```

## Portable Distribution

For portable/no-install version:

```bash
# Create portable package
mkdir PPMS-Portable-1.0.0
xcopy dist\PPMS PPMS-Portable-1.0.0\app
copy .env.example PPMS-Portable-1.0.0\.env
copy serviceAccountKey.json PPMS-Portable-1.0.0\
copy INSTALLATION.md PPMS-Portable-1.0.0\README.txt

# Zip for distribution
tar -czf PPMS-Portable-1.0.0.zip PPMS-Portable-1.0.0\
```

## System Requirements for Deployment

### Minimum Requirements
- Windows 10 or later
- 2GB RAM
- 500MB free disk space
- Internet connection for Firebase
- Stable WiFi/LAN connectivity

### Recommended Requirements
- Windows 10/11 (Latest updates)
- 4GB+ RAM
- 1GB free disk space
- Dedicated WiFi access point
- Backup internet connection

## Installation Methods

### Method 1: MSI Installer (Recommended for Enterprise)
```bash
# Run installer
PPMS-Setup-1.0.0.msi

# Accept license
# Choose installation directory
# Complete installation
# Run from Start Menu or Desktop shortcut
```

### Method 2: Portable Zip (Recommended for Testing)
```bash
# Extract zip file
# Navigate to folder
# Run PPMS.exe

# No installation required
# Can run from USB drive
```

### Method 3: From Source (Development)
```bash
# Install Python 3.8+
# Follow installation guide in docs/INSTALLATION.md
python src/main.py
```

## Configuration After Deployment

### First Run Setup
1. Copy `.env` template to `.env`
2. Add Firebase credentials to `.env`
3. Place `serviceAccountKey.json` in app directory
4. Run application

### Initial Data Setup
1. Create admin user
2. Add fuel types
3. Configure tanks
4. Setup nozzles
5. Create initial users
6. Load sample data

## Version Control & Updates

### Update Mechanism
```python
# Check for updates
def check_for_updates():
    latest_version = get_latest_version_from_server()
    if latest_version > CURRENT_VERSION:
        show_update_prompt()
        download_and_install_update()
```

### Update Distribution
- Check on startup
- Notify user of available updates
- Download silently in background
- Restart required for update

### Rollback Procedure
```bash
# Keep previous version
backup_current_version()

# Install new version
install_update()

# If issues, restore
restore_backup()
```

## Performance Tuning for Deployment

### Database Connection Pool
```python
# Implement connection pooling
pool_size = 10
max_overflow = 20
```

### Caching Configuration
```python
# Enable caching for production
CACHE_ENABLED = True
CACHE_TTL = 3600  # 1 hour
```

### Memory Management
```python
# Optimize memory usage
GC_ENABLED = True
GC_INTERVAL = 300  # 5 minutes
```

## Monitoring & Logging

### Log Management
```bash
# Logs location
C:\Users\{User}\AppData\Local\PPMS\logs\

# Log rotation
Daily rotation
Keep last 30 days
```

### Performance Monitoring
- Database query times
- UI response times
- Network latency
- Memory usage
- CPU usage

### Health Checks
```python
def health_check():
    firebase_ok = check_firebase_connection()
    database_ok = check_database_connection()
    storage_ok = check_local_storage()
    return firebase_ok and database_ok and storage_ok
```

## Security in Production

### Credential Management
- Never commit credentials
- Use environment variables
- Secure `.env` file (700 permissions)
- Rotate keys regularly

### Network Security
- Use HTTPS only
- Implement VPN for remote access
- Firewall rules for database
- Rate limiting for APIs

### Data Protection
- Backup daily
- Encrypt sensitive data
- Audit trail enabled
- Regular security scans

## Support & Troubleshooting

### Common Issues

**Issue: Application won't start**
- Check system requirements
- Verify Firebase credentials
- Check internet connection
- Review logs in C:\Users\{User}\AppData\Local\PPMS\logs\

**Issue: Firebase connection failed**
- Verify `.env` configuration
- Check serviceAccountKey.json
- Verify internet connectivity
- Check Firebase project status

**Issue: Database operations slow**
- Check network connection
- Clear application cache
- Restart application
- Check Firebase quotas

## Post-Deployment

### User Training
- Complete documentation provided
- Video tutorials available
- Live support during go-live
- User guide in docs/ folder

### Feedback Collection
- User feedback form in app
- Bug reporting mechanism
- Feature request process
- Regular support reviews

## Rollout Plan

### Phase 1: Testing (Week 1)
- Install on test machines
- Load test data
- Conduct UAT
- Fix issues

### Phase 2: Pilot (Week 2)
- Deploy to 1-2 locations
- Monitor closely
- Gather feedback
- Make adjustments

### Phase 3: Full Rollout (Week 3-4)
- Deploy to all locations
- Train all users
- Provide support
- Monitor performance

### Phase 4: Optimization (Week 5+)
- Monitor performance
- Optimize configuration
- Update documentation
- Plan future enhancements

---

**Version**: 1.0.0  
**Last Updated**: December 2025  
**Status**: Production Ready
