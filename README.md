# SkillConnect — Event Networking Platform

> **Connect, learn, and grow at professional events.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-skillconnect--12m0.onrender.com-brightgreen?style=for-the-badge)](https://skillconnect-12m0.onrender.com/)
[![GitHub](https://img.shields.io/badge/GitHub-sushma265%2FSkillConnect-blue?style=for-the-badge&logo=github)](https://github.com/sushma265/SkillConnect)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

---

## 🚀 Overview

**SkillConnect** is a full-stack event networking platform that enables professionals to discover, register for, and actively participate in events, workshops, and live sessions. It bridges the gap between event organizers and attendees through real-time tools, AI-powered assistance, seamless check-in, and rich analytics.

Whether you're an organizer managing logistics or an attendee looking to grow your network, SkillConnect has you covered.

---

## 🌐 Live Demo

🔗 **[https://skillconnect-12m0.onrender.com/](https://skillconnect-12m0.onrender.com/)**

| Link | Description |
|------|-------------|
| 🏠 [Home](https://skillconnect-12m0.onrender.com/) | Landing page — featured events & announcements |
| 📅 [Browse Events](https://skillconnect-12m0.onrender.com/browse-events) | All events & workshops |
| 🎤 [Browse Sessions](https://skillconnect-12m0.onrender.com/browse-sessions) | Keynotes, panels, and workshops |
| 📊 [Analytics](https://skillconnect-12m0.onrender.com/analytics-view) | Organizer dashboard |
| 🔐 [Login](https://skillconnect-12m0.onrender.com/login) | Sign in to your account |
| ✍️ [Register](https://skillconnect-12m0.onrender.com/register) | Create a free account |
| 🛠️ [Admin Panel](https://skillconnect-12m0.onrender.com/admin-panel) | Platform administration |
| 📋 [Dashboard](https://skillconnect-12m0.onrender.com/dashboard) | Personal user dashboard |

---

## ✨ Features

### 👤 For Attendees
- 🔍 Browse and filter events, workshops, and sessions
- 📝 Register and manage event attendance
- 🤝 Network with fellow attendees and exchange contacts
- 💬 Participate in live Q&A and polls during sessions
- 🎓 Download verified **certificates** upon session completion
- 🤖 Get instant answers via the **AI Chatbot** assistant
- 📹 Join live **video conference** sessions without leaving the platform
- 👤 Build a professional profile

### 🎯 For Organizers
- ➕ Create and publish events with scheduling details
- 📲 QR code check-in for seamless attendee management
- 📊 Analytics dashboard — track attendance, engagement & performance
- 📢 Post announcements and updates
- 🎓 Issue digital certificates to attendees
- 📹 Host virtual events via integrated video conferencing

### 🤖 AI Chatbot
- 💬 Smart assistant available 24/7 for attendees and organizers
- 📌 Answers queries about events, schedules, and registrations
- 🔎 Helps discover relevant sessions based on user interests
- ⚡ Instant responses without navigating away from the page

### 🎓 Certificates
- 🏅 Auto-generated digital certificates upon event/session completion
- 🔐 Tamper-proof and verifiable
- 📥 Downloadable in PDF format
- 🌐 Shareable directly to LinkedIn and other professional networks

### 📹 Video Conferencing
- 🎥 Host and join live virtual events natively
- 🔗 No third-party redirect — seamlessly embedded within the platform
- 🖥️ Screen sharing, chat, and participant management
- 📅 Scheduled and on-demand sessions supported

### 🛡️ Platform
- ⚡ Live sessions — keynotes, panels, workshops
- 🗳️ Interactive live polls and real-time feedback
- 📣 Announcements feed on the homepage
- 🛡️ Admin panel for platform governance
- 💸 100% Free to use

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Backend** | Python Flask |
| **Database** | MongoDB (PyMongo / Flask-PyMongo) |
| **Authentication** | Flask-Login (Session-based) |
| **AI Chatbot** | Integrated AI Assistant |
| **Video Conferencing** | Embedded Video SDK |
| **Certificates** | PDF Generation Engine |
| **Deployment** | Render.com |
| **Version Control** | Git & GitHub |

---

## 📁 Project Structure

```
SkillConnect/
├── static/              # Static assets
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript files
├── templates/           # Jinja2 HTML templates
│   ├── index.html       # Landing page
│   ├── browse_events.html
│   ├── browse_sessions.html
│   ├── dashboard.html
│   ├── analytics.html
│   ├── admin_panel.html
│   ├── chatbot.html
│   ├── certificates.html
│   ├── video_conference.html
│   ├── login.html
│   └── register.html
├── app.py               # Flask app entry point
├── routes/              # Flask Blueprints
├── models/              # MongoDB collection helpers
├── config.py            # App configuration
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

---

## 🔗 API Endpoints

SkillConnect follows a RESTful API architecture built using Flask and MongoDB.

### Authentication APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | User login |
| GET | `/auth/google` | Google OAuth login |
| GET | `/auth/google/callback` | Google OAuth callback |
| GET | `/auth/profile` | Get current user profile |
| POST | `/auth/logout` | Logout user |

### Event APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/events` | Create a new event |
| GET | `/events` | Get all events |
| GET | `/events/<event_id>` | Get event details |
| PUT | `/events/<event_id>` | Update an event |
| DELETE | `/events/<event_id>` | Delete an event |
| POST | `/events/<event_id>/register` | Register for an event |
| GET | `/events/my-registrations` | Get user registrations |
| GET | `/events/<event_id>/registrations` | Get event registrations |

### Session APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sessions` | Create session |
| GET | `/sessions` | Get all sessions |
| GET | `/sessions/<session_id>` | Get session details |
| PUT | `/sessions/<session_id>` | Update session |
| DELETE | `/sessions/<session_id>` | Delete session |

### Chatbot APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chatbot/message` | Send message to AI chatbot |
| GET | `/chatbot/history` | Get conversation history |
| DELETE | `/chatbot/clear` | Clear chat history |

### Certificate APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/certificates` | Get all user certificates |
| GET | `/certificates/<id>` | Get certificate details |
| GET | `/certificates/<id>/download` | Download certificate as PDF |
| POST | `/certificates/generate` | Generate certificate (admin/organizer) |
| GET | `/certificates/verify/<id>` | Verify certificate authenticity |

### Video Conference APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/video/create-room` | Create a video conference room |
| GET | `/video/join/<room_id>` | Join a conference room |
| GET | `/video/rooms` | List active rooms |
| DELETE | `/video/rooms/<room_id>` | End a conference session |

### Announcement APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/announcements` | Create announcement |
| GET | `/announcements` | Get all announcements |
| GET | `/announcements/<id>` | Get announcement |
| PUT | `/announcements/<id>` | Update announcement |
| DELETE | `/announcements/<id>` | Delete announcement |

### Networking APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/network/connect` | Send connection request |
| GET | `/network/connections` | Get user connections |
| PUT | `/network/accept/<id>` | Accept request |
| DELETE | `/network/remove/<id>` | Remove connection |

### Analytics APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics` | Platform analytics |
| GET | `/analytics/events` | Event analytics |
| GET | `/analytics/sessions` | Session analytics |
| GET | `/analytics/engagement` | Engagement metrics |

### Admin APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/users` | Manage users |
| DELETE | `/admin/users/<id>` | Delete user |
| GET | `/admin/events` | Manage events |
| DELETE | `/admin/events/<id>` | Delete event |
| GET | `/admin/reports` | Platform reports |

### Utility APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/` | Home page |

**Total APIs:** 40+ REST endpoints supporting authentication, event management, networking, analytics, QR check-ins, AI chatbot, certificates, video conferencing, announcements, and administration.

---

## ⚙️ Getting Started

### Prerequisites

- Python 3.8+
- pip
- MongoDB instance (local or Atlas)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/sushma265/SkillConnect.git
cd SkillConnect

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your MongoDB URI, secret key, etc.

# 5. Start the Flask development server
flask run
```

The app will be running at `http://localhost:5000`.

### Environment Variables

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
MONGO_URI=mongodb://localhost:27017/skillconnect
CHATBOT_API_KEY=your_chatbot_api_key
VIDEO_SDK_KEY=your_video_sdk_key
VIDEO_SDK_SECRET=your_video_sdk_secret
```

---

## 📸 Screenshots

| Page | Preview |
|------|---------|
| 🏠 Home | Featured events, announcements, platform stats |
| 📅 Events | Filterable grid of events & workshops |
| 🎤 Sessions | Keynotes, panels, and workshops by category |
| 📊 Analytics | Organizer metrics and engagement charts |
| 🤖 AI Chatbot | Smart assistant for instant help |
| 🎓 Certificates | Digital certificate viewer & downloader |
| 📹 Video Conference | Embedded live video session interface |

---

## 🗺️ Roadmap

- [x] 🤖 AI Chatbot for attendee assistance
- [x] 🎓 Digital certificates with PDF download
- [x] 📹 Embedded video conferencing
- [ ] 🐳 Docker & docker-compose for containerized deployment
- [ ] 📱 Mobile app (React Native / Flutter)
- [ ] 💳 Stripe / Razorpay payment gateway for paid events
- [ ] 🔔 Push notifications and email reminders
- [ ] 🌍 Multi-language support (i18n)
- [ ] 🎮 Gamification — badges, leaderboards, and achievements
- [ ] 🔗 Public API for third-party integrations

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

```bash
# 1. Fork the repository
# 2. Create your feature branch
git checkout -b feature/your-feature-name

# 3. Commit your changes
git commit -m "feat: add your feature description"

# 4. Push to the branch
git push origin feature/your-feature-name

# 5. Open a Pull Request
```

Please ensure your code follows the existing style and includes appropriate documentation.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👩‍💻 Author

**Sushma** — [@sushma265](https://github.com/sushma265)

---

<p align="center">
  <a href="https://skillconnect-12m0.onrender.com/">🌐 Try SkillConnect Live</a> &nbsp;|&nbsp;
  <a href="https://github.com/sushma265/SkillConnect">⭐ Star on GitHub</a>
</p>