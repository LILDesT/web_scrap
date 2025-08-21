from celery import Celery
from app.config import settings

celery = Celery(
    'web_scraper',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks']
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_routes={
        'app.tasks.scrape_url': {'queue': 'scraping'},
    },
    task_annotations={
        'app.tasks.scrape_url': {'rate_limit': '10/m'}
    }
)