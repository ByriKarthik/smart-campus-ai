# 🎓 Smart Campus AI  
### Intelligent University Management System (UMS)

Smart Campus AI is a full-stack Django-based University Management System designed to simulate and optimize real campus operations including academic scheduling, AI-driven attendance tracking, resource analytics, remedial management, and intelligent canteen load optimization.

This project integrates role-based dashboards, timetable automation, real-time monitoring, and data simulation to create a realistic smart campus environment.

---

## 🚀 Features

### 🔐 Role-Based Authentication
- Admin Dashboard
- Faculty Dashboard
- Student Dashboard
- Session-based login system

---

## 📅 Academic Timetable Engine
- Weekly schedule generation
- Section-based timetable
- Faculty-based timetable
- “Today’s Classes” intelligent dashboard panel
- Schedule-driven attendance marking

---

## 🧠 Smart Attendance System
- AI-assisted face-based attendance
- Manual override
- Schedule-aware attendance restriction
- Duplicate session protection
- Confidence scoring
- Parent email notification for absenteeism
- Attendance percentage tracking
- Planner insights (classes required to maintain 75%)

---

## 🏫 Resource & Operations Monitoring (Admin)

### 📊 Attendance Monitoring
- Students below attendance threshold
- Faculty inactive today
- Attendance analytics summary

### 🏢 Operations Monitoring
- Section capacity utilization
- Overloaded section detection
- Faculty workload distribution
- Busiest canteen stall detection
- Pending food order tracking

---

## 🍽 Smart Canteen Recommendation Engine
- Stall ranking algorithm
- Load-based scoring system
- Break-type weight adjustment
- Estimated wait time prediction
- Order placement system
- Order history tracking
- Real-time stall congestion detection

---

## 🛠 Make-Up & Remedial Module
- Faculty remedial scheduling
- Time-slot based sessions
- Section-specific remedial classes
- Dashboard visibility for students

---

## 🧪 Data Simulation Engine
- Automated university data seeding
- Random student generation
- Faculty distribution
- Attendance history generation
- Schedule generation
- Canteen order simulation

---

## 🖥️ Tech Stack

- **Backend:** Django
- **Database:** SQLite (development)
- **Frontend:** Bootstrap 5
- **ML Components:** OpenCV (Haar Cascade), NumPy
- **Email System:** SMTP (Gmail)
- **Data Simulation:** Faker
- **Version Control:** Git & GitHub

---

## 📂 Project Structure

```
campus_project/
│
├── accounts/ # Custom User & Role System
├── academics/ # Departments, Courses, Subjects, Schedule
├── attendance/ # AI + Manual Attendance Engine
├── canteen/ # Stall & Order Recommendation Engine
├── planner/ # Remedial & Make-Up Module
├── notifications/ # Email Alerts
├── ml/ # Face Embedding & Recognition Logic
├── templates/ # UI Templates
└── manage.py


```

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/ByriKarthik/smart-campus-ai.git
cd smart-campus-ai
```
2️⃣ Create Virtual Environment
```
python -m venv venv
venv\Scripts\activate   # Windows
```
3️⃣ Install Dependencies
```
pip install -r requirements.txt
```
4️⃣ Apply Migrations
```
python manage.py migrate
```
5️⃣ Generate Sample Data
```
python manage.py seed_university_data
```
6️⃣ Run Server
```
python manage.py runserver
```

Open:
```
http://127.0.0.1:8000/
```
# 📊 System Architecture

Timetable → Attendance → Analytics → Admin Monitoring
Canteen Orders → Load Engine → Stall Ranking → Operations Dashboard

The system is modular and interconnected to simulate real campus decision-making.

# 🎯 Key Highlights

- Fully integrated academic workflow

- Real-time schedule-aware attendance system

- Load-balanced canteen recommendation engine

- Intelligent dashboard insights

- Scalable architecture for future deployment

# 🚀 Future Improvements

- Production deployment (PostgreSQL + Cloud)

- Advanced timetable conflict solver

- Deep learning-based face recognition upgrade

- Real-time WebSocket notifications

- Interactive analytics charts

# 👨‍💻 Author

Karthik Byri

B.Tech

Computer Science
