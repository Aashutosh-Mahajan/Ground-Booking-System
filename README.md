# 🏟️ Ground Booking System

A web-based platform for managing and streamlining **college ground reservations**, built using **Django**, **HTML**, **CSS**, and **PostgreSQL**.

---

## ✨ Features

- **🎓 Student Portal** – Request ground bookings with date, time, and purpose.
- **🛠 Admin Panel** – Approve or reject booking requests.
- **📋 Allotted Grounds Dashboard** – View all confirmed bookings in one place.
- **⏱ Timetable Check System** – Prevents scheduling conflicts by verifying availability.
- **📱 User-Friendly Interface** – Simple and responsive design.

---

## 🖥️ Tech Stack

- **Backend:** Django
- **Frontend:** HTML, CSS
- **Database:** PostgreSQL

---

## 🚀 How It Works

1. **Students** submit a booking request.
2. **Admin** reviews the request and either approves or rejects it.
3. Approved bookings appear on the **Allotted Grounds Dashboard**.
4. **Timetable Check System** ensures no overlapping reservations.

---

## ⚙️ Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ground-booking-system.git
   cd ground-booking-system
   
2.Create & activate a virtual environment:
python -m venv venv
source venv/bin/activate  # For Linux/Mac
venv\Scripts\activate     # For Windows

3.Install dependencies:
pip install -r requirements.txt

4.Configure PostgreSQL in settings.py.

5.Run migrations:
python manage.py migrate

6.Start the development server:
python manage.py runserver
