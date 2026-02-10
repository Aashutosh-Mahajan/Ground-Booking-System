<div align="center">

# 🏟️ SportsDeck - Ground Booking System

### *A comprehensive web-based platform for managing college sports ground reservations*

[![Django](https://img.shields.io/badge/Django-5.2.4-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://www.postgresql.org/)

[Features](#-key-features) • [Installation](#-installation) • [Usage](#-usage) • [API](#-api-reference) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#️-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Models Documentation](#-models-documentation)
- [API Reference](#-api-reference)
- [Security Features](#-security-features)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Changelog](#-changelog)

---

## 🌟 Overview

**SportsDeck** is an enterprise-grade ground booking management system designed specifically for educational institutions. It streamlines the entire process of sports facility reservations, from initial booking requests to final approvals, while preventing scheduling conflicts through intelligent time-slot management.

### Purpose

This system addresses the common challenges faced by colleges in managing sports ground bookings:
- **Conflict Prevention**: Automated checking prevents double-bookings
- **Transparency**: Real-time status tracking for all stakeholders
- **Efficiency**: Digital workflow replaces manual booking processes
- **Accountability**: Complete audit trail of all booking activities
- **Fair Access**: First-Come-First-Served (FCFS) system ensures equitable allocation

### Target Users

- **Students**: Book grounds for sports activities, events, and practice sessions
- **Sports Coordinators**: Manage and approve booking requests
- **Administrative Staff**: Oversee facility utilization and generate reports

---

## ✨ Key Features

### 🎓 Student Features

- **User Authentication**
  - Secure registration with email verification (OTP-based)
  - Password reset functionality with OTP verification
  - Session-based authentication
  
- **Booking Management**
  - Request ground bookings with date, time slot, and purpose
  - Select sports type (Football, Basketball, Cricket, etc.)
  - Add player details (name, branch, year, division)
  - Request equipment if needed
  - Real-time availability checking
  
- **Dashboard & History**
  - View personal booking history
  - Filter bookings by status (Pending/Approved/Rejected)
  - Track booking status in real-time
  - View detailed booking information

### 🛠 Admin Features

- **Administrative Dashboard**
  - Comprehensive view of all booking requests
  - Approve or reject bookings with one click
  - View detailed booking information including player lists
  - Filter and search functionality
  
- **Ground Management**
  - View allotted grounds dashboard
  - Manage multiple sports facilities
  - Track ground utilization
  
- **Conflict Prevention**
  - Automatic detection of scheduling conflicts
  - Unique constraint enforcement for approved bookings
  - Time-slot validation system

### 🔒 Security Features

- **Password Security**: Hashed password storage using Django's built-in hashing
- **CSRF Protection**: Built-in CSRF token validation
- **Session Management**: Secure session-based authentication
- **Email Verification**: OTP-based verification for user registration
- **XSS Protection**: Template auto-escaping enabled
- **SQL Injection Prevention**: Django ORM with parameterized queries

### 📊 System Features

- **FCFS (First-Come-First-Served) Logic**: Automatic approval/rejection based on submission time
- **Email Notifications**: Automated emails for booking confirmations and OTP verification
- **Responsive Design**: Mobile-friendly interface
- **Data Integrity**: Database constraints prevent conflicting bookings
- **Audit Trail**: Complete tracking of booking creation and status changes

---

## 🏗 System Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer (Browser)                   │
│              HTML/CSS/JavaScript Frontend                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ HTTP/HTTPS
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   Web Server Layer                           │
│            Gunicorn (Production) / Django Dev Server         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Application Layer (Django)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              URL Router (urls.py)                    │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────────────┐   │
│  │            Views Layer (views.py)                    │   │
│  │  - Business Logic                                    │   │
│  │  - Request Processing                                │   │
│  │  - Response Rendering                                │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────────────┐   │
│  │         Models Layer (models.py)                     │   │
│  │  - Booking, Player, StudentUser                      │   │
│  │  - AdminUser, AllotedGroundBooking                   │   │
│  │  - OTPVerification                                   │   │
│  └────────────────────┬─────────────────────────────────┘   │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        │ Django ORM
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                Database Layer (PostgreSQL)                   │
│  - User Data                                                 │
│  - Booking Records                                           │
│  - Session Storage                                           │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

```
┌─────────────────┐       ┌──────────────────┐
│    Booking      │◄──────│     Player       │
├─────────────────┤       ├──────────────────┤
│ id (PK)         │       │ id (PK)          │
│ student_name    │       │ booking_id (FK)  │
│ student_email   │       │ name             │
│ ground          │       │ branch           │
│ sport           │       │ year             │
│ date            │       │ division         │
│ time_slot       │       └──────────────────┘
│ status          │
│ created_at      │
└─────────────────┘
        │
        │
        ▼
┌─────────────────────────┐
│ AllotedGroundBooking    │
├─────────────────────────┤
│ id (PK)                 │
│ booking_id (FK)         │
│ date                    │
│ ground                  │
│ time_slot               │
└─────────────────────────┘

┌──────────────────┐       ┌──────────────────┐
│  StudentUser     │       │   AdminUser      │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │       │ id (PK)          │
│ email (UNIQUE)   │       │ username (UNIQUE)│
│ full_name        │       │ password (HASH)  │
│ password (HASH)  │       └──────────────────┘
└──────────────────┘

┌──────────────────┐
│ OTPVerification  │
├──────────────────┤
│ id (PK)          │
│ email            │
│ otp              │
│ expires_at       │
│ is_verified      │
└──────────────────┘
```

---

## 🖥️ Tech Stack

### Backend
- **Django 5.2.4**: High-level Python web framework
- **Python 3.x**: Programming language
- **PostgreSQL**: Robust relational database
- **Gunicorn 23.0.0**: Python WSGI HTTP Server for production
- **WhiteNoise 6.8.2**: Static file serving for Django

### Frontend
- **HTML5**: Markup language
- **CSS3**: Styling and responsive design
- **JavaScript**: Client-side interactivity
- **Bootstrap** (via templates): UI components

### Additional Libraries
- **psycopg2-binary 2.9.10**: PostgreSQL adapter for Python
- **python-decouple 3.8**: Configuration management
- **dj-database-url 3.0.1**: Database URL parsing
- **Pillow 11.3.0**: Image processing library
- **django-deep-serializer 0.1.3**: Advanced serialization

### Development Tools
- **virtualenv**: Python environment isolation
- **pip**: Package management

---

## 📦 Prerequisites

Before installing SportsDeck, ensure you have the following installed:

### Required Software

1. **Python 3.8+**
   ```bash
   python --version  # Should output Python 3.8 or higher
   ```

2. **PostgreSQL 12+**
   - Download from: https://www.postgresql.org/download/
   - Verify installation:
     ```bash
     psql --version
     ```

3. **pip** (Python package manager)
   ```bash
   pip --version
   ```

4. **Git** (for cloning repository)
   ```bash
   git --version
   ```

### System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: At least 500MB free space
- **Network**: Internet connection for package installation

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/ground-booking-system.git

# Navigate to project directory
cd ground-booking-system
```

### Step 2: Create Virtual Environment

**For Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**For Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal after activation.

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt
```

**Note for Windows Users**: If you encounter issues with `psycopg2-binary`, install PostgreSQL development tools or use:
```bash
pip install psycopg2-binary --only-binary :all:
```

### Step 4: Environment Configuration

Create a `.env` file in the project root directory:

```bash
# Copy the example environment file
cp .env.example .env  # Linux/macOS
copy .env.example .env  # Windows
```

If `.env.example` doesn't exist, create `.env` manually with the following content:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/ground_booking_db

# Email Configuration (for OTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security (for production)
CSRF_TRUSTED_ORIGINS=https://yourdomain.com
```

**Generating SECRET_KEY:**
```python
# Run in Python shell
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

---

## ⚙️ Configuration

### Database Configuration

#### PostgreSQL Setup

1. **Create Database**:
   ```sql
   -- Login to PostgreSQL
   psql -U postgres
   
   -- Create database
   CREATE DATABASE ground_booking_db;
   
   -- Create user (optional)
   CREATE USER booking_admin WITH PASSWORD 'your_password';
   
   -- Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE ground_booking_db TO booking_admin;
   
   -- Exit
   \q
   ```

2. **Update .env file** with your database credentials:
   ```env
   DATABASE_URL=postgresql://booking_admin:your_password@localhost:5432/ground_booking_db
   ```

### Email Configuration

For OTP verification, configure email settings:

1. **Gmail Setup** (recommended for development):
   - Enable 2-Factor Authentication on your Gmail account
   - Generate App Password: https://myaccount.google.com/apppasswords
   - Add to `.env`:
     ```env
     EMAIL_HOST_USER=your-email@gmail.com
     EMAIL_HOST_PASSWORD=your-16-character-app-password
     ```

2. **Other Email Providers**:
   Update `EMAIL_HOST` and `EMAIL_PORT` in `.env` accordingly.

### Static Files Configuration

Static files are automatically configured using WhiteNoise. For production:

```python
# In settings.py (already configured)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
```

---

##  Usage

### Starting the Development Server

```bash
# Start Django development server
python manage.py runserver

# Or specify port
python manage.py runserver 8000
```

Access the application at: **http://localhost:8000**

### Running with Task

Alternatively, use the configured VS Code task:
```bash
# From VS Code Command Palette (Ctrl+Shift+P)
Tasks: Run Task → Run Django dev server
```

### Application URLs

| Feature | URL | Description |
|---------|-----|-------------|
| Home | `/` | Landing page |
| Student Login | `/student/login/` | Student authentication |
| Student Signup | `/student/signup/` | New student registration |
| Student Dashboard | `/student/dashboard/` | Student main dashboard |
| Student Booking | `/student/booking/` | Create new booking |
| Booking History | `/student/history/` | View booking history |
| Admin Login | `/custom-admin/login/` | Admin authentication |
| Admin Dashboard | `/custom-admin/dashboard/` | Admin management panel |
| Rules & Regulations | `/student/rules/` | Booking guidelines |

### User Workflows

#### Student Workflow

1. **Registration**:
   - Navigate to `/student/signup/`
   - Fill in registration form
   - Verify email with OTP
   - Account created

2. **Login**:
   - Go to `/student/login/`
   - Enter email and password
   - Access student dashboard

3. **Book a Ground**:
   - Navigate to "Book Ground"
   - Select sport, date, time slot, and ground
   - Add player details
   - Submit booking request
   - Receive confirmation email

4. **Track Booking**:
   - Go to "Booking History"
   - View status: Pending/Approved/Rejected
   - Filter by status

#### Admin Workflow

1. **Login**:
   - Navigate to `/custom-admin/login/`
   - Enter admin credentials
   - Access admin dashboard

2. **Review Bookings**:
   - View all pending requests
   - Click on booking to see details
   - View player list and equipment requests

3. **Approve/Reject**:
   - Click "Approve" to confirm booking
   - Click "Reject" to decline request
   - System sends notification to student

4. **View Allotted Grounds**:
   - Switch to "Allotted Grounds" tab
   - See all approved bookings
   - Track ground utilization

---

## 📁 Project Structure

```
Ground-Booking-System/
│
├── booking/                      # Main application
│   ├── __init__.py
│   ├── admin.py                  # Django admin configuration
│   ├── apps.py                   # App configuration
│   ├── forms.py                  # Form definitions
│   ├── models.py                 # Database models
│   ├── views.py                  # View functions
│   ├── urls.py                   # URL routing
│   │
│   ├── management/               # Custom management commands
│   │   └── commands/
│   │
│   ├── migrations/               # Database migrations
│   │   ├── 0001_initial.py
│   │   ├── 0002_alter_booking_roll_number.py
│   │   └── ...
│   │
│   ├── static/                   # Static files
│   │   ├── css/                  # Stylesheets
│   │   └── images/               # Images
│   │
│   └── templates/                # HTML templates
│       ├── base.html             # Base template
│       └── booking/              # App-specific templates
│           ├── home.html
│           ├── student_login.html
│           ├── student_dashboard.html
│           ├── admin_dashboard.html
│           └── ...
│
├── groundbooking/                # Project configuration
│   ├── __init__.py
│   ├── settings.py               # Project settings
│   ├── urls.py                   # Root URL configuration
│   ├── wsgi.py                   # WSGI configuration
│   └── asgi.py                   # ASGI configuration
│
├── staticfiles/                  # Collected static files (production)
│
├── docs/                         # Documentation
│   └── TECHNICAL_OVERVIEW.md
│
├── manage.py                     # Django management script
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── runtime.txt                   # Python version for deployment
├── Procfile                      # Deployment configuration
├── render.yaml                   # Render deployment config
├── build.sh                      # Build script
├── .env                          # Environment variables (not in git)
├── .gitignore                    # Git ignore file
└── README.md                     # This file
```

---

## 📊 Models Documentation

### Booking Model

Represents a ground booking request.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `student_name` | CharField(100) | Name of student making booking |
| `student_email` | EmailField | Student email address |
| `student_branch` | CharField(50) | Student's branch (CSE, IT, etc.) |
| `student_year` | CharField(20) | Academic year (FE, SE, TE, BE) |
| `student_division` | CharField(10) | Division (A, B, C) |
| `roll_number` | CharField(20) | Student roll number |
| `ground` | CharField(100) | Ground name |
| `sport` | CharField(50) | Sport type |
| `date` | DateField | Booking date |
| `time_slot` | CharField(50) | Time slot |
| `purpose` | TextField | Purpose of booking |
| `equipment` | TextField | Required equipment |
| `number_of_players` | PositiveIntegerField | Number of players |
| `status` | CharField(20) | Status (Pending/Approved/Rejected) |
| `created_at` | DateTimeField | Timestamp of creation |

**Constraints:**
- Unique constraint on (date, sport, time_slot) for Approved bookings
- Prevents double-booking of same slot

**Indexes:**
- `idx_sport_date_slot_status`: Speeds up FCFS lookups
- `idx_created_at`: Optimizes time-based queries

### Player Model

Stores player information for each booking.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `booking` | ForeignKey | Reference to Booking |
| `name` | CharField(100) | Player name |
| `branch` | CharField(50) | Player branch |
| `year` | CharField(10) | Academic year |
| `division` | CharField(10) | Division |

**Relationships:**
- Many-to-One with Booking (multiple players per booking)

### StudentUser Model

User authentication and profile for students.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `full_name` | CharField(100) | Full name |
| `email` | EmailField (UNIQUE) | Email address |
| `roll_number` | CharField(20) | Roll number |
| `branch` | CharField(50) | Branch |
| `year` | CharField(20) | Academic year |
| `division` | CharField(10) | Division |
| `password` | CharField(255) | Hashed password |

### AdminUser Model

Admin authentication.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `username` | CharField(100) (UNIQUE) | Admin username |
| `password` | CharField(255) | Hashed password |

### AllotedGroundBooking Model

Tracks approved bookings.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `booking` | ForeignKey | Reference to original Booking |
| `date` | DateField | Booking date |
| `ground` | CharField(100) | Ground name |
| `time_slot` | CharField(50) | Time slot |
| `allotted_to` | CharField(100) | Student name |
| `roll_number` | CharField(20) | Roll number |
| `purpose` | TextField | Purpose |
| `players` | PositiveIntegerField | Number of players |

### OTPVerification Model

Manages OTP verification for email validation.

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer (PK) | Primary key |
| `email` | EmailField | Email address |
| `otp` | CharField(6) | 6-digit OTP |
| `created_at` | DateTimeField | Creation timestamp |
| `expires_at` | DateTimeField | Expiration timestamp |
| `is_verified` | BooleanField | Verification status |
| `full_name` | CharField(100) | Temporary storage |
| `roll_number` | CharField(20) | Temporary storage |
| `branch` | CharField(50) | Temporary storage |
| `year` | CharField(20) | Temporary storage |
| `division` | CharField(10) | Temporary storage |
| `password` | CharField(255) | Temporary storage |

**Methods:**
- `is_expired()`: Check if OTP has expired
- `generate_otp()`: Generate random 6-digit OTP

---

## 🔌 API Reference

### Check Availability Endpoint

**Endpoint:** `/check-availability/`  
**Method:** `GET`  
**Description:** Check if a time slot is available for booking

**Parameters:**
```javascript
{
    "sport": "Football",
    "date": "2026-02-15",
    "time_slot": "10:00 AM - 11:00 AM"
}
```

**Response:**
```json
{
    "available": true,
    "message": "Slot is available"
}
```

### Get Players Endpoint

**Endpoint:** `/get-players/<booking_id>/`  
**Method:** `GET`  
**Description:** Retrieve player list for a booking

**Response:**
```json
{
    "players": [
        {
            "name": "John Doe",
            "branch": "CSE",
            "year": "SE",
            "division": "A"
        }
    ]
}
```

### Get Equipment Endpoint

**Endpoint:** `/get-equipment/<booking_id>/`  
**Method:** `GET`  
**Description:** Retrieve equipment details for a booking

**Response:**
```json
{
    "equipment": "2 Footballs, 1 Net, Cones"
}
```

---

## 🔒 Security Features

### Authentication & Authorization

- **Password Hashing**: Uses Django's PBKDF2 algorithm with SHA256
- **Session Management**: Secure session cookies with HTTPONLY flag
- **CSRF Protection**: Token-based CSRF protection on all POST requests
- **OTP Verification**: Time-limited OTP for email verification

### Data Protection

- **SQL Injection**: Protected via Django ORM
- **XSS Prevention**: Template auto-escaping enabled
- **Sensitive Data**: Passwords never stored in plain text
- **Email Masking**: Email addresses partially masked in UI

### Production Security Checklist

```python
# In production .env:
DEBUG=False
SECRET_KEY=strong-random-secret-key
ALLOWED_HOSTS=yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# Additional settings.py configurations:
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

---

## 🚢 Deployment

### Deployment on Render

1. **Create Render Account**: Sign up at https://render.com

2. **Create PostgreSQL Database**:
   - Create new PostgreSQL instance
   - Copy internal database URL

3. **Create Web Service**:
   - Connect GitHub repository
   - Select branch
   - Configure:
     ```
     Build Command: ./build.sh
     Start Command: gunicorn groundbooking.wsgi:application
     ```

4. **Environment Variables**:
   ```
   SECRET_KEY=your-secret-key
   DEBUG=False
   DATABASE_URL=your-postgres-url
   ALLOWED_HOSTS=.onrender.com
   ```

5. **Deploy**: Click "Create Web Service"

### Deployment Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set strong `SECRET_KEY`
- [ ] Configure database URL
- [ ] Set up email service
- [ ] Collect static files
- [ ] Run migrations
- [ ] Create admin users
- [ ] Test all endpoints
- [ ] Configure HTTPS
- [ ] Set up monitoring

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test booking

# Run with verbosity
python manage.py test --verbosity=2

# Run specific test class
python manage.py test booking.tests.BookingModelTest
```

### Manual Testing Checklist

#### Student Features
- [ ] Student registration with OTP
- [ ] Student login/logout
- [ ] Password reset functionality
- [ ] Create booking request
- [ ] View booking history
- [ ] Filter bookings by status
- [ ] Check availability before booking

#### Admin Features
- [ ] Admin login/logout
- [ ] View all pending bookings
- [ ] Approve booking
- [ ] Reject booking
- [ ] View player details
- [ ] View allotted grounds

#### System Features
- [ ] Prevent double-booking
- [ ] FCFS logic working
- [ ] Email notifications sent
- [ ] OTP expiration working
- [ ] Session management
- [ ] CSRF protection

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: `ModuleNotFoundError: No module named 'booking'`
**Solution:**
```bash
# Ensure you're in the correct directory
cd Ground-Booking-System

# Verify manage.py exists
ls manage.py  # Linux/macOS
dir manage.py  # Windows
```

#### Issue: `psycopg2` installation fails on Windows
**Solution:**
```bash
# Option 1: Use binary wheel
pip install psycopg2-binary --only-binary :all:

# Option 2: Install PostgreSQL development tools
# Download from: https://www.postgresql.org/download/windows/
```

#### Issue: Database connection error
**Solution:**
```bash
# Check PostgreSQL is running
sudo service postgresql status  # Linux
brew services list  # macOS
# Check Services app on Windows

# Verify database exists
psql -U postgres -l

# Test connection
psql -U your_username -d ground_booking_db
```

#### Issue: `SECRET_KEY` not found
**Solution:**
```bash
# Ensure .env file exists
cat .env  # Linux/macOS
type .env  # Windows

# Verify SECRET_KEY is set
python -c "from decouple import config; print(config('SECRET_KEY'))"
```

#### Issue: Static files not loading
**Solution:**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Verify STATIC_ROOT in settings.py
python manage.py findstatic css/styles.css
```

#### Issue: Email not sending
**Solution:**
- Verify Gmail app password is correct
- Enable "Less secure app access" (if not using app password)
- Check `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env`
- Test email configuration:
  ```python
  from django.core.mail import send_mail
  send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
  ```

#### Issue: Migrations conflict
**Solution:**
```bash
# Reset migrations (CAUTION: Development only)
python manage.py migrate booking zero
python manage.py migrate

# Or delete migration files and recreate
rm booking/migrations/00*.py  # Keep __init__.py
python manage.py makemigrations
python manage.py migrate
```

### Getting Help

If you encounter issues not listed here:

1. **Check Django logs**: Look for error messages in terminal
2. **Enable DEBUG mode**: Set `DEBUG=True` in `.env` (development only)
3. **Check browser console**: Press F12 for JavaScript errors
4. **Review documentation**: Refer to Django docs at https://docs.djangoproject.com/
5. **Open an issue**: Create issue on GitHub repository

---

## 🤝 Contributing

We welcome contributions to SportsDeck! Here's how you can help:

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/ground-booking-system.git
   ```
3. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. Make your changes
5. Run tests:
   ```bash
   python manage.py test
   ```
6. Commit your changes:
   ```bash
   git commit -m "Add: Brief description of changes"
   ```
7. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
8. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide for Python code
- Write descriptive commit messages
- Add comments for complex logic
- Update documentation for new features
- Write tests for new functionality
- Ensure all tests pass before submitting PR

### Commit Message Format

```
Type: Brief description

Detailed description (optional)

Fixes #issue_number (if applicable)
```

**Types:**
- `Add`: New feature
- `Fix`: Bug fix
- `Update`: Changes to existing functionality
- `Refactor`: Code restructuring
- `Docs`: Documentation changes
- `Test`: Adding or updating tests
- `Style`: Code style changes

### Pull Request Guidelines

- Provide clear description of changes
- Reference related issues
- Include screenshots for UI changes
- Ensure CI/CD checks pass
- Request review from maintainers

---

## 📝 Changelog

### Version 1.0.0 (Current)

**Features:**
- Student registration with OTP verification
- Student login/logout system
- Ground booking request system
- Admin approval/rejection workflow
- Booking history tracking
- Real-time availability checking
- Email notifications
- FCFS (First-Come-First-Served) logic
- Password reset functionality
- Responsive design

**Database:**
- PostgreSQL integration
- Optimized indexes for performance
- Unique constraints for data integrity

**Security:**
- CSRF protection
- XSS prevention
- SQL injection prevention
- Password hashing
- Session management

---

<div align="center">

**Made with ❤️ by the SportsDeck Team**

[⬆ Back to Top](#-sportsdeck---ground-booking-system)

</div>
