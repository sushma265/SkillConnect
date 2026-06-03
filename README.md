# SkillConnect — Event Networking Platform

> **Connect, learn, and grow at professional events.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-skillconnect--12m0.onrender.com-brightgreen?style=for-the-badge)](https://skillconnect-12m0.onrender.com/)
[![GitHub](https://img.shields.io/badge/GitHub-sushma265%2FSkillConnect-blue?style=for-the-badge&logo=github)](https://github.com/sushma265/SkillConnect)

---

## 🚀 Overview

**SkillConnect** is a full-stack event networking platform that enables professionals to discover, register for, and actively participate in events, workshops, and live sessions. It bridges the gap between event organizers and attendees through real-time tools, seamless check-in, and rich analytics.

Whether you're an organizer managing logistics or an attendee looking to grow your network, SkillConnect has you covered.

---

## 🌐 Live Demo

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

### For Attendees
- 🔍 Browse and filter events, workshops, and sessions
- 📝 Register and manage event attendance
- 🤝 Network with fellow attendees and exchange contacts
- 💬 Participate in live Q&A and polls during sessions
- 👤 Build a professional profile

### For Organizers
- ➕ Create and publish events with scheduling details
- 📲 QR code check-in for seamless attendee management
- 📊 Analytics dashboard — track attendance, engagement & performance
- 📢 Post announcements and updates

### Platform
- ⚡ Live sessions — keynotes, panels, workshops
- 🗳️ Interactive live polls and real-time feedback
- 📣 Announcements feed on the homepage
- 🛡️ Admin panel for platform governance
- 100% Free to use

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Backend** | Python Flask |
| **Database** | MongoDB (PyMongo / Flask-PyMongo) |
| **Authentication** | Flask-Login (Session-based) |
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

## ⚙️ Getting Started

### Prerequisites

- Node.js (v16+)
- npm or yarn
- MongoDB or PostgreSQL instance

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
```

---

## 📸 Screenshots

| Page | Preview |
|------|---------|
| 🏠 Home | Featured events, announcements, platform stats |
| 📅 Events | Filterable grid of events & workshops |
| 🎤 Sessions | Keynotes, panels, and workshops by category |
| 📊 Analytics | Organizer metrics and engagement charts |

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

Please ensure your code follows the existing code style and includes appropriate documentation.

---

## 🗺️ Roadmap

- [ ] 🐳 Docker & docker-compose for containerized deployment
- [ ] Mobile app (React Native / Flutter)
- [ ] AI-powered attendee matchmaking
- [ ] Video conferencing integration for virtual events
- [ ] Multi-language support (i18n)
- [ ] Stripe / Razorpay payment gateway for paid events
- [ ] Push notifications and email reminders
- [ ] Public API for third-party integrations
- [ ] Gamification — badges, leaderboards, and achievements

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👩‍💻 Author

**Sushma** — [@sushma265](https://github.com/sushma265)

---

<p align="center">Made with ❤️ · <a href="https://skillconnect-12m0.onrender.com/">Try SkillConnect Live</a></p>