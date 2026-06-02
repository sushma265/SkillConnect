# SkillConnect 🎓

A Flask-based Skill Development & Event Management Platform where users can enroll in courses, register for workshops, book events, and make secure payments through Razorpay. Conductors can create and manage learning content, while administrators oversee the entire platform.

---

## 🚀 Features

### 👤 User

* Register and Login
* Browse Courses
* Purchase Courses
* View Events & Workshops
* Register for Events
* Submit Feedback
* View Announcements
* Payment History

### 🎤 Event Conductor

* Create Courses
* Create Workshops & Events
* Manage Learning Content
* Post Announcements
* View Registrations

### 🛡️ Admin

* Manage Users
* Manage Courses
* Manage Events
* Monitor Payments
* Platform Administration

---

## 🏗️ Tech Stack

* Flask
* Flask-SQLAlchemy
* Flask-JWT-Extended
* SQLite
* Razorpay Payment Gateway
* Python Dotenv
* Docker
* Docker Compose

---

## 📂 Project Structure

```text
skillconnect/
│
├── app/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── courses.py
│   │   ├── events.py
│   │   ├── payments.py
│   │   ├── feedback.py
│   │   ├── announcements.py
│   │   └── admin.py
│   │
│   ├── models.py
│   ├── utils.py
│   └── __init__.py
│
├── instance/
│   └── skillconnect.db
│
├── Dockerfile
├── docker-compose.yml
├── run.py
├── seed.py
├── requirements.txt
├── .env
└── README.md
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/your-username/skillconnect.git
cd skillconnect
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / Mac

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file:

```env
SECRET_KEY=your_secret_key

JWT_SECRET_KEY=your_jwt_secret

RAZORPAY_KEY_ID=your_razorpay_key

RAZORPAY_KEY_SECRET=your_razorpay_secret
```

---

## 🗄️ Initialize Database

```bash
python seed.py
```

---

## ▶️ Run Application

```bash
python run.py
```

Server starts at:

```text
http://127.0.0.1:5000
```

---

# 🐳 Docker Development

Run the application without installing Python dependencies locally.

## Dockerfile

Create a file named `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "run.py"]
```

## docker-compose.yml

Create a file named `docker-compose.yml`

```yaml
version: "3.9"

services:
  skillconnect:
    build: .
    container_name: skillconnect_app

    ports:
      - "5000:5000"

    env_file:
      - .env

    volumes:
      - .:/app
      - ./instance:/app/instance

    restart: unless-stopped
```

---

## Build Docker Image

```bash
docker build -t skillconnect .
```

---

## Run Docker Container

```bash
docker run -p 5000:5000 --env-file .env skillconnect
```

---

## Run Using Docker Compose

```bash
docker-compose up --build
```

---

## Run in Background

```bash
docker-compose up -d
```

---

## Stop Containers

```bash
docker-compose down
```

---

## View Logs

```bash
docker-compose logs -f
```

---

## Access Application

```text
http://localhost:5000
```

---

## 📡 Main API Routes

### Authentication

```http
POST /auth/signup
POST /auth/login
GET  /auth/me
```

### Courses

```http
GET    /courses
POST   /courses
GET    /courses/<id>
PUT    /courses/<id>
DELETE /courses/<id>
```

### Events

```http
GET    /events
POST   /events
GET    /events/<id>
PUT    /events/<id>
DELETE /events/<id>
POST   /events/<id>/register
```

### Payments

```http
POST /payments/create-order
POST /payments/verify
GET  /payments/history
```

### Feedback

```http
POST /feedback
GET  /feedback
```

### Announcements

```http
POST /announcements
GET  /announcements
```

---

## 💳 Razorpay Payment Flow

```text
User selects Course/Event
          ↓
Create Razorpay Order
          ↓
Complete Payment
          ↓
Verify Payment
          ↓
Access Granted
```

---

## 🔐 Authentication

Protected routes require JWT Token:

```http
Authorization: Bearer <access_token>
```

---

## 🎯 Future Enhancements

* QR Event Check-in
* Certificate Generation
* Email Notifications
* Real-Time Chat
* Event Analytics Dashboard
* AI Course Recommendations
* Docker Deployment on Cloud
* Kubernetes Support
* CI/CD Pipeline using GitHub Actions

---

## 👨‍💻 Developed For

**College Mini Project / Major Project**

**Domain:** EdTech + Event Management + Online Payments

---

## 📜 License

This project is developed for educational and learning purposes.
