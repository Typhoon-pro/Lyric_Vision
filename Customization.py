from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, UserPreferences, VideoProject
import os
import json

customize_bp = Blueprint('customize', __name__, url_prefix='/api')

AVAILABLE_FONTS = [
    {'id': 'dejavu_bold', 'name': 'DejaVu Sans Bold', 'path': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'},
    {'id': 'liberation_serif', 'name': 'Liberation Serif', 'path': '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'},
    {'id': 'liberation_mono', 'name': 'Liberation Mono', 'path': '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf'},
]

BACKGROUND_PRESETS = [
    {'id': 'dark_gradient', 'name': 'Midnight', 'colors': ['#0f0c29', '#302b63', '#24243e']},
    {'id': 'ocean', 'name': 'Deep Ocean', 'colors': ['#000428', '#004e92', '#000428']},
    {'id': 'sunset', 'name': 'Sunset Blaze', 'colors': ['#1a0000', '#4a0000', '#1a0000']},
    {'id': 'neon', 'name': 'Neon Night', 'colors': ['#0a001a', '#1a0033', '#0a001a']},
    {'id': 'forest', 'name': 'Dark Forest', 'colors': ['#0a1a0a', '#1a3320', '#0a1a0a']},
    {'id': 'aurora', 'name': 'Aurora', 'colors': ['#0f0f23', '#1a0a2e', '#0a1628']},
    {'id': 'custom', 'name': 'Custom Colors', 'colors': None},
]

TEXT_ANIMATIONS = [
    {'id': 'fade', 'name': 'Fade In/Out', 'description': 'Smooth opacity transition'},
    {'id': 'typewriter', 'name': 'Typewriter', 'description': 'Characters appear one by one'},
    {'id': 'slide_up', 'name': 'Slide Up', 'description': 'Text slides up into position'},
    {'id': 'bounce', 'name': 'Bounce', 'description': 'Text bounces into view'},
    {'id': 'glow_pulse', 'name': 'Glow Pulse', 'description': 'Text glows rhythmically'},
]

TEXT_POSITIONS = [
    {'id': 'center', 'name': 'Center', 'y_expr': '(h-text_h)/2'},
    {'id': 'bottom', 'name': 'Bottom Third', 'y_expr': 'h*0.75-text_h/2'},
    {'id': 'top', 'name': 'Top Third', 'y_expr': 'h*0.25-text_h/2'},
]

RESOLUTIONS = [
    {'id': '720p', 'name': '720p HD', 'width': 1280, 'height': 720},
    {'id': '1080p', 'name': '1080p Full HD', 'width': 1920, 'height': 1080},
    {'id': '4k', 'name': '4K Ultra HD', 'width': 3840, 'height': 2160, 'premium': True},
]


@customize_bp.route('/customization/options', methods=['GET'])
def get_customization_options():
    return jsonify({
        'fonts': AVAILABLE_FONTS,
        'backgrounds': BACKGROUND_PRESETS,
        'animations': TEXT_ANIMATIONS,
        'positions': TEXT_POSITIONS,
        'resolutions': RESOLUTIONS
    })


@customize_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.preferences:
        return jsonify({'error': 'Preferences not found'}), 404
    return jsonify({'preferences': user.preferences.to_dict()})


@customize_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    prefs = user.preferences
    if not prefs:
        prefs = UserPreferences(user_id=user.id)
        db.session.add(prefs)

    allowed_fields = [
        'font_family', 'font_size', 'font_color', 'glow_color',
        'glow_enabled', 'background_style', 'background_color_1',
        'background_color_2', 'background_color_3', 'text_position',
        'text_animation', 'resolution', 'vignette_enabled'
    ]

    for field in allowed_fields:
        if field in data:
            if field == 'font_size':
                data[field] = max(24, min(96, int(data[field])))
            if field == 'resolution' and data[field] == '4k' and not user.is_premium:
                return jsonify({'error': '4K resolution requires a premium account'}), 403
            setattr(prefs, field, data[field])

    db.session.commit()
    return jsonify({'message': 'Preferences updated', 'preferences': prefs.to_dict()})


@customize_bp.route('/videos', methods=['GET'])
@jwt_required()
def get_video_history():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    videos = VideoProject.query.filter_by(user_id=user_id) \
        .order_by(VideoProject.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'videos': [v.to_dict() for v in videos.items],
        'total': videos.total,
        'pages': videos.pages,
        'current_page': page
    })


@customize_bp.route('/videos/<video_id>', methods=['GET'])
@jwt_required()
def get_video_detail(video_id):
    user_id = get_jwt_identity()
    video = VideoProject.query.filter_by(id=video_id, user_id=user_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    result = video.to_dict()
    if video.lyrics_json:
        result['lyrics'] = json.loads(video.lyrics_json)
    if video.custom_settings:
        result['settings'] = json.loads(video.custom_settings)
    return jsonify(result)


@customize_bp.route('/videos/<video_id>/download', methods=['GET'])
@jwt_required()
def download_video(video_id):
    user_id = get_jwt_identity()
    video = VideoProject.query.filter_by(id=video_id, user_id=user_id).first()

    if not video:
        return jsonify({'error': 'Video not found'}), 404
    if video.status != 'completed':
        return jsonify({'error': 'Video is not ready yet'}), 400

    file_path = os.path.join('outputs', video.output_filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Video file not found on server'}), 404

    return send_file(file_path, as_attachment=True, download_name=f"{video.title}_lyrics.mp4", mimetype='video/mp4')


@customize_bp.route('/videos/<video_id>', methods=['DELETE'])
@jwt_required()
def delete_video(video_id):
    user_id = get_jwt_identity()
    video = VideoProject.query.filter_by(id=video_id, user_id=user_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    if video.output_filename:
        file_path = os.path.join('outputs', video.output_filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(video)
    db.session.commit()
    return jsonify({'message': 'Video deleted successfully'})


@customize_bp.route('/videos/<video_id>/regenerate', methods=['POST'])
@jwt_required()
def regenerate_video(video_id):
    user_id = get_jwt_identity()
    video = VideoProject.query.filter_by(id=video_id, user_id=user_id).first()

    if not video:
        return jsonify({'error': 'Video not found'}), 404
    if not video.lyrics_json:
        return jsonify({'error': 'No lyrics data available for regeneration'}), 400

    data = request.get_json() or {}
    video.status = 'processing'
    video.custom_settings = json.dumps(data.get('settings', {}))
    db.session.commit()

    return jsonify({'message': 'Video regeneration started', 'video': video.to_dict()})


