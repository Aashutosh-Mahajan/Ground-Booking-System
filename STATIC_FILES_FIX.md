# Static Files Not Loading on Render - Fix Guide

## Issue
After deploying to Render, the website shows unstyled HTML (no CSS) - the page looks like plain text with blue links.

## Root Causes & Solutions

### ✅ Fix 1: Ensure DEBUG=False on Render

**Problem:** WhiteNoise only serves static files when `DEBUG=False`

**Solution:** In Render Dashboard → Environment Variables:
```
DEBUG=False
```
(Or simply don't set DEBUG at all - it defaults to False)

### ✅ Fix 2: Verify Build Command Runs Collectstatic

**Problem:** Static files aren't being collected during deployment

**Solution:** In Render Dashboard → Settings → Build Command:
```bash
./build.sh
```

Or manually set:
```bash
pip install -r requirements.txt && python manage.py collectstatic --no-input --clear && python manage.py migrate
```

### ✅ Fix 3: Check ALLOWED_HOSTS

**Problem:** If ALLOWED_HOSTS is misconfigured, Django won't serve the site properly

**Solution:** Your settings.py now has:
```python
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default=".onrender.com,localhost,127.0.0.1").split(",")
```

In Render, you can either:
- Not set ALLOWED_HOSTS env var (uses default `.onrender.com`)
- Or set: `ALLOWED_HOSTS=.onrender.com,yourdomain.com`

### ✅ Fix 4: Verify WhiteNoise Configuration

**Problem:** WhiteNoise isn't properly configured

**Solution:** Already fixed in settings.py:
- ✅ WhiteNoise middleware is AFTER SecurityMiddleware
- ✅ STATICFILES_STORAGE uses WhiteNoise
- ✅ STATIC_ROOT points to 'staticfiles'

### ✅ Fix 5: Check Render Build Logs

**Solution:** Go to Render Dashboard → Your Service → Logs (during build):

Look for these lines:
```
Installing dependencies...
✓ Successfully installed whitenoise...
Collecting static files...
138 static files copied to '/opt/render/project/src/staticfiles'
Running migrations...
Build completed successfully!
```

If you see errors here, that's your issue.

### ✅ Fix 6: Force Clear Browser Cache

**Problem:** Browser is caching old version without styles

**Solution:** 
- Hard refresh: `Ctrl + F5` (Windows) or `Cmd + Shift + R` (Mac)
- Or open in Incognito/Private window

## Quick Deployment Checklist

Before deploying, ensure:

- [ ] `build.sh` has execute permissions (run locally: `git add build.sh --chmod=+x`)
- [ ] `DEBUG=False` in Render environment variables
- [ ] `ALLOWED_HOSTS` includes `.onrender.com`
- [ ] WhiteNoise is in MIDDLEWARE (after SecurityMiddleware)
- [ ] Build command is set to `./build.sh`
- [ ] Start command is `gunicorn groundbooking.wsgi:application`

## Verify Static Files Locally

Test before deploying:

```bash
# Set DEBUG to False
# In .env file: DEBUG=False

# Collect static files
python manage.py collectstatic --no-input --clear

# Run with gunicorn (production server)
gunicorn groundbooking.wsgi:application

# Open http://localhost:8000 - styles should load
```

If styles don't load locally with DEBUG=False, they won't work on Render either.

## Still Not Working?

### Check Render Service Logs

Go to Render Dashboard → Your Service → Logs (Runtime logs):

**Look for 404 errors on static files:**
```
GET /static/css/styles.css 404
```

This means collectstatic didn't run or failed.

**Look for WhiteNoise messages:**
```
[WhiteNoise] Serving static files from /opt/render/project/src/staticfiles
```

This confirms WhiteNoise is active.

### Manual Fix on Render Shell

1. Go to Render Dashboard → Your Service → Shell
2. Run:
```bash
python manage.py collectstatic --no-input --clear
ls -la staticfiles/css/
```

This will show if static files exist and where they are.

## Updated Files (Already Done)

✅ **settings.py:**
- Changed STATICFILES_STORAGE to `CompressedStaticFilesStorage` (more compatible)
- Added CSRF_TRUSTED_ORIGINS for `.onrender.com`
- Fixed ALLOWED_HOSTS to use environment variable with default

✅ **build.sh:**
- Added logging messages
- Added `--clear` flag to collectstatic to ensure fresh files
- Added error checking with `set -o errexit`

## Commit and Redeploy

After these fixes, commit and push:

```bash
git add .
git commit -m "Fix static files for Render deployment"
git push
```

Render will automatically redeploy. Watch the build logs carefully!

## Expected Build Output

You should see:
```
Installing dependencies...
...
Installing collected packages: whitenoise, gunicorn, ...
Successfully installed ...

Collecting static files...
138 static files copied to '/opt/render/project/src/staticfiles'.

Running migrations...
Operations to perform:
  Apply all migrations: admin, auth, booking, contenttypes, sessions
Running migrations:
  No migrations to apply.

Build completed successfully!
```

Then your CSS should load! 🎉
