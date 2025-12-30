# Firestore Security Rules for PPMS

## Overview
These rules implement role-based access control (RBAC) with fine-grained permissions for each user role.

## Rule Structure

### Users Collection
- **Read**: Users can read their own profile. Admins can read any user.
- **Write**: Users can update their own profile. Admins can manage all users.
- **Validation**: Requires email, name, and role fields.

### Fuel Types Collection
- **Read**: Authenticated users can read (needed for dropdowns).
- **Write**: Only admins and managers can create/update fuel types.
- **Validation**: Requires id, name, and unit_price.

### Tanks Collection
- **Read**: Authenticated users can read tank information.
- **Write**: Only admins and managers can manage tanks.
- **Validation**: Requires id, name, fuel_type_id, and capacity.

### Nozzles Collection
- **Read**: Authenticated users can read nozzle data.
- **Write**: Only admins and managers can manage nozzles.
- **Validation**: Requires id, machine_id, and nozzle_number.

### Readings Collection
- **Read**: Authenticated users can read readings.
- **Write**: Any authenticated user can record readings.
- **Validation**: Requires id, nozzle_id, date, and readings data.

### Sales Collection
- **Read**: Authenticated users can read sales records.
- **Write**: Operators and managers can record sales.
- **Validation**: Requires transaction data with amount and quantities.

### Purchases Collection
- **Read**: Authenticated users can read purchase history.
- **Write**: Only admins and managers can record purchases.
- **Validation**: Requires supplier and invoice information.

### Customers Collection
- **Read**: Authenticated users can read customer data.
- **Write**: Managers and accountants can manage customers.
- **Validation**: Requires name and phone number.

### Expenses Collection
- **Read**: Authenticated users can read expenses.
- **Write**: Managers and accountants can record expenses.
- **Validation**: Requires date, category, and amount.

### Shifts Collection
- **Read**: Authenticated users can read shift data.
- **Write**: Any authenticated user can manage shifts they own.
- **Validation**: Requires shift timing and operator information.

### Payments Collection
- **Read**: Authenticated users can read payment records.
- **Write**: Any authenticated user can record payments.
- **Validation**: Requires customer, amount, and date information.

### Reports Collection
- **Read**: Authenticated users can read reports.
- **Write**: Managers and accountants can generate reports.
- **Validation**: Requires report type and generated_by information.

### Audit Logs Collection
- **Read**: Only admins can read audit logs.
- **Write**: Any authenticated user can create logs (for audit trail).
- **Validation**: Requires action, entity_type, and timestamp.

## Implementation Notes

1. **Role-Based Access**: All write operations check the user's role field.
2. **Timestamp Validation**: All records must include created_at timestamp.
3. **User Tracking**: Sensitive operations include user_id reference.
4. **Soft Deletes**: Records use status field instead of hard deletion.
5. **Data Integrity**: Validation rules ensure required fields exist.

## Testing Rules

Before deploying to production:

```bash
# Test with Firebase Emulator Suite
firebase emulators:start

# Run security rules tests
firebase test:firestore
```

## Updating Rules

1. Update rules in Firebase Console
2. Or use Firebase CLI:
   ```bash
   firebase deploy --only firestore:rules
   ```

## Audit Trail

All modifications are logged in audit_logs collection with:
- User who made the change
- Timestamp of change
- Type of entity modified
- Old and new values
- IP address (if tracked)

## Data Privacy

- Customer personal data is encrypted in transit
- Payment information is handled securely
- Access logs are maintained for 180 days
- Sensitive fields are excluded from unnecessary queries
