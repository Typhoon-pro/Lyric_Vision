# Lyric_Vision

# 🎵 LyricVision

> Transform your music into stunning cinematic lyrics videos powered by AI.

Upload an MP3 file and LyricVision will automatically transcribe the lyrics using OpenAI Whisper, then generate a beautiful video with animated text overlaid on cinematic backgrounds — ready to download and share.

---

## ✨ Features

- **AI-Powered Transcription** — Accurate lyrics extraction using OpenAI Whisper with precise timestamps
- **Cinematic Video Generation** — Dark gradient backgrounds with smooth text animations via FFmpeg
- **User Accounts** — Register, login, manage profile, and access video history
- **Full Customization** — Fonts, colors, backgrounds, text positions, animations, and resolution
- **Async Processing** — Celery workers handle video generation without blocking the API
- **Cloud-Ready** — Docker, Terraform (AWS), CI/CD with GitHub Actions
- **CDN Delivery** — CloudFront for fast global video downloads
- **Premium Tier** — 4K resolution, extended storage, priority processing

---

## 📁 Project Structure

lyricvision/ ├── app.py # Main Flask application ├── models.py # SQLAlchemy database models ├── auth.py # Authentication routes (JWT) ├── customization.py # Customization & video history API ├── celery_app.py # Async task queue (Celery + Redis) ├── requirements.prod.txt # Python dependencies ├── Dockerfile.prod # Production Docker image ├── docker-compose.prod.yml # Full production stack ├── deploy.sh # One-click deploy script ├── .env.example # Environment variable template ├── nginx/ │ └── nginx.conf # Reverse proxy configuration ├── terraform/ │ └── main.tf # AWS infrastructure (IaC) ├── .github/ │ └── workflows/ │ └── deploy.yml # CI/CD pipeline └── templates/ ├── index.html # Landing page (upload UI) ├── dashboard.html # User dashboard └── login.html # Login/register page

2. Configure Environment
bash



cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
3. Run the App
bash



python app.py
Visit http://localhost:5000 in your browser.

4. (Optional) Run Celery Worker
bash



celery -A celery_app worker --loglevel=info
🐳 Docker (Production)
Build & Run
bash



# Copy and configure your environment
cp .env.example .env.production
# Edit .env.production with real values

# Start all services
docker-compose -f docker-compose.prod.yml up -d --build
This starts:

Flask App (x2 replicas) — Gunicorn WSGI server
Celery Worker — Async video processing
Nginx — Reverse proxy, SSL, rate limiting
PostgreSQL — User data & video metadata
Redis — Task queue & caching

