"""
Skrypt do sprawdzania konfiguracji Google OAuth
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from dotenv import load_dotenv

load_dotenv()

def check_config():
    print("🔍 Sprawdzanie konfiguracji Google OAuth...")
    print()
    
    errors = []
    warnings = []
    
    # 1. Sprawdź .env
    print("1️⃣ Sprawdzanie .env...")
    client_id = os.getenv('GOOGLE_LOGIN_CLIENT_ID', '')
    client_secret = os.getenv('GOOGLE_LOGIN_CLIENT_SECRET', '')
    
    if not client_id or client_id.startswith('your-'):
        errors.append("❌ GOOGLE_LOGIN_CLIENT_ID nie jest ustawione w .env")
    else:
        print(f"   ✓ GOOGLE_LOGIN_CLIENT_ID: {client_id[:20]}...")
    
    if not client_secret or client_secret.startswith('your-'):
        errors.append("❌ GOOGLE_LOGIN_CLIENT_SECRET nie jest ustawione w .env")
    else:
        print(f"   ✓ GOOGLE_LOGIN_CLIENT_SECRET: {client_secret[:10]}...")
    
    print()
    
    # 2. Sprawdź Site
    print("2️⃣ Sprawdzanie Django Site...")
    try:
        site = Site.objects.get(pk=1)
        print(f"   ✓ Site istnieje: {site.domain}")
        if site.domain not in ['localhost:8000', 'localhost', '127.0.0.1:8000']:
            warnings.append(f"⚠️ Site domain to '{site.domain}' - upewnij się że pasuje do twojego serwera")
    except Site.DoesNotExist:
        errors.append("❌ Site (pk=1) nie istnieje - uruchom: python manage.py setup_google_oauth")
    
    print()
    
    # 3. Sprawdź Social App
    print("3️⃣ Sprawdzanie Google Social App...")
    try:
        social_app = SocialApp.objects.get(provider='google')
        print(f"   ✓ Google Social App istnieje: {social_app.name}")
        print(f"   ✓ Client ID: {social_app.client_id[:20]}...")
        
        if social_app.sites.count() == 0:
            errors.append("❌ Social App nie ma przypisanego żadnego Site")
        else:
            print(f"   ✓ Przypisane sites: {social_app.sites.count()}")
    except SocialApp.DoesNotExist:
        errors.append("❌ Google Social App nie istnieje - uruchom: python manage.py setup_google_oauth")
    
    print()
    print("=" * 60)
    print()
    
    # Podsumowanie
    if errors:
        print("❌ Znalezione błędy:")
        for error in errors:
            print(f"   {error}")
        print()
        print("Aby naprawić, wykonaj:")
        print("   1. Edytuj plik .env i ustaw GOOGLE_LOGIN_CLIENT_ID i GOOGLE_LOGIN_CLIENT_SECRET")
        print("   2. Uruchom: python manage.py setup_google_oauth")
        print()
        return False
    
    if warnings:
        print("⚠️ Ostrzeżenia:")
        for warning in warnings:
            print(f"   {warning}")
        print()
    
    print("✅ Wszystko OK! Google OAuth jest poprawnie skonfigurowany.")
    print()
    print("Możesz teraz:")
    print("   1. Uruchomić serwer: python manage.py runserver")
    print("   2. Przejść do: http://localhost:8000/login/")
    print("   3. Kliknąć 'Zaloguj przez Google'")
    print()
    print("📖 Jeśli masz problemy, zobacz: QUICKSTART.md")
    print()
    
    return True

if __name__ == '__main__':
    check_config()
