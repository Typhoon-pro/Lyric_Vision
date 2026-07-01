🎵 LyricVision
Transform your music into stunning cinematic lyrics videos powered by AI.

Status: Production Ready  •  Python 3.11+  •  License: MIT


Upload an MP3 file and LyricVision will automatically transcribe the lyrics using OpenAI Whisper, then generate a beautiful video with animated text overlaid on cinematic backgrounds — ready to download and share.

✨ Features
•	🎙️ AI-Powered Transcription — Accurate lyrics extraction using OpenAI Whisper with precise timestamps
•	🎬 Cinematic Video Generation — Dark gradient backgrounds with smooth text animations via FFmpeg
•	👤 User Accounts — Register, login, manage profile, and access video history
•	🎨 Full Customization — Fonts, colors, backgrounds, text positions, animations, and resolution
•	⚡ Async Processing — Celery workers handle video generation without blocking the API
•	☁️ Cloud-Ready — Docker, Terraform (AWS), CI/CD with GitHub Actions
•	🌍 CDN Delivery — CloudFront for fast global video downloads
•	💎 Premium Tier — 4K resolution, extended storage, priority processing

📁 Project Structure

lyricvision/
├── app.py                  # Main Flask application
├── models.py               # SQLAlchemy database models
├── auth.py                 # Authentication routes (JWT)
├── customization.py        # Customization & video history API
├── celery_app.py           # Async task queue (Celery + Redis)
├── requirements.prod.txt   # Python dependencies
├── Dockerfile.prod         # Production Docker image
├── docker-compose.prod.yml # Full production stack
├── deploy.sh               # One-click deploy script
├── .env.example            # Environment variable template
├── nginx/
│   └── nginx.conf          # Reverse proxy configuration
├── terraform/
│   └── main.tf             # AWS infrastructure (IaC)
├── .github/
│   └── workflows/
│       └── deploy.yml      # CI/CD pipeline
└── templates/
    ├── index.html          # Landing page (upload UI)
    ├── dashboard.html      # User dashboard
    └── login.html          # Login/register page


🚀 Quick Start (Local Development)
Prerequisites
•	Python 3.11+
•	FFmpeg installed (sudo apt install ffmpeg or brew install ffmpeg)
•	Redis (for Celery) — optional for local dev
•	OpenAI API key
1. Clone & Install

git clone https://github.com/Typhoon-pro/lyricvision.git
cd lyricvision

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.prod.txt

2. Configure Environment

cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

Minimal .env for local development:

SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-change-me
OPENAI_API_KEY=sk-your-openai-api-key-here
DATABASE_URL=sqlite:///lyricvision.db

3. Run the App

python app.py

Visit http://localhost:5000 in your browser.
4. (Optional) Run Celery Worker

# Start Redis first
redis-server

# In another terminal
celery -A celery_app worker --loglevel=info


🐳 Docker (Production)
Build & Run

# Copy and configure your environment
cp .env.example .env.production
# Edit .env.production with real values

# Start all services
docker-compose -f docker-compose.prod.yml up -d --build

This starts the following services:
Service	Purpose
Flask App (x2)	Gunicorn WSGI server
Celery Worker	Async video processing
Nginx	Reverse proxy, SSL, rate limiting
PostgreSQL	User data & video metadata
Redis	Task queue & caching

Access the App:
•	Frontend: http://localhost
•	API: http://localhost/api
•	Health Check: http://localhost/health

☁️ Cloud Deployment (AWS)
Architecture
Layer	Service	Purpose
CDN	CloudFront	Fast video delivery globally
Load Balancer	ALB	HTTPS termination, traffic distribution
App Servers	ECS Fargate (x2)	Flask API, auto-scales 2→10
Workers	ECS Fargate (x2)	Celery video processing
Queue	ElastiCache Redis	Task queue + session caching
Database	RDS PostgreSQL	User accounts, video metadata
Storage	S3	Generated video files
Secrets	Secrets Manager	API keys, credentials
CI/CD	GitHub Actions	Auto-deploy on push to main
Monitoring	CloudWatch + Sentry	Logs, metrics, error tracking

Prerequisites
•	AWS Account with CLI configured
•	Terraform installed
•	Domain name (optional, for SSL)
Deploy

# 1. Configure AWS credentials
aws configure

# 2. Create S3 bucket for Terraform state
aws s3 mb s3://lyricvision-terraform-state

# 3. Provision infrastructure
cd terraform
terraform init
terraform apply

# 4. Deploy everything
cd ..
chmod +x deploy.sh
./deploy.sh production

CI/CD Pipeline
Every push to main triggers the following pipeline:
◦	1. Test — Unit tests with pytest
◦	2. Build — Docker image built & pushed to ECR
◦	3. Deploy — ECS services updated with zero downtime
◦	4. Migrate — Database migrations run automatically
GitHub Secrets required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, OPENAI_API_KEY_TEST

🔌 API Reference
Authentication
Method	Endpoint	Description	Auth
POST	/api/auth/register	Create new account	❌
POST	/api/auth/login	Login, get JWT token	❌
POST	/api/auth/logout	Logout (discard token)	✅
GET	/api/auth/me	Get current user profile	✅
PATCH	/api/auth/me	Update profile	✅
POST	/api/auth/change-password	Change password	✅
POST	/api/auth/refresh	Refresh access token	✅

Upload & Processing
Method	Endpoint	Description	Auth
POST	/upload	Upload MP3 & generate video	Optional
GET	/download/<filename>	Download video (anonymous)	❌

Example: Upload Request

curl -X POST http://localhost:5000/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@song.mp3" \
  -F 'settings={"font_size": 56, "text_animation": "slide_up", "resolution": "1080p"}'

Example: Response

{
  "success": true,
  "message": "Lyrics video generated successfully!",
  "lyrics": [
    "Never gonna give you up",
    "Never gonna let you down",
    "Never gonna run around and desert you"
  ],
  "download_url": "/api/videos/uuid-here/download"
}

Customization
Method	Endpoint	Description	Auth
GET	/api/customization/options	Get all available options	❌
GET	/api/preferences	Get user's saved preferences	✅
PUT	/api/preferences	Update default preferences	✅

Video History
Method	Endpoint	Description	Auth
GET	/api/videos	List user's videos (paginated)	✅
GET	/api/videos/<id>	Get video details + lyrics	✅
GET	/api/videos/<id>/download	Download generated video	✅
DELETE	/api/videos/<id>	Delete video	✅
POST	/api/videos/<id>/regenerate	Regenerate with new settings	✅

🎨 Customization Options
Fonts
•	DejaVu Sans Bold (default)
•	Liberation Serif
•	Liberation Mono
Background Presets
•	Midnight — Dark purple gradient (default)
•	Deep Ocean — Navy blue
•	Sunset Blaze — Deep red
•	Neon Night — Dark neon purple
•	Dark Forest — Dark green
•	Aurora — Multi-color dark
•	Custom Colors — Pick your own RGB values
Text Animations
•	Fade — Smooth opacity in/out (default)
•	Typewriter — Characters appear sequentially
•	Slide Up — Text slides into position
•	Bounce — Text bounces into view
•	Glow Pulse — Text glows rhythmically
Text Positions
•	Center (default)
•	Top Third
•	Bottom Third
Resolutions
•	720p HD (1280×720)
•	1080p Full HD (1920×1080) — default
•	4K Ultra HD (3840×2160) — Premium only

🔐 Environment Variables
Variable	Description	Required	Default
SECRET_KEY	Flask secret key	✅	—
JWT_SECRET_KEY	JWT signing key	✅	—
OPENAI_API_KEY	OpenAI API key (Whisper)	✅	—
DATABASE_URL	PostgreSQL connection string	✅	sqlite:///lyricvision.db
REDIS_URL	Redis connection string	For Celery	redis://localhost:6379/0
AWS_ACCESS_KEY_ID	AWS credentials	For S3/CDN	—
AWS_SECRET_ACCESS_KEY	AWS secret access key	For S3/CDN	—
S3_BUCKET	S3 bucket for videos	For cloud	—
CDN_URL	CloudFront distribution URL	For cloud	—
SENTRY_DSN	Sentry error tracking	Optional	—

Full .env.example

# ---- App Settings ----
FLASK_ENV=production
SECRET_KEY=generate-a-random-64-char-string
JWT_SECRET_KEY=generate-another-random-64-char-string

# ---- OpenAI (for Whisper transcription) ----
OPENAI_API_KEY=sk-your-openai-api-key

# ---- Database (PostgreSQL) ----
DB_USER=lyricvision_admin
DB_PASSWORD=your-secure-db-password
DB_NAME=lyricvision
DATABASE_URL=postgresql://lyricvision_admin:your-password@db:5432/lyricvision

# ---- Redis (Task Queue) ----
REDIS_PASSWORD=your-redis-password
REDIS_URL=redis://:your-redis-password@redis:6379/0

# ---- AWS (Storage & CDN) ----
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET=lyricvision-videos-production
CDN_URL=https://d1234567890.cloudfront.net

# ---- Domain & SSL ----
DOMAIN=lyricvision.com

# ---- Monitoring (Optional) ----
SENTRY_DSN=https://xxx@sentry.io/xxx


🧪 Running Tests

# Install test dependencies
pip install pytest pytest-cov pytest-flask

# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html

Test Structure

tests/
├── test_auth.py           # Authentication tests
├── test_upload.py         # Upload & processing tests
├── test_customization.py  # Customization API tests
└── conftest.py            # Pytest fixtures


📈 Scaling & Performance
Horizontal Scaling
•	ECS Auto-Scaling: App instances scale from 2→10 based on CPU utilization (70% threshold)
•	Worker Scaling: Separate worker service scales independently for video processing
•	Load Balancing: ALB distributes traffic across healthy instances
Storage Optimization
•	S3 Lifecycle: Auto-moves videos to cheaper storage tiers
◦	30 days → Standard-IA
◦	90 days → Glacier
◦	Free-tier videos deleted after 7 days
•	CDN Caching: CloudFront caches videos at edge locations worldwide
•	Database: RDS Multi-AZ automatic failover for high availability
•	Monitoring: CloudWatch metrics, logs, alarms + Sentry for real-time error tracking

🐛 Troubleshooting
FFmpeg not found

# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Verify installation
ffmpeg -version

Redis connection error

# Start Redis locally
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine

OpenAI API errors
•	Check your API key is valid
•	Ensure you have credits in your OpenAI account
•	Verify the audio file is a valid MP3
Database migration issues

# Initialize migrations
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade


🛣️ Roadmap
Phase 1 (Current)
•	☑ Core video generation
•	☑ User authentication
•	☑ Basic customization
•	☑ Cloud deployment
Phase 2 (Q3 2026)
•	☐ Real-time progress via WebSockets
•	☐ Background video/image uploads (custom backgrounds)
•	☐ Multi-language transcription support
•	☐ Karaoke mode (word-level highlighting)
Phase 3 (Q4 2026)
•	☐ Social sharing (direct to YouTube/TikTok)
•	☐ Team/collaboration workspaces
•	☐ Mobile app (React Native)
•	☐ Stripe payment integration for Premium
Phase 4 (2027)
•	☐ AI-generated background videos
•	☐ Voice cloning for covers
•	☐ Batch processing API
•	☐ White-label solution for agencies

📄 License
MIT License
Copyright (c) 2026 Typhoon
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

🤝 Contributing
Contributions are welcome! Please follow these steps:
1.	Fork the repository
2.	Create your feature branch (git checkout -b feature/amazing-feature)
3.	Commit your changes (git commit -m 'Add amazing feature')
4.	Push to the branch (git push origin feature/amazing-feature)
5.	Open a Pull Request
Contribution Guidelines
•	Write clear, descriptive commit messages
•	Add tests for new features
•	Update documentation as needed
•	Follow PEP 8 style guide for Python code
•	Ensure all tests pass before submitting PR

🙏 Acknowledgments
•	OpenAI Whisper — Speech-to-text transcription
•	FFmpeg — Video generation engine
•	Flask — Web framework
•	Celery — Distributed task queue
•	Terraform — Infrastructure as Code
•	PostgreSQL — Database
•	Redis — In-memory data store
•	AWS — Cloud infrastructure

📞 Support
•	Issues: github.com/Typhoon-pro/lyricvision/issues
•	Discussions: github.com/Typhoon-pro/lyricvision/discussions
•	Email: typhoonochieng515@gmail.com

Built with ❤️ by Typhoon
Making music visual, one lyric at a time
