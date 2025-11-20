"""
Django management command to fix duplicate Google Social Apps
"""
from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Usuwa duplikaty Google Social App'

    def handle(self, *args, **kwargs):
        # Znajdź wszystkie Google Social Apps
        google_apps = SocialApp.objects.filter(provider='google')
        count = google_apps.count()
        
        if count == 0:
            self.stdout.write(
                self.style.ERROR('❌ Nie znaleziono żadnego Google Social App!')
            )
            return
        
        if count == 1:
            self.stdout.write(
                self.style.SUCCESS('✓ Jest tylko jeden Google Social App - wszystko OK!')
            )
            app = google_apps.first()
            self.stdout.write(f'   Name: {app.name}')
            self.stdout.write(f'   Client ID: {app.client_id[:20]}...')
            self.stdout.write(f'   Sites: {app.sites.count()}')
            return
        
        # Mamy duplikaty - usuń wszystkie oprócz pierwszego
        self.stdout.write(
            self.style.WARNING(f'⚠️ Znaleziono {count} Google Social Apps - usuwam duplikaty...')
        )
        
        # Zachowaj pierwszy
        first_app = google_apps.first()
        self.stdout.write(f'   Zachowuję: {first_app.name} (ID: {first_app.pk})')
        
        # Usuń resztę
        duplicates = google_apps.exclude(pk=first_app.pk)
        for dup in duplicates:
            self.stdout.write(f'   Usuwam: {dup.name} (ID: {dup.pk})')
            dup.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Usunięto {count - 1} duplikatów!')
        )
        self.stdout.write('')
        self.stdout.write('Pozostały Google Social App:')
        self.stdout.write(f'   Name: {first_app.name}')
        self.stdout.write(f'   Client ID: {first_app.client_id[:20]}...')
        self.stdout.write(f'   Sites: {first_app.sites.count()}')
