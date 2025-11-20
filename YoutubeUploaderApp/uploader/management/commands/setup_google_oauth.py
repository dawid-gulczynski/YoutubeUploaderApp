"""
Django management command to configure Google OAuth Social App
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os


class Command(BaseCommand):
    help = 'Konfiguruje Google OAuth Social App dla logowania'

    def handle(self, *args, **kwargs):
        # Sprawdź czy mamy credentials w .env
        client_id = os.getenv('GOOGLE_LOGIN_CLIENT_ID', '')
        client_secret = os.getenv('GOOGLE_LOGIN_CLIENT_SECRET', '')
        
        if not client_id or not client_secret or client_id.startswith('your-'):
            self.stdout.write(
                self.style.ERROR('❌ Brak credentials w .env!')
            )
            self.stdout.write(
                'Ustaw GOOGLE_LOGIN_CLIENT_ID i GOOGLE_LOGIN_CLIENT_SECRET w pliku .env'
            )
            return
        
        # Upewnij się, że Site istnieje i jest poprawnie skonfigurowany
        site, created = Site.objects.get_or_create(
            pk=1,
            defaults={
                'domain': 'localhost:8000',
                'name': 'YouTube Uploader'
            }
        )
        
        if not created:
            # Zaktualizuj istniejący site
            site.domain = 'localhost:8000'
            site.name = 'YouTube Uploader'
            site.save()
            self.stdout.write(
                self.style.SUCCESS(f'✓ Zaktualizowano Site: {site.domain}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Utworzono Site: {site.domain}')
            )
        
        # Utwórz lub zaktualizuj Google Social App
        social_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google OAuth',
                'client_id': client_id,
                'secret': client_secret,
            }
        )
        
        if not created:
            # Zaktualizuj istniejący
            social_app.name = 'Google OAuth'
            social_app.client_id = client_id
            social_app.secret = client_secret
            social_app.save()
            self.stdout.write(
                self.style.SUCCESS('✓ Zaktualizowano Google Social App')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✓ Utworzono Google Social App')
            )
        
        # Dodaj site do social app
        if site not in social_app.sites.all():
            social_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Dodano site do Social App')
            )
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Konfiguracja Google OAuth zakończona pomyślnie!')
        )
        self.stdout.write('')
        self.stdout.write('Teraz możesz:')
        self.stdout.write('1. Uruchomić serwer: python manage.py runserver')
        self.stdout.write('2. Przejść do /login/')
        self.stdout.write('3. Kliknąć "Zaloguj przez Google"')
        self.stdout.write('')
        self.stdout.write('⚠️ Pamiętaj aby w Google Cloud Console:')
        self.stdout.write('   Authorized redirect URIs: http://localhost:8000/accounts/google/login/callback/')
