# Konfiguracja automatycznej publikacji zaplanowanych shortów

## Jak to działa?

System pozwala zaplanować publikację shortów na YouTube na określoną datę i godzinę. Shorty ze statusem `scheduled` są automatycznie publikowane przez zadanie cron.

## Konfiguracja Crontab (Linux/macOS)

### 1. Otwórz crontab:
```bash
crontab -e
```

### 2. Dodaj wpis (sprawdzaj co 5 minut):
```bash
*/5 * * * * cd /Users/gulon/coding/YoutubeApp/YoutubeUploaderApp && /Users/gulon/coding/YoutubeApp/YoutubeUploaderApp/.venv/bin/python manage.py publish_scheduled_shorts >> /tmp/youtube_scheduled.log 2>&1
```

### 3. Sprawdź czy crontab został zapisany:
```bash
crontab -l
```

### 4. Logi:
Logi będą zapisywane w `/tmp/youtube_scheduled.log`. Możesz je sprawdzić:
```bash
tail -f /tmp/youtube_scheduled.log
```

## Testowanie

### Ręczne uruchomienie:
```bash
python manage.py publish_scheduled_shorts
```

### Dry-run (bez publikacji, tylko podgląd):
```bash
python manage.py publish_scheduled_shorts --dry-run
```

## Alternatywne rozwiązania

### Celery (dla produkcji)

Dla aplikacji produkcyjnych lepiej użyć Celery z Celery Beat:

1. Zainstaluj Celery:
```bash
pip install celery redis
```

2. Skonfiguruj w `settings.py`:
```python
# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_BEAT_SCHEDULE = {
    'publish-scheduled-shorts': {
        'task': 'uploader.tasks.publish_scheduled_shorts',
        'schedule': 300.0,  # Co 5 minut
    },
}
```

3. Utwórz `uploader/tasks.py`:
```python
from celery import shared_task
from django.core.management import call_command

@shared_task
def publish_scheduled_shorts():
    call_command('publish_scheduled_shorts')
```

4. Uruchom Celery worker i beat:
```bash
celery -A app worker -l info
celery -A app beat -l info
```

### Django-cron (prostsze niż Celery)

1. Zainstaluj:
```bash
pip install django-cron
```

2. Dodaj do `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ...
    'django_cron',
]
```

3. Utwórz `uploader/cron.py`:
```python
from django_cron import CronJobBase, Schedule
from django.core.management import call_command

class PublishScheduledShorts(CronJobBase):
    RUN_EVERY_MINS = 5
    
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'uploader.publish_scheduled_shorts'
    
    def do(self):
        call_command('publish_scheduled_shorts')
```

4. Uruchom:
```bash
python manage.py runcrons
```

## Jak użytkownicy planują shorty?

1. Użytkownik przechodzi do edycji shorta
2. Wypełnia pole "Zaplanowana data publikacji"
3. Klika "Zapisz i publikuj"
4. System:
   - Jeśli data jest w przyszłości → ustawia status `scheduled`
   - Jeśli pole jest puste → publikuje od razu
5. Cron co 5 minut sprawdza shorty z `scheduled_at <= now()` i je publikuje

## Monitorowanie

Sprawdź zaplanowane shorty w Django Admin:
- Przejdź do: Shorts → filtruj po status = "Zaplanowany"
- Sprawdź `scheduled_at` i `upload_status`

## Troubleshooting

### Shorty nie są publikowane automatycznie
1. Sprawdź czy crontab działa: `crontab -l`
2. Sprawdź logi: `tail -f /tmp/youtube_scheduled.log`
3. Uruchom ręcznie: `python manage.py publish_scheduled_shorts`
4. Sprawdź permissions: upewnij się, że cron ma dostęp do plików projektu

### Błędy OAuth
- Sprawdź czy użytkownik ma aktywne konto YouTube (is_active=True)
- Sprawdź czy tokeny nie wygasły
- Sprawdź logi: `/tmp/youtube_scheduled.log`
