# 🚀 RAILWAY ENVIRONMENT VARIABLES

## 📧 **Email Configuration for Railway**

Add these environment variables to your Railway project:

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=vignesharkumaravelan@gmail.com
MAIL_PASSWORD=gpgfjwkbderuxxxj
```

## 🏢 **Company Information**

```bash
COMPANY_NAME=MAHADEVI&CO
COMPANY_EMAIL=mahadevico@yahoo.in
```

## 🔐 **Security**

```bash
SECRET_KEY=your-secret-key-change-this-in-production-use-strong-random-key
FLASK_ENV=production
FLASK_DEBUG=False
```

## 📊 **Application Settings**

```bash
INVOICE_PREFIX=INV
DEFAULT_TAX_RATE=18.0
DEFAULT_DUE_DAYS=30
INVOICES_PER_PAGE=20
CUSTOMERS_PER_PAGE=20
```

## 🗄️ **Database**

Railway will automatically provide `DATABASE_URL` for PostgreSQL.

---

## 🎯 **How to Add Variables on Railway**

1. Go to your Railway project dashboard
2. Click on your service
3. Go to "Variables" tab
4. Click "New Variable"
5. Add each variable one by one
6. Railway will automatically redeploy

---

## ✅ **After Adding Variables**

Your OTP deletion will work perfectly:
- ✅ OTP sent to both email addresses
- ✅ Deletion only after OTP verification
- ✅ Works on Railway with PostgreSQL
- ✅ CASCADE constraints applied automatically

**You're all set!** 🎉
