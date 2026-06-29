import os
import json
from celery import Celery
from datetime import datetime, timedelta

celery_app = Celery(
    'lyricvision',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=540,
    worker_max_tasks_per_child=50,
    task_routes={
        'tasks.process_video': {'queue': 'video_processing'},
        'tasks.transcribe_audio': {'queue': 'transcription'},
    }
)


@celery_app.task(bind=True, name='tasks.process_video', max_retries=3)
def process_video_task(self, video_project_id, audio_path, settings):
    from app import app
    from models import db, VideoProject

    with app.app_context():
        video = VideoProject.query.get(video_project_id)
        if not video:
            return {'error': 'Video project not found'}

        try:
            video.status = 'processing'
            db.session.commit()

            self.update_state(state='TRANSCRIBING', meta={'progress': 20})
            from app import transcribe_audio
            segments = transcribe_audio(audio_path)

            if not segments:
                raise ValueError('Could not extract lyrics')

            video.lyrics_json = json.dumps(segments)
            db.session.commit()

            self.update_state(state='GENERATING', meta={'progress': 50})
            from app import generate_video_with_settings, get_audio_duration

            output_filename = f"{video.id}_lyrics.mp4"
            output_path = os.path.join('outputs', output_filename)
            generate_video_with_settings(audio_path, segments, output_path, settings)

            s3_url = None
            if os.getenv('S3_BUCKET'):
                self.update_state(state='UPLOADING', meta={'progress': 85})
                s3_url = upload_to_s3(output_path, output_filename)

            video.output_filename = output_filename
            video.duration_seconds = get_audio_duration(audio_path)
            video.status = 'completed'
            video.completed_at = datetime.utcnow()
            video.custom_settings = json.dumps(settings)
            db.session.commit()

            if os.path.exists(audio_path):
                os.remove(audio_path)

            return {
                'status': 'completed',
                'video_id': video.id,
                'download_url': s3_url or f'/api/videos/{video.id}/download'
            }

        except Exception as e:
            video.status = 'failed'
            db.session.commit()
            if self.request.retries < self.max_retries:
                raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
            return {'error': str(e)}


def upload_to_s3(file_path, filename):
    import boto3

    s3 = boto3.client('s3')
    bucket = os.getenv('S3_BUCKET')
    key = f'videos/{filename}'

    s3.upload_file(
        file_path, bucket, key,
        ExtraArgs={'ContentType': 'video/mp4', 'CacheControl': 'max-age=86400'}
    )

    cdn_url = os.getenv('CDN_URL')
    if cdn_url:
        return f'{cdn_url}/{key}'
    return f'https://{bucket}.s3.amazonaws.com/{key}'


@celery_app.task(name='tasks.cleanup_old_videos')
def cleanup_old_videos():
    from app import app
    from models import db, VideoProject, User

    with app.app_context():
        cutoff = datetime.utcnow() - timedelta(days=7)
        old_videos = VideoProject.query \
            .join(User) \
            .filter(User.is_premium == False) \
            .filter(VideoProject.created_at < cutoff) \
            .all()

        for video in old_videos:
            if video.output_filename:
                path = os.path.join('outputs', video.output_filename)
                if os.path.exists(path):
                    os.remove(path)
            db.session.delete(video)

        db.session.commit()
        return {'cleaned': len(old_videos)}


celery_app.conf.beat_schedule = {
    'cleanup-old-videos': {
        'task': 'tasks.cleanup_old_videos',
        'schedule': 86400.0,
    },
}


