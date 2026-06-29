from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    avatar_url = db.Column(db.String(500), default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_premium = db.Column(db.Boolean, default=False)

    preferences = db.relationship('UserPreferences', backref='user', uselist=False, cascade='all, delete-orphan')
    videos = db.relationship('VideoProject', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'is_premium': self.is_premium,
            'created_at': self.created_at.isoformat(),
            'video_count': self.videos.count()
        }


class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    font_family = db.Column(db.String(100), default='DejaVu Sans Bold')
    font_size = db.Column(db.Integer, default=48)
    font_color = db.Column(db.String(7), default='#FFFFFF')
    glow_color = db.Column(db.String(7), default='#A855F7')
    glow_enabled = db.Column(db.Boolean, default=True)
    background_style = db.Column(db.String(50), default='dark_gradient')
    background_color_1 = db.Column(db.String(7), default='#0f0c29')
    background_color_2 = db.Column(db.String(7), default='#302b63')
    background_color_3 = db.Column(db.String(7), default='#24243e')
    text_position = db.Column(db.String(20), default='center')
    text_animation = db.Column(db.String(30), default='fade')
    resolution = db.Column(db.String(10), default='1080p')
    vignette_enabled = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'font_family': self.font_family,
            'font_size': self.font_size,
            'font_color': self.font_color,
            'glow_color': self.glow_color,
            'glow_enabled': self.glow_enabled,
            'background_style': self.background_style,
            'background_color_1': self.background_color_1,
            'background_color_2': self.background_color_2,
            'background_color_3': self.background_color_3,
            'text_position': self.text_position,
            'text_animation': self.text_animation,
            'resolution': self.resolution,
            'vignette_enabled': self.vignette_enabled,
        }


class VideoProject(db.Model):
    __tablename__ = 'video_projects'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(255))
    output_filename = db.Column(db.String(255))
    lyrics_json = db.Column(db.Text)
    duration_seconds = db.Column(db.Float)
    status = db.Column(db.String(20), default='processing')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, default=None)
    custom_settings = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'original_filename': self.original_filename,
            'status': self.status,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'download_url': f'/api/videos/{self.id}/download' if self.status == 'completed' else None
        }


