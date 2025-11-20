"""
Skrypt sprawdzający Sites w bazie danych
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

print("🔍 Sprawdzanie Sites w bazie danych...")
print()

# Sprawdź wszystkie Sites
sites = Site.objects.all()
print(f"Znaleziono {sites.count()} Sites:")
for site in sites:
    print(f"   ID: {site.pk}, Domain: {site.domain}, Name: {site.name}")

print()

# Sprawdź Social Apps
social_apps = SocialApp.objects.filter(provider='google')
print(f"Znaleziono {social_apps.count()} Google Social Apps:")
for app in social_apps:
    print(f"   ID: {app.pk}, Name: {app.name}")
    print(f"   Client ID: {app.client_id[:20]}...")
    print(f"   Sites przypisane: {app.sites.count()}")
    for site in app.sites.all():
        print(f"      - {site.domain}")
    print()
