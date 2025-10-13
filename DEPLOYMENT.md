# Render Deployment Guide

## Files Created for Deployment

✅ **Procfile** - Tells Render how to run Django with Gunicorn
✅ **runtime.txt** - Specifies Python 3.13.0
✅ **build.sh** - Build script to install dependencies, collect static files, and run migrations
✅ **render.yaml** - Infrastructure as Code configuration for Render
✅ **.env.example** - Template for required environment variables

## Prerequisites

1. **GitHub Repository**: Push your code to GitHub
2. **Render Account**: Sign up at https://render.com
3. **Email App Password**: Generate an app password if using Gmail

## Deployment Steps

### Option 1: Using render.yaml (Recommended)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push
   ```

2. **Create New Blueprint on Render**
   - Go to https://dashboard.render.com
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`

3. **Configure Environment Variables**
   - Render will prompt you to fill in email settings:
     - `EMAIL_HOST` (e.g., smtp.gmail.com)
     - `EMAIL_HOST_USER` (your email)
     - `EMAIL_HOST_PASSWORD` (your app password)
     - `DEFAULT_FROM_EMAIL` (your email)
   - Other variables (SECRET_KEY, DATABASE_URL) are auto-generated

4. **Deploy**
   - Click "Apply" to start deployment
   - Render will create PostgreSQL database and web service
   - Wait for build to complete (~5-10 minutes)

### Option 2: Manual Setup

1. **Create PostgreSQL Database**
   - Dashboard → New → PostgreSQL
   - Name: `ground-booking-db`
   - Select free tier
   - Click "Create Database"
   - Copy the "Internal Database URL"

2. **Create Web Service**
   - Dashboard → New → Web Service
   - Connect GitHub repository
   - Configuration:
     - **Name**: ground-booking-system
     - **Runtime**: Python 3
     - **Build Command**: `./build.sh`
     - **Start Command**: `gunicorn groundbooking.wsgi:application`

3. **Add Environment Variables**
   - Go to Environment tab
   - Add all variables from `.env.example`:
     ```
     SECRET_KEY=<generate-random-50-char-string>
     DEBUG=False
     DATABASE_URL=<paste-internal-database-url>
     EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
     EMAIL_HOST=smtp.gmail.com
     EMAIL_PORT=587
     EMAIL_USE_TLS=True
     EMAIL_HOST_USER=your-email@gmail.com
     EMAIL_HOST_PASSWORD=your-app-password
     DEFAULT_FROM_EMAIL=your-email@gmail.com
     ```

4. **Deploy**
   - Click "Create Web Service"
   - Render will start building and deploying

## After Deployment

1. **Check Logs**: Monitor deployment in Render dashboard logs
2. **Access Your Site**: Visit `https://your-app-name.onrender.com`
3. **Create Superuser** (if needed):
   - Go to Render dashboard → Shell
   - Run: `python manage.py createsuperuser`
4. **Test Functionality**: Test booking system and email notifications

## Troubleshooting

### Static Files Not Loading
- Check WhiteNoise is in MIDDLEWARE (settings.py)
- Verify STATIC_ROOT and STATICFILES_STORAGE are set
- Run `python manage.py collectstatic` locally to test

### Database Connection Errors
- Verify DATABASE_URL is correct in environment variables
- Ensure database is in same region as web service
- Check `ssl_require=True` in DATABASES config

### Email Not Sending
- Verify email credentials are correct
- For Gmail: Use app password, not regular password
- Check EMAIL_PORT and EMAIL_USE_TLS settings

### Build Fails
- Check build.sh has execute permissions: `chmod +x build.sh`
- Verify all dependencies are in requirements.txt
- Check Python version matches runtime.txt

## Free Tier Limitations

- **Database**: 1 GB storage, expires after 90 days
- **Web Service**: Spins down after 15 minutes of inactivity
- **Bandwidth**: 100 GB/month

## Upgrade to Paid Tier

For production use, consider upgrading:
- **Starter Database**: $7/month (no expiration)
- **Starter Web Service**: $7/month (always on)

## Support

- Render Docs: https://render.com/docs
- Django on Render: https://render.com/docs/deploy-django

---

**Note**: First deployment may take 10-15 minutes. Subsequent deployments are faster.
