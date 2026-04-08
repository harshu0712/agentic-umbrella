# 🚀 Agentic Umbrella Platform

A full-stack web application designed to manage **compliance, audit tracking, user management, and system monitoring** through a centralized dashboard.

---

## 📌 Overview

The **Agentic Umbrella Platform** is built to simulate enterprise-level workflows involving:

* Compliance validation
* Audit tracking
* Exception handling
* User activity monitoring

It provides a **modern dashboard UI** powered by React and a **robust backend API** using Django REST Framework.

---

## ✨ Features

### 📊 Dashboard

* Displays key metrics like:

  * Audit events
  * Active exceptions
  * Compliance pass rate
  * Pending RTI submissions

### 👥 Users Module

* View all users from backend
* Integrated with custom Django user model

### ✅ Compliance System

* Track compliance checks
* Calculate pass/fail rates

### ⚠️ Exception Handling

* Monitor blocking issues
* Track severity levels

### 🔔 Notifications

* Event-based notification system (backend ready)

### 🔐 Authentication

* JWT-based login system
* Access & refresh tokens

---

## 🛠️ Tech Stack

### Frontend

* ⚛️ React (Vite)
* 🎨 Tailwind CSS
* 🔗 Axios (API calls)

### Backend

* 🐍 Django
* 🔧 Django REST Framework
* 🔐 Simple JWT Authentication
* 🗄️ SQLite / PostgreSQL

---

## 📂 Project Structure

```
agentic-umbrella/
│
├── backend/
│   ├── compliance/
│   ├── audit/
│   ├── notifications/
│   ├── exceptions_handler/
│   ├── core/
│   └── config/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── Sidebar.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Users.jsx
│   │   └── services/
│   │       └── api.js
│
└── README.md
```

---

## ⚙️ Setup Instructions

### 🔽 1. Clone Repository

```bash
git clone https://github.com/harshu0712/agentic-umbrella.git
cd agentic-umbrella
```

---

### 🐍 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows

pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate

python manage.py runserver
```

Backend will run at:

```
http://127.0.0.1:8000
```

---

### ⚛️ 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will run at:

```
http://localhost:4000
```

---

## 🔗 API Endpoints

| Feature     | Endpoint              |
| ----------- | --------------------- |
| Dashboard   | `/api/dashboard/`     |
| Users       | `/api/users/`         |
| Login       | `/api/token/`         |
| Refresh JWT | `/api/token/refresh/` |

---

## 🔐 Authentication Flow

* User logs in → receives access + refresh tokens
* Access token used for API calls
* Refresh token generates new access token

---

## 🧠 Key Learnings

* Full-stack integration (React + Django)
* API handling with Axios
* JWT authentication implementation
* State management using React hooks
* UI design using Tailwind CSS

---

## 🚀 Future Enhancements

* 📈 Charts & analytics dashboard
* ✏️ Edit / Delete users
* 🔍 Search & filtering
* 📡 Real-time updates (WebSockets)
* 📊 Advanced reporting

---

## 👨‍💻 Author

**Harshith R S**

---

## 📢 Notes

This project demonstrates a **complete full-stack workflow**, including:

* Backend API design
* Frontend integration
* Authentication system
* Clean UI design

Suitable for:

* Internship projects
* Academic submissions
* Portfolio showcase
