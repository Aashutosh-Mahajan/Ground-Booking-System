# Ground Booking System — Technical Overview

This document provides a comprehensive, implementation-level overview of the Ground Booking System (aka "SportDeck") built with Django. It is intended for architects, engineers, and reviewers preparing an overview paper or evaluating the system’s design, data model, workflows, and deployment.

---

## 1. Executive Summary

- Purpose: Digitize and streamline college ground reservations with approval workflows, conflict prevention, and transparent allocations.
- Core actors:
  - Students: request bookings, track status, and view history.
  - Admins: review, approve/reject requests, and manage allotted grounds.
- Key features:
  - First-Come-First-Serve (FCFS) approval with automatic conflict resolution.
  - Availability check and slot overlap detection by date/sport/time.
  - Email notifications on approval/rejection.
  - Allotments view with filters and pagination.

---

## 2. High-level Architecture

- Framework: Django 5.x monolith
- App structure: single domain app `booking` inside project `groundbooking`.
- Persistence: PostgreSQL (via `DATABASE_URL`) using `dj-database-url`.
- Static assets: collected and served by WhiteNoise in production.
- Email: SMTP (configurable via environment variables) using Django’s `send_mail`.
- Deployment: Render.com with Gunicorn; build step runs migrations and collectstatic.
- Configuration: Twelve-Factor style via `python-decouple` and environment variables.

### 2.1 Component Diagram (Mermaid)

```mermaid
flowchart LR
  subgraph Client
    A[Student Web UI]
    B[Admin Web UI]
  end

  A -->|HTTP/HTML| C[Django Views]
  B -->|HTTP/HTML| C
  C -->|ORM| D[(PostgreSQL)]
  C -->|Static| E[WhiteNoise]
  C -->|SMTP| F[Email Server]
```

---

## 3. Repository Layout

- `booking/` domain app
  - `models.py` entities: Booking, Player, StudentUser, AdminUser, AllotedGroundBooking
  - `views.py` MVC controllers for student/admin flows, FCFS approval, availability, AJAX
  - `forms.py` typed forms and widgets for booking/player capture
  - `templates/booking/*.html` pages and email template
  - `urls.py` app-level routes
- `groundbooking/` project
  - `settings.py` configuration (DB, static, email, apps)
  - `urls.py` project-level URL inclusion
  - `wsgi.py/asgi.py` entry points
- Ops & config
  - `requirements.txt`, `build.sh`, `Procfile`, `render.yaml`, `runtime.txt`

---

## 4. Data Model

### 4.1 Entities and Relationships

- Booking
  - Captures booking request and metadata (organizer details, slot, sport, equipment, purpose, status).
  - One-to-many: Booking 1..* Player
  - One-to-zero-or-one: Booking 0..1 AllotedGroundBooking (reflected on approval)
- Player
  - Member of a booking; fields for name, branch, year, division.
- StudentUser
  - Directory of students used to auto-fill player metadata when added by email.
- AdminUser
  - Custom admin login entries (note: current implementation stores plaintext passwords; see security section).
- AllotedGroundBooking
  - Denormalized view of approved bookings for quick display; linked to the Booking when available.

### 4.2 Constraints and Indexes

- FCFS and conflict prevention
  - Unique approved slot constraint: only one Approved booking for (date, sport, time_slot)
    - `UniqueConstraint(fields=["date", "sport", "time_slot"], condition=Q(status="Approved"), name="uniq_approved_sport_slot")`
  - Indexes accelerate queueing and auditing:
    - `idx_sport_date_slot_status` on `(date, sport, time_slot, status)`
    - `idx_created_at` on `(created_at)`

### 4.3 Model Diagram (Mermaid)

```mermaid
classDiagram
  class Booking {
    +id: BigAutoField
    +student_name: Char(100)
    +student_email: Email
    +student_branch: Char(50)?
    +student_year: Char(20)?
    +student_division: Char(10)?
    +roll_number: Char(20)?
    +ground: Char(100)
    +sport: Char(50)?
    +date: Date
    +time_slot: Char(50)
    +purpose: Text
    +equipment: Text?
    +number_of_players: PositiveInt
    +status: Enum(Pending, Approved, Rejected)
    +created_at: DateTime(auto_add)
  }

  class Player {
    +id
    +name: Char(100)
    +branch: Enum
    +year: Enum
    +division: Enum
    +booking_id: FK -> Booking
  }

  class StudentUser {
    +id
    +full_name: Char(100)?
    +email: Email unique
    +roll_number: Char(20)?
    +branch: Char(50)?
    +year: Char(20)?
    +division: Char(10)?
    +password: Char(255)?
  }

  class AdminUser {
    +id
    +username: Char(100) unique
    +password: Char(255)
  }

  class AllotedGroundBooking {
    +id
    +booking_id: FK -> Booking (nullable)
    +date: Date
    +ground: Char(100)
    +time_slot: Char(50)
    +allotted_to: Char(100)
    +roll_number: Char(20)
    +purpose: Text?
    +players: PositiveInt
  }

  Booking "1" --> "*" Player
  Booking "0..1" <-- "*" AllotedGroundBooking
```

---

## 5. Application Flows

### 5.1 Student Booking Flow

1. Student navigates to booking page and selects date, ground, sport, and time slot (UI provides hidden inputs and summary).
2. Student fills organizer details and selects number of players; optional equipment is auto-filled based on sport.
3. Student searches and adds players via AJAX lookups against `StudentUser` by name; form posts player emails as hidden inputs.
4. Server-side rules in `views.student_booking`:
   - 24-hour rule: Organizer and selected players cannot have an Approved booking in the last 24 hours.
   - Player auto-enrichment: If a provided email matches `StudentUser`, creates a `Player` with branch/year/division; otherwise, captures name only.
   - Guarantees at least one player (organizer) is attached.
5. Request saved as `Booking(status="Pending")`; success view shown.

### 5.2 Admin Approval (FCFS)

- Admin dashboard lists Pending bookings ordered by oldest first (FCFS queue) with filters and pagination for allotted records.
- Approve action (`views.approve_booking`) within a DB transaction:
  1. Lock all bookings for the same (date, sport, time_slot) using `select_for_update`.
  2. Approve the oldest Pending; auto-reject all other Pending requests for that exact slot.
  3. Upsert an `AllotedGroundBooking` snapshot with organizer and player count.
  4. Send an approval email to the winner; send rejection emails to conflicts (best-effort).
- Reject action (`views.reject_booking`): Sets status and sends rejection email.

### 5.3 Availability Check (AJAX)

- Endpoint: `/check-availability/` computes availability for a fixed set of time ranges (currently 07:00–09:00 and 16:00–18:00).
- Considers Approved bookings for the same date and sport; marks overlapping ranges as "booked".
- Uses tolerant time parsing to handle a few input formats.

### 5.4 Email Notifications

- Template: `templates/booking/emails/booking_status_email.html` with a styled summary and player table.
- Sends from `DEFAULT_FROM_EMAIL`; approval emails are mandatory (exceptions bubble to UI with warnings), rejections are best-effort.

### 5.5 Student History and Dashboard

- Student session is keyed by `student_email`; dashboard greets the student; history view paginates and allows filtering by status.

---

## 6. URLs and Endpoints

- Public
  - `/` → Home
  - `/student/login/`, `/student/logout/`, `/student/dashboard/`, `/student/history/`
  - `/student/booking/` → Booking form (posts booking)
  - `/student/rules/` → Rules & regulations
  - `/check-availability/` → AJAX JSON for time slots
  - `/fetch-student-data/` → AJAX JSON: top 10 matching students by name
- Admin (custom)
  - `/custom-admin/login/`, `/custom-admin/logout/`
  - `/custom-admin/dashboard/` → Pending queue + Allotted view
  - `/approve-booking/<id>/`, `/reject-booking/<id>/`
  - View helpers: `/get-players/<booking_id>/`, `/get-equipment/<booking_id>/`, `/get-allotment-players/<allot_id>/`, `/get-allotment-equipment/<allot_id>/`
- Django Admin: `/admin/`

---

## 7. Configuration, Environments, and Secrets

- Environment variables (see `groundbooking/settings.py` and `render.yaml`):
  - `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
  - `DATABASE_URL` (PostgreSQL connection string)
  - Email: `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`
- Static files:
  - `STATIC_ROOT=staticfiles/` (collected by `build.sh`)
  - WhiteNoise `CompressedStaticFilesStorage` for efficient serving
- Runtime:
  - `runtime.txt`: Python 3.13
  - `Procfile`: `web: gunicorn groundbooking.wsgi:application`
  - `build.sh`: pip install, collectstatic, migrate

### 7.1 Local Development (Windows-friendly)

- Create a virtual environment and install requirements.
- Provide a `.env` file or environment variables for local settings including a PostgreSQL `DATABASE_URL`.
- Note for Windows: `psycopg2-binary` is intentionally skipped by marker; install PostgreSQL client dev tools and use `psycopg2` or access a remote Postgres.

Example `.env` keys:

```
SECRET_KEY=dev-secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://user:pass@localhost:5432/groundbooking
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@sportdeck.local
```

---

## 8. Security Considerations

- Authentication
  - Student and custom admin sessions are maintained via Django session storage.
  - Current `StudentUser` and `AdminUser` models store passwords in plaintext; this is NOT recommended for production.
    - Recommended improvements: use Django’s built-in `User` model or hash passwords with `make_password`/`check_password`.
- CSRF and hosts
  - CSRF trusted origins configured for `*.onrender.com`.
  - `ALLOWED_HOSTS` is env-configured for Render + localhost.
- Email: Avoid leaking sensitive context in emails; current template shares booking metadata only.

---

## 9. Performance and Scalability

- Query efficiency
  - Indexes on `(date, sport, time_slot, status)` and `(created_at)` support FCFS queueing and slot lookups.
  - `select_for_update` ensures serialization for conflicting approvals.
- Pagination
  - Allotted grounds list is paginated to reduce payload and render time.
- Static serving
  - WhiteNoise serves compressed assets directly from app dyno.

---

## 10. Error Handling and Observability

- Email sending errors surface as UI warnings but do not roll back approvals/rejections.
- Availability endpoint returns "freeze" for invalid/missing inputs to signal UI to disable actions.
- Logging: basic `print` statements are used in AJAX lookup; consider replacing with structured logging.

---

## 11. Testing Strategy (Recommended)

- Unit tests for:
  - FCFS approval path including exclusivity constraint and conflict auto-rejects.
  - 24-hour rule for organizers and added players.
  - Availability overlaps for multiple formats.
- Integration tests for:
  - Booking form POST with dynamic players and equipment mapping.
  - Email sending using Django’s `locmem` backend.

---

## 12. Known Limitations and Roadmap

- Credentials: migrate to Django auth for both students and admins; hash all passwords.
- Time slots: currently hardcoded ranges and string parsing; consider normalized time tables and proper validation.
- Equipment: sport-to-equipment mapping is client-side; move to server-side config.
- Data integrity: relate `StudentUser` to `Booking` via FK (organizer) for stronger referential consistency.
- Admin UX: add search, bulk actions, and filters for player attributes; export CSV.
- Observability: add logging, metrics, error tracking (Sentry) and health endpoints.

---

## 13. Deployment and Operations

- Platform: Render.com
- Build: `build.sh` runs install, collectstatic, and migrate
- Start: Gunicorn WSGI entry
- Database: Managed Postgres provisioned via `render.yaml` with automatic `DATABASE_URL` binding
- Static: Served by WhiteNoise; ensure `collectstatic` succeeds on deploy

---

## 14. Appendix: Approval Sequence (Mermaid)

```mermaid
sequenceDiagram
  participant A as Admin
  participant V as Django View (approve_booking)
  participant DB as PostgreSQL
  participant E as Email Server

  A->>V: Approve booking (id)
  V->>DB: select_for_update(date,sport,time_slot)
  V->>DB: Approve oldest Pending
  V->>DB: Bulk update others -> Rejected
  V->>DB: Upsert AllotedGroundBooking
  V->>E: Send Approval Email
  V->>E: Send Rejection Emails (others)
  V-->>A: Redirect with success/warnings
```

---

Document version: 1.0 (generated on 2025-10-25)
