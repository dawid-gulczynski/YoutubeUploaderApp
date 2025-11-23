"""
Management command do publikowania zaplanowanych shortów
Uruchom: python manage.py publish_scheduled_shorts
Lub dodaj do crontab: */5 * * * * cd /path/to/project && python manage.py publish_scheduled_shorts
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from uploader.models import Short, YTAccount
from uploader.youtube_service import upload_short_to_youtube
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Publikuje shorty zaplanowane na YouTube'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Pokaż co zostanie opublikowane bez faktycznego uploadowania',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        # Znajdź shorty zaplanowane do publikacji (scheduled_at <= teraz)
        scheduled_shorts = Short.objects.filter(
            upload_status='scheduled',
            scheduled_at__lte=now
        ).select_related('video__user')
        
        count = scheduled_shorts.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('Brak shortów do opublikowania.'))
            return
        
        self.stdout.write(f'Znaleziono {count} shortów do opublikowania...')
        
        published_count = 0
        failed_count = 0
        
        for short in scheduled_shorts:
            user = short.video.user
            
            if dry_run:
                self.stdout.write(
                    f'[DRY RUN] Opublikowałbym: "{short.title}" (ID: {short.id}) '
                    f'dla użytkownika {user.username}'
                )
                continue
            
            # Pobierz konto YouTube użytkownika
            yt_account = YTAccount.objects.filter(user=user, is_active=True).first()
            
            if not yt_account:
                self.stdout.write(
                    self.style.WARNING(
                        f'❌ Brak aktywnego konta YouTube dla użytkownika {user.username}. '
                        f'Short "{short.title}" (ID: {short.id}) zostanie pominięty.'
                    )
                )
                # Ustaw status na failed
                short.upload_status = 'failed'
                short.save()
                failed_count += 1
                continue
            
            try:
                # Ustaw status uploading
                short.upload_status = 'uploading'
                short.save()
                
                # Pobierz tagi z pola tags
                tags = short.tags if short.tags else ''
                
                self.stdout.write(f'Uploaduję: "{short.title}" (ID: {short.id})...')
                
                # Upload na YouTube
                result = upload_short_to_youtube(short, yt_account, tags)
                
                if result['success']:
                    # Sukces - zapisz dane YouTube
                    short.upload_status = 'published'
                    short.yt_video_id = result['video_id']
                    short.yt_url = result['video_url']
                    short.published_at = timezone.now()
                    short.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Opublikowano: "{short.title}" (ID: {short.id})'
                            f' -> {result["video_url"]}'
                        )
                    )
                    published_count += 1
                else:
                    # Błąd uploadu
                    short.upload_status = 'failed'
                    short.save()
                    
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Błąd podczas publikacji "{short.title}" (ID: {short.id}): '
                            f'{result["error"]}'
                        )
                    )
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f'Error publishing scheduled short {short.id}: {str(e)}')
                short.upload_status = 'failed'
                short.save()
                
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Wyjątek podczas publikacji "{short.title}" (ID: {short.id}): {str(e)}'
                    )
                )
                failed_count += 1
        
        # Podsumowanie
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Podsumowanie:')
        self.stdout.write(f'  • Znalezionych: {count}')
        self.stdout.write(self.style.SUCCESS(f'  • Opublikowanych: {published_count}'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'  • Nieudanych: {failed_count}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
