# 🔧 Multi-Signature Solution Design

## Current System Analysis
- User has ONE signature stored in `signature_data` field
- Signature appears on ALL invoices automatically
- No selection mechanism for different signatures

## Proposed Solution Architecture

### 1. Database Schema Changes
```sql
-- New table for storing multiple signatures per user
CREATE TABLE user_signatures (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES user(id),
    signature_name VARCHAR(100) NOT NULL,
    signature_data TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES user(id)
);

-- Add signature selection to invoices
ALTER TABLE invoice ADD COLUMN selected_signature_id INTEGER REFERENCES user_signatures(id);
```

### 2. Implementation Features
- **Multiple Signatures**: Users can upload unlimited signatures
- **Named Signatures**: Each signature has a descriptive name (e.g., "CEO Signature", "Manager Signature")
- **Default Signature**: One signature marked as default for new invoices
- **Per-Invoice Selection**: Each invoice can have its own signature
- **Signature Management**: Upload, delete, rename signatures
- **Backward Compatibility**: Existing invoices use current signature

### 3. UI Components
- **Signature Management**: Upload multiple signatures with names
- **Signature Selection**: Dropdown in invoice creation/edit
- **Signature Preview**: Show preview of all signatures
- **Default Setting**: Mark one signature as default

### 4. PDF Integration
- Use selected signature ID instead of current_user.signature_data
- Fallback to default signature if none selected
- Maintain current UI positioning and styling

## Files to Modify
1. `app.py` - Database models and routes
2. `templates/create_invoice.html` - Add signature selection
3. `templates/edit_invoice.html` - Add signature selection  
4. `templates/signature_upload.html` - Multi-signature management
5. `templates/print_invoice.html` - Use selected signature
6. Database migration script

This solution provides maximum flexibility while maintaining ease of use.
