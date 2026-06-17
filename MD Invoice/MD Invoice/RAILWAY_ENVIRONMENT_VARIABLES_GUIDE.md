# 🔧 RAILWAY ENVIRONMENT VARIABLES GUIDE

## 📋 **ALL ENVIRONMENT VARIABLES TO ADD**

Go to **Railway Dashboard → Your Project → Variables** and add these:

### **🔑 PASSWORD VARIABLES**

```bash
# Invoice Deletion Password (Required)
DELETE_PASSWORD=Mahadevi&Co2211

# Admin Login Password (Required)  
DEFAULT_ADMIN_PASSWORD=admin123
```

### **📧 EMAIL CONFIGURATION**

```bash
# Email Settings (for notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=vigneshar kumaravelan@gmail.com
MAIL_PASSWORD=gpgfjwkbderuxxxj
MAIL_TIMEOUT=10

# Company Information
COMPANY_NAME=MD Invoice System
COMPANY_EMAIL=vigneshar kumaravelan@gmail.com
```

### **🔐 SECURITY CONFIGURATION**

```bash
# Flask Security
SECRET_KEY=your-random-secret-key-here
```

---

## 🎯 **HOW TO CHANGE PASSWORDS**

### **Change Invoice Deletion Password:**

1. Go to **Railway Dashboard**
2. **Variables** tab
3. Find `DELETE_PASSWORD`
4. Change value to your new password
5. **Save** - Railway auto-redeploys

### **Change Admin Login Password:**

1. Go to **Railway Dashboard**  
2. **Variables** tab
3. Find `DEFAULT_ADMIN_PASSWORD`
4. Change value to your new password
5. **Save** - Railway auto-redeploys

---

## 💡 **BENEFITS OF ENVIRONMENT VARIABLES**

### ✅ **Security**
- Passwords not stored in code
- Easy to change without redeploying
- Different passwords for different environments

### ✅ **Flexibility**  
- Change passwords anytime
- No code changes required
- Immediate effect after Railway redeploy

### ✅ **Control**
- Centralized password management
- Easy password rotation
- Environment-specific passwords

---

## 🔒 **PASSWORD RECOMMENDATIONS**

### **For DELETE_PASSWORD:**
- Use company-specific phrase
- Include numbers and symbols
- Example: `Mahadevi&Co2024!`

### **For DEFAULT_ADMIN_PASSWORD:**
- Strong, unique password
- Minimum 12 characters
- Mix of letters, numbers, symbols
- Example: `Admin@MD2024#Secure!`

---

## 📊 **CURRENT CONFIGURATION**

Your current setup:
- ✅ **DELETE_PASSWORD**: `Mahadevi&Co2211` (changeable via Railway)
- ✅ **DEFAULT_ADMIN_PASSWORD**: `admin123` (changeable via Railway)
- ✅ **Email configuration**: Already set up
- ✅ **Company info**: Configured

## 🚀 **DEPLOYMENT STATUS**

Environment variables are now:
- ✅ Integrated into the application
- ✅ Configurable via Railway dashboard  
- ✅ Immediately effective on config change
- ✅ No code changes needed for password updates

**Perfect setup for flexible password management!**
