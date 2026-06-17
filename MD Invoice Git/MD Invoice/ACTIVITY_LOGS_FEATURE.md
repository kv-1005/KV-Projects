# 📊 Activity Logs Feature - Complete Documentation

## 🎯 Overview

The Activity Logs feature provides comprehensive audit trail functionality for the MD Invoice application. It tracks **who did what, when, where, why, and how** across all system operations.

## ✨ Key Features

### 1. **Comprehensive Tracking**
- **User Authentication**: Login/logout events
- **Invoice Operations**: Create, update, delete
- **Customer Management**: Add, edit, delete
- **Company Settings**: Updates
- **Purchase Orders**: Delete operations
- **Failed Login Attempts**: Security monitoring
- And more...

### 2. **Detailed Information Captured**
Each log entry contains:
- **Who**: Username and User ID
- **What**: Action type (create, update, delete, login, logout, etc.)
- **Which Entity**: Type (invoice, customer, company, etc.) and ID
- **Resource Identifier**: Human-readable identifier (invoice number, customer name, etc.)
- **When**: Precise timestamp
- **Where**: IP address
- **Context**: Description and metadata
- **Changes**: Old value and new value (for updates)

### 3. **Advanced Filtering & Search**
- Search across username, resource identifier, and description
- Filter by action type (create, update, delete, login, etc.)
- Filter by entity type (invoice, customer, company, etc.)
- Filter by specific user
- Date range filtering (from/to)
- Combine multiple filters

### 4. **Export Functionality**
- Export filtered logs as CSV
- Includes all log fields
- Timestamp in filename
- Ready for external analysis

### 5. **Clean UI**
- Paginated table view
- Color-coded action badges
- Responsive design
- Quick filter access
- Real-time filtering

## 🗄️ Database Schema

### ActivityLog Model

```python
class ActivityLog(db.Model):
    # Who
    user_id: Foreign Key to User
    username: String (stored for history even if user deleted)
    
    # What
    action_type: String (create, update, delete, view, export, login, logout)
    entity_type: String (invoice, customer, vendor, company, purchase_order, signature, user)
    entity_id: Integer (ID of affected entity)
    
    # Context
    resource_identifier: String (invoice_number, customer_name, etc.)
    old_value: Text (previous state for updates)
    new_value: Text (new state for updates)
    
    # When
    timestamp: DateTime (indexed for performance)
    ip_address: String (IPv4 or IPv6)
    
    # Additional
    description: Text (human-readable description)
    metadata: Text (JSON string for additional data)
```

## 🚀 Setup Instructions

### 1. Create the Database Table

Run the migration script:

```bash
python create_activity_logs_table.py
```

Or let the app create it automatically on first run (it will call `db.create_all()` in `init_db()`).

### 2. Verify Installation

1. Start the application
2. Navigate to the "Activity Logs" menu item
3. Perform some actions (login, create invoice, etc.)
4. Check that logs appear in real-time

## 📍 Navigation

Access the Activity Logs page via:
- **Menu Bar**: Click "Activity Logs" in the sidebar
- **URL**: `/activity-logs`

## 🔍 Usage Examples

### Viewing All Activity
1. Go to Activity Logs page
2. Click "Apply Filters" (no filters = all activities)

### Filtering by User
1. Select a user from the "User" dropdown
2. Click "Apply Filters"

### Finding Specific Invoice Actions
1. Enter invoice number in "Search" field
2. Or select "invoice" in "Entity" dropdown
3. Click "Apply Filters"

### Viewing Login Attempts
1. Select "login" or "login_attempt_failed" in "Action" dropdown
2. Click "Apply Filters"

### Exporting Logs
1. Apply desired filters
2. Click "Export CSV" button
3. Download will start immediately

## 🎨 Action Type Color Coding

- **Create**: Green badge (success)
- **Update**: Yellow badge (warning)
- **Delete**: Red badge (danger)
- **Login**: Blue badge (info)
- **Logout**: Gray badge (secondary)
- **Failed Login**: Red badge (danger)
- **View**: Blue badge (primary)
- **Export**: Blue badge (info)
- **Other**: Gray badge

## 🔒 Security Features

1. **Immutable Logs**: Once created, logs are never modified
2. **Immediate Commit**: Each log entry is committed immediately for audit integrity
3. **User Tracking**: Stores username even if user is later deleted
4. **IP Tracking**: Records IP address for all actions
5. **Failed Attempt Logging**: Tracks failed login attempts

## 🛠️ Technical Implementation

### Logging Function

```python
log_activity(
    action_type='create',           # What action
    entity_type='invoice',          # What entity
    entity_id=123,                  # Entity ID
    resource_identifier='INV-001',  # Human-readable ID
    old_value='previous',           # Previous state
    new_value='current',            # New state
    description='Invoice created',  # Description
    metadata={'extra': 'data'}      # Additional JSON data
)
```

### Currently Logged Operations

#### Authentication
- ✅ Successful login
- ✅ Failed login attempts
- ✅ Logout

#### Company
- ✅ Create company
- ✅ Update company details

#### Customers
- ✅ Create customer
- ✅ Update customer

#### Invoices
- ✅ Create invoice
- ✅ Delete invoice (OTP verified)
- ✅ Delete invoice (password verified)

#### Purchase Orders
- ✅ Delete purchase order

### Adding More Logging

To add logging to any new route:

```python
from app import log_activity

# After a successful operation
db.session.commit()

# Log the activity
log_activity(
    action_type='your_action',
    entity_type='your_entity',
    entity_id=entity.id,
    resource_identifier='resource_name',
    description='Human readable description'
)
```

**Important**: Call `log_activity()` AFTER `db.session.commit()` to ensure the entity exists in the database.

## 📊 Performance Considerations

1. **Indexed Timestamp**: Fast chronological queries
2. **Pagination**: Loads 20 entries per page
3. **Efficient Filtering**: Uses database indexes
4. **Async Logging**: Logging failures don't break main functionality
5. **Automatic Cleanup**: Consider periodic archiving for very large datasets

## 🔄 Future Enhancements (Optional)

Potential additions:
- User activity summary dashboard
- Real-time log streaming
- Log retention policies
- Advanced analytics
- Email alerts for critical actions
- GraphQL API for mobile apps
- Integration with external SIEM tools

## 📝 Notes

- Logs are stored permanently unless manually deleted
- Export includes all fields except metadata for readability
- IP address may be empty behind proxies (consider adding X-Forwarded-For support)
- Large old_value/new_value fields are truncated in table view
- CSV export includes full descriptions and values

## ✅ Testing Checklist

- [x] Database model created
- [x] Logging function implemented
- [x] Routes added with filtering
- [x] Export functionality working
- [x] UI template created
- [x] Navigation menu updated
- [x] Login/logout logging
- [x] Invoice CRUD logging
- [x] Customer CRUD logging
- [x] Company update logging
- [x] Purchase order deletion logging
- [x] Migration script created

## 🎉 Success!

Your MD Invoice application now has comprehensive activity logging! Every important action is tracked, searchable, and exportable.

---

**Built with ❤️ for MD Invoice**
*Comprehensive audit trail for business operations*

