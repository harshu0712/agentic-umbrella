# Agentic Umbrella Platform – Backend

## 📌 Project Overview

This project is a backend system for managing contractors, agencies, and umbrella companies.
It supports user management, work tracking, compliance, and audit logging.

---

## 🧱 Tech Stack

* Backend: Django (Python)
* Database: PostgreSQL
* API: Django REST Framework
* Admin Panel: Django Admin

---

## ⚙️ Current Implementation Status

### ✅ Completed

* Backend APIs implemented
* PostgreSQL database integrated
* Custom User Model (core.User)
* Organisation, Membership, Work Record modules
* Audit logging system
* Admin panel for full data management

### 🔄 Pending / To Be Integrated

* Frontend integration
* Advanced business logic (if any remaining)
* Deployment setup

---

## 🗄️ Database Setup (PostgreSQL)

1. Install PostgreSQL

2. Create database:

   ```
   umbrella_db
   ```

3. Update credentials in:

   ```
   backend/config/settings.py
   ```

Example:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'umbrella_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## 🚀 Backend Setup Instructions

### 1. Clone Repository

```
git clone <repo-link>
cd agentic-umbrella/backend
```

### 2. Create Virtual Environment

```
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

### 4. Apply Migrations

```
python manage.py migrate
```

### 5. Run Server

```
python manage.py runserver
```

---

## 🌐 API Access

Base URL:

```
http://127.0.0.1:8000/
```

Available Endpoints:

* `/admin/` → Admin Panel
* `/api/health/` → Health Check
* `/api/v1/auth/` → Authentication
* `/api/v1/audit/` → Audit Logs
* `/api/v1/notifications/`
* `/api/v1/compliance/`

---

## 🔐 Admin Access

Create admin user:

```
python manage.py createsuperuser
```

Login:

```
http://127.0.0.1:8000/admin/
```

---

## 🔗 System Architecture (Concept)

* Contractor (User)
* Agency (Organisation)
* Umbrella (Organisation)
* Membership → links user & organisation
* Work Records → track hours & payments
* Audit Logs → track system activity

---

## 🔄 Integration Notes (For Further Development)

* Frontend can consume APIs via REST endpoints
* Authentication uses token-based system
* Database is fully structured and ready
* Ensure `.env` or credentials are configured properly

---

## 📌 Important Notes

* Do not upload `venv/`
* Ensure PostgreSQL is running before starting backend
* Migrations must be applied before running server

---

## 👨‍💻 Author Notes

Backend is fully functional and tested with PostgreSQL.
Ready for frontend integration and further enhancements.
