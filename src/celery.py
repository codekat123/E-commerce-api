import os
from celery import Celery
from celery.schedules import crontab  # we'll use this for periodic scheduling

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')

app = Celery('src')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')



app.conf.beat_schedule = {
    'refresh_recommendations_every_2_days': {
        'task': 'recommendations.task.compute_item_similarity',  
        'schedule': crontab(minute=0, hour='*/50'),  
        'args': (), 
    },
}
