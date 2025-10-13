# Gmail SMTP Setup for Render - Complete Guide

## Problem
Email sending fails on Render causing 500 errors when approving/rejecting bookings.

**Error in logs:** `TimeoutError` or `ConnectionError` to SMTP server

---

## ✅ SOLUTION: Proper Gmail SMTP Configuration

### Step 1: Generate Gmail App Password

**Important:** You MUST use an App Password, not your regular Gmail password!

1. **Enable 2-Factor Authentication (2FA):**
   - Go to https://myaccount.google.com/security
   - Under "How you sign in to Google", enable **2-Step Verification**
   - Follow the setup process

2. **Generate App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Sign in if prompted
   - Under "Select app", choose **Mail**
   - Under "Select device", choose **Other (Custom name)**
   - Type: `Render Ground Booking`
   - Click **Generate**
   - **Copy the 16-character password** (format: `xxxx xxxx xxxx xxxx`)
   - Remove spaces when using it: `xxxxxxxxxxxxxxxx`

### Step 2: Update Render Environment Variables

Go to **Render Dashboard** → Your Service → **Environment** tab

**Set these variables:**
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail-address@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password-no-spaces
DEFAULT_FROM_EMAIL=your-gmail-address@gmail.com
```

**Example:**
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=john.doe@gmail.com
EMAIL_HOST_PASSWORD=abcdwxyzefgh1234
DEFAULT_FROM_EMAIL=john.doe@gmail.com
```

**Important Notes:**
- Use the SAME Gmail address for both `EMAIL_HOST_USER` and `DEFAULT_FROM_EMAIL`
- Remove ALL spaces from the app password
- Make sure it's the app password, NOT your regular password
- `EMAIL_USE_TLS` must be exactly `True` (capital T)

### Step 3: Update Local .env File (for local testing)

Your `.env` file should have:
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-gmail@gmail.com
```

### Step 4: Code Changes Already Applied

**✅ Settings.py Updated:**
- Added `EMAIL_TIMEOUT = 30` to prevent hanging
- Configuration reads from environment variables

**✅ Views.py Updated:**
- Added try-except blocks around email sending
- Bookings are saved FIRST, then email attempts
- If email fails, user sees warning message
- Admin is notified to contact student manually
- No more 500 errors!

### Step 5: Deploy to Render

```bash
# Stage changes
git add .

# Commit
git commit -m "Fix email error handling with SMTP timeout"

# Push (Render auto-deploys)
git push origin development
```

---

## Testing

### Test Email Locally First:

1. **Update your local `.env` file** with your Gmail credentials
2. **Run the server:**
   ```bash
   python manage.py runserver
   ```
3. **Try approving a booking:**
   - Should send email successfully
   - Check terminal output for any errors

### Test on Render:

1. **Check environment variables are set** in Render Dashboard
2. **Wait for deployment** to complete
3. **Approve a booking** from admin dashboard
4. **Check Render Logs:**
   - Go to Dashboard → Your Service → Logs
   - Look for: `Booking approved and confirmation email sent`
   - Or: `Warning: Email failed but booking was saved` (if email failed)

---

## Troubleshooting

### Still Getting Errors?

#### 1. **Check Gmail App Password**
```
Error: "Authentication failed"
```
**Fix:**
- Make sure you're using App Password, not regular password
- Remove all spaces from the password
- Regenerate app password if needed

#### 2. **Port 587 Blocked on Render**
```
Error: "Connection timed out"
```
**Fix - Try Port 465 with SSL:**

Update Render environment variables:
```
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
```

Add to `settings.py`:
```python
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
```

#### 3. **Gmail Blocks Connection**
```
Error: "SMTP authentication failed" or "Less secure app access"
```
**Fix:**
- Make sure 2FA is enabled
- Use App Password (not regular password)
- Check Gmail activity: https://myaccount.google.com/notifications
- Allow the login if blocked

#### 4. **Email Still Fails but Want Booking to Work**
The code is already fixed to handle this!
- Booking WILL be saved
- Admin sees warning: "Email notification failed"
- No 500 error anymore
- Just inform student manually

---

## Alternative: Try Port 465

If port 587 doesn't work, Gmail also supports port 465 with SSL:

### Render Environment Variables:
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-gmail@gmail.com
```

### Add to settings.py:
```python
# After EMAIL_USE_TLS line:
EMAIL_USE_SSL = config("EMAIL_USE_SSL", default=False, cast=bool)
```

---

## What Was Fixed in Code

### ✅ In `views.py`:

**Before:**
```python
send_mail(...)  # ❌ Crashes if email fails
return redirect('admin_dashboard')
```

**After:**
```python
booking.status = 'Approved'
booking.save()  # ✅ Save FIRST

try:
    send_mail(...)
    messages.success(request, 'Email sent!')
except Exception as e:
    print(f"ERROR: Email failed: {e}")
    messages.warning(request, 'Email failed - inform student manually')
    pass  # ✅ Continue without crashing

return redirect('admin_dashboard')
```

**Result:**
- Booking is saved even if email fails
- User sees appropriate message
- No 500 Internal Server Error
- Admin can manually notify student if needed

---

## Important Notes

### Gmail Sending Limits:
- **500 emails per day** for regular Gmail accounts
- **2000 emails per day** for Google Workspace accounts
- If you hit the limit, emails will fail until next day

### Security Best Practices:
- ✅ Always use App Passwords, never regular password
- ✅ Keep app password in environment variables only
- ✅ Never commit passwords to Git
- ✅ Rotate app passwords periodically

### For Production:
Gmail SMTP may be unreliable on cloud platforms due to:
- Rate limiting
- IP blocks
- Timeouts

**If Gmail continues to fail on Render**, consider:
- SendGrid (100 emails/day free)
- Mailgun (100 emails/day free)  
- Amazon SES (62,000 emails/month free)

But for small projects, Gmail should work with proper app password setup!

---

## Quick Checklist

Before deploying, make sure:

- [ ] 2FA enabled on Gmail
- [ ] App Password generated (16 chars)
- [ ] App Password copied WITHOUT spaces
- [ ] All Render environment variables set correctly
- [ ] `EMAIL_HOST_USER` matches `DEFAULT_FROM_EMAIL`
- [ ] Code changes committed and pushed
- [ ] Render deployment completed
- [ ] Tested by approving a booking
- [ ] Checked Render logs for success/error messages

---

## Summary

**Current Status:**
✅ Email error handling fixed - no more 500 errors
✅ Bookings save successfully even if email fails
✅ Admin sees clear message if email fails
✅ 30-second timeout prevents hanging
✅ Try-except blocks prevent crashes

**Next Steps:**
1. Generate Gmail App Password
2. Set Render environment variables
3. Deploy changes
4. Test booking approval/rejection
5. Monitor logs for email success

Your booking system is now robust and won't crash due to email failures! 🎉
