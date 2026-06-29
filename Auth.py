from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from models import db, User, UserPreferences
from datetime import timedelta
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, ""


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not username or len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400

    if not validate_email(email):
        return jsonify({'error': 'Invalid email address'}), 400

    is_valid, msg = validate_password(password)
    if not is_valid:
        return jsonify({'error': msg}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    preferences = UserPreferences(user=user)

    db.session.add(user)
    db.session.add(preferences)
    db.session.commit()

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=24))
    refresh_token = create_refresh_token(identity=user.id, expires_delta=timedelta(days=30))

    return jsonify({
        'message': 'Account created successfully!',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password'}), 401

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=24))
    refresh_token = create_refresh_token(identity=user.id, expires_delta=timedelta(days=30))

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    })


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logged out successfully'})


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'user': user.to_dict(),
        'preferences': user.preferences.to_dict() if user.preferences else {}
    })


@auth_bp.route('/me', methods=['PATCH'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()

    if 'username' in data:
        new_username = data['username'].strip()
        if len(new_username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != user.id:
            return jsonify({'error': 'Username already taken'}), 409
        user.username = new_username

    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']

    db.session.commit()
    return jsonify({'user': user.to_dict()})


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()

    if not user.check_password(data.get('current_password', '')):
        return jsonify({'error': 'Current password is incorrect'}), 401

    is_valid, msg = validate_password(data.get('new_password', ''))
    if not is_valid:
        return jsonify({'error': msg}), 400

    user.set_password(data['new_password'])
    db.session.commit()
    return jsonify({'message': 'Password changed successfully'})


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id, expires_delta=timedelta(hours=24))
    return jsonify({'access_token': access_token})


