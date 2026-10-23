# Salah Circle

**A multi-user cloud based prayer tracking and community accountability platform built with Flask and deployed on Google Cloud.**

Salah Circle helps Muslims track their five daily prayers (Fajr, Dhuhr, Asr, Maghrib, Isha), see friends' daily progress, and stay consistent through analytics, streaks, and AI-generated encouragement.

📄 **[Technical Report (IEEE format)](docs/Salah_Circle_IEEE.pdf)**

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-REST%20API-black?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![GCP](https://img.shields.io/badge/Google%20Cloud-Compute%20Engine-4285F4?logo=googlecloud)
![Gemini](https://img.shields.io/badge/Google-Gemini%20AI-8E75B2?logo=googlegemini)

---

## ✨ Features

- **Prayer Tracking**: Toggle each of the five daily prayers with one click.
- **Real-Time Prayer Times**: Daily timings from the [Aladhan API](https://aladhan.com/prayer-times-api) (ISNA method).
- **Multi-User Support**: Join by name, switch between users, and manage accounts with Flask sessions.
- **Social Feed**: See every user's progress for the day to encourage community accountability.
- **AI Motivation**: Personalized Islamic motivational messages from Google Gemini (`gemini-2.5-flash-lite`), with a fallback message if the API is unavailable.
- **Analytics Dashboard**:
  - 30-day prayer heatmap
  - 7-day completion trend
  - Streak counter (consecutive days with all 5 prayers)
  - 30-day completion rate

---

## 🏗️ Architecture

```
Browser ──HTTP──▶ Frontend (app.py :5002) ──REST/JSON──▶ Backend API (api.py :5001) ──▶ SQLite (prayer.db)
                        │                                        │
                        ▼                                        ▼
                  Aladhan API                             Google Gemini API
```

| Component | Description |
|-----------|-------------|
| `api.py` | Flask REST API: business logic, database access, Gemini integration |
| `app.py` | Flask frontend: Jinja2 templates, sessions, Aladhan integration |
| `prayer.db` | SQLite database (`users` and `prayers` tables) |
| `templates/` | `index.html` (dashboard), `analytics.html` (analytics page) |
| `static/` | Logo assets |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/users` | List all users |
| `POST` | `/api/users` | Create a user (or return the existing one) |
| `DELETE` | `/api/users/<id>` | Delete a user and their prayer records |
| `GET` | `/api/prayers/<id>/today` | Get today's prayers for a user |
| `POST` | `/api/prayers/<id>/toggle` | Toggle a prayer's completion |
| `GET` | `/api/social/today` | Get all users' progress for today |
| `GET` | `/api/analytics/<id>` | Get heatmap, 7-day trend, and streak |
| `GET` | `/api/motivation/<id>` | Get an AI-generated motivational message |

---

## 🗄️ Database Schema

```sql
users   (id, name UNIQUE, created_at)
prayers (id, user_id → users.id, prayer_name, prayer_date, completed, completed_at)
        UNIQUE (user_id, prayer_name, prayer_date)
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

### Run Locally

```bash
git clone https://github.com/Mdrafi4632/SalahCircle.git
cd SalahCircle

pip install flask requests google-generativeai

# Set your Gemini API key
export GEMINI_API_KEY="your-api-key"        # Windows: set GEMINI_API_KEY=your-api-key

# Terminal 1: start the backend API
python api.py

# Terminal 2: start the frontend
python app.py
```

Open **http://localhost:5002** in your browser.

### Run with Docker Compose

```bash
docker-compose up --build
```

The frontend reaches the API through Docker's internal network (`API_URL=http://api:5001`), and `prayer.db` is mounted as a volume so data persists.

---

## ☁️ Deployment

- **Google Compute Engine**: Both services run on a GCE VM (`us-central1`) with ports 5001 and 5002 open.
- **Docker Hub**:
  - [`rafi4632/prayer-tracker-api`](https://hub.docker.com/r/rafi4632/prayer-tracker-api)
  - [`rafi4632/prayer-tracker-app`](https://hub.docker.com/r/rafi4632/prayer-tracker-app)
- **Kubernetes (GKE)**: Deployment and Service manifests were created and a LoadBalancer IP was assigned. The pods failed to pull because the images were built on Apple Silicon (ARM64) and the GKE nodes run AMD64. Fix with a multi-platform build:

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t rafi4632/prayer-tracker-app:latest --push .
```

---

## 🔮 Future Improvements

- Password or OAuth authentication
- Move from SQLite to Cloud SQL for horizontal scaling
- Per-user location and time zone for accurate prayer times
- Cache daily Gemini messages to stay within API quota
- Prayer-time reminder notifications
- CI/CD pipeline for automated builds and deployment

---

## 👤 Author

**Md Rafiul Islam Rafi**
M.S. Student, Fordham University
CISC 5550 Cloud Computing, Professor Zhou Ji

---

> *"A person is upon the religion of his close friend, so let each of you look at whom he befriends."* (Abu Dawud & Tirmidhi)
