
import os
import subprocess
import json
from flask import Flask, request, jsonify, send_file, render_template
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from pathlib import Path
import openai

from models import db, User, UserPreferences, VideoProject
from auth import auth_bp
from customization import customize_bp

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///lyricvision.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-me')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(customize_bp)

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# OpenAI config
openai.api_key = os.getenv('OPENAI_API_KEY', 'your-api-key-here')

ALLOWED_EXTENSIONS = {'mp3'}

RESOLUTION_MAP = {
    '720p': (1280, 720),
    '1080p': (1920, 1080),
    '4k': (3840, 2160),
}

FONT_MAP = {
    'DejaVu Sans Bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    'Liberation Serif': '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf',
    'Liberation Mono': '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
}

POSITION_MAP = {
    'center': '(h-text_h)/2',
    'bottom': 'h*0.75-text_h/2',
    'top': 'h*0.25-text_h/2',
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def transcribe_audio(audio_path):
    with open(audio_path, 'rb') as audio_file:
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
    segments = []
    for segment in response.segments:
        segments.append({
            'start': segment['start'],
            'end': segment['end'],
            'text': segment['text'].strip()
        })
    return segments


def get_audio_duration(audio_path):
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration', '-of',
        'default=noprint_wrappers=1:nokey=1', audio_path
    ]
    return float(subprocess.check_output(cmd).decode().strip())


def generate_video_with_settings(audio_path, segments, output_path, settings=None):
    if settings is None:
        settings = {}

    resolution = settings.get('resolution', '1080p')
    width, height = RESOLUTION_MAP.get(resolution, (1920, 1080))

    font_family = settings.get('font_family', 'DejaVu Sans Bold')
    font_path = FONT_MAP.get(font_family, FONT_MAP['DejaVu Sans Bold'])
    font_size = settings.get('font_size', 48)
    font_color = settings.get('font_color', '#FFFFFF').lstrip('#')

    bg_color_1 = settings.get('background_color_1', '#1a0a2e')
    text_position = settings.get('text_position', 'center')
    y_expr = POSITION_MAP.get(text_position, '(h-text_h)/2')

    text_animation = settings.get('text_animation', 'fade')
    vignette_enabled = settings.get('vignette_enabled', True)

    duration = get_audio_duration(audio_path)

    drawtext_parts = []
    for seg in segments:
        text = seg['text'].replace("'", "\\'").replace(":", "\\:")
        text = text.replace('"', '\\"').replace('%', '%%')
        start = seg['start']
        end = seg['end']

        if text_animation == 'fade':
            fade_in, fade_out = 0.4, 0.4
            alpha_expr = (
                f"if(lt(t-{start},{fade_in}),(t-{start})/{fade_in},"
                f"if(lt({end}-t,{fade_out}),({end}-t)/{fade_out},1))"
            )
        elif text_animation == 'typewriter':
            fade_out = 0.3
            alpha_expr = f"if(lt({end}-t,{fade_out}),({end}-t)/{fade_out},1)"
        elif text_animation == 'slide_up':
            fade_in, fade_out = 0.5, 0.3
            alpha_expr = (
                f"if(lt(t-{start},{fade_in}),(t-{start})/{fade_in},"
                f"if(lt({end}-t,{fade_out}),({end}-t)/{fade_out},1))"
            )
        else:
            fade_in, fade_out = 0.3, 0.3
            alpha_expr = (
                f"if(lt(t-{start},{fade_in}),(t-{start})/{fade_in},"
                f"if(lt({end}-t,{fade_out}),({end}-t)/{fade_out},1))"
            )

        if text_animation == 'slide_up':
            y_animated = (
                f"if(lt(t-{start},0.5),"
                f"{y_expr}+50*(1-(t-{start})/0.5),"
                f"{y_expr})"
            )
        else:
            y_animated = y_expr

        main_text = (
            f"drawtext=text='{text}':"
            f"fontfile={font_path}:"
            f"fontsize={font_size}:"
            f"fontcolor=#{font_color}:"
            f"shadowcolor=black@0.9:"
            f"shadowx=2:shadowy=2:"
            f"borderw=1:"
            f"x=(w-text_w)/2:"
            f"y={y_animated}:"
            f"enable='between(t,{start},{end})':"
            f"alpha='{alpha_expr}'"
        )
        drawtext_parts.append(main_text)

    filter_str = ','.join(drawtext_parts)

    if vignette_enabled:
        filter_str = f'vignette=PI/4,{filter_str}'

    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i',
        f'color=c={bg_color_1}:s={width}x{height}:d={duration}',
        '-i', audio_path,
        '-vf', filter_str,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '22',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        '-movflags', '+faststart',
        output_path
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})


@app.route('/upload', methods=['POST'])
@jwt_required(optional=True)
def upload_file():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    file = request.files['audio']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Only MP3 files are allowed'}), 400

    custom_settings = {}
    if request.form.get('settings'):
        try:
            custom_settings = json.loads(request.form['settings'])
        except json.JSONDecodeError:
            pass

    user_id = get_jwt_identity()
    if user_id:
        user = User.query.get(user_id)
        if user and user.preferences:
            base_settings = user.preferences.to_dict()
            base_settings.update(custom_settings)
            custom_settings = base_settings

    filename = secure_filename(file.filename)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(audio_path)

    try:
        segments = transcribe_audio(audio_path)
        if not segments:
            return jsonify({'error': 'Could not extract lyrics from audio'}), 422

        output_filename = f"{Path(filename).stem}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_lyrics.mp4"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        generate_video_with_settings(audio_path, segments, output_path, custom_settings)

        download_url = f'/download/{output_filename}'
        if user_id:
            video_project = VideoProject(
                user_id=user_id,
                title=request.form.get('title', Path(filename).stem),
                original_filename=filename,
                output_filename=output_filename,
                lyrics_json=json.dumps(segments),
                duration_seconds=get_audio_duration(audio_path),
                status='completed',
                completed_at=datetime.utcnow(),
                custom_settings=json.dumps(custom_settings)
            )
            db.session.add(video_project)
            db.session.commit()
            download_url = f'/api/videos/{video_project.id}/download'

        return jsonify({
            'success': True,
            'message': 'Lyrics video generated successfully!',
            'lyrics': [seg['text'] for seg in segments],
            'download_url': download_url
        })

    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    return jsonify({'error': 'File not found'}), 404


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, port=5000)

