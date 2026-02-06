import os
import logging
from celery import Celery
from celery.signals import worker_ready

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@worker_ready.connect
def preload_models(sender, **kwargs):
    """Pre-load ML models when Celery worker starts."""
    logger.info("Celery worker ready - pre-loading embedding model")
    
    try:
        from apps.conversations.huggingface_service import preload_model
        preload_model()
        logger.info("Embedding model pre-loaded successfully")
    except Exception as e:
        logger.error(f"Failed to pre-load embedding model: {e}", exc_info=True)