# 📚 Dokumentacja Techniczna - YouTube Uploader App

## Spis treści
1. [Przegląd projektu](#1-przegląd-projektu)
2. [Architektura systemu](#2-architektura-systemu)
3. [Stack technologiczny](#3-stack-technologiczny)
4. [Struktura bazy danych](#4-struktura-bazy-danych)
5. [Moduły aplikacji](#5-moduły-aplikacji)
6. [API i integracje](#6-api-i-integracje)
7. [Bezpieczeństwo](#7-bezpieczeństwo)
8. [Instalacja i konfiguracja](#8-instalacja-i-konfiguracja)
9. [Deployment](#9-deployment)
10. [Testy i monitoring](#10-testy-i-monitoring)

---

## 1. Przegląd projektu

### 1.1 Cel aplikacji
YouTube Uploader to aplikacja webowa Django służąca do automatyzacji procesu tworzenia i publikacji YouTube Shorts. Aplikacja umożliwia:
- Upload długich filmów wideo
- Automatyczne cięcie na krótsze segmenty (YouTube Shorts) z live progress tracking
- Zarządzanie metadanymi (tytuły, opisy, tagi)
- Automatyczna publikacja na YouTube
- Real-time monitoring postępu przetwarzania
- Zarządzanie użytkownikami z systemem ról (User, Moderator, Admin)

### 1.2 Główne założenia
- **Modułowa architektura**: Separacja logiki biznesowej, prezentacji i danych
- **User-provided credentials**: Każdy użytkownik korzysta z własnych kluczy API YouTube
- **Asynchroniczne przetwarzanie**: Cięcie wideo w tle bez blokowania UI
- **Real-time progress tracking**: Live monitoring postępu przetwarzania z AJAX polling
- **System ról**: User, Moderator, Admin z różnymi uprawnieniami
- **Bezpieczeństwo**: OAuth 2.0, haszowanie haseł, walidacja danych

---

## 2. Architektura systemu

### 2.1 Wzorce projektowe

#### MVT (Model-View-Template)
Django implementuje wzorzec MVT:
- **Model**: Warstwa danych (`models.py`)
- **View**: Logika biznesowa (`views.py`)
- **Template**: Prezentacja (HTML templates)

#### Service Layer Pattern
Logika biznesowa wydzielona do serwisów:
- `youtube_service.py`: Integracja z YouTube API
- `video_processing.py`: Przetwarzanie wideo z FFmpeg

#### Repository Pattern
Django ORM działa jako warstwa abstrakcji nad bazą danych.

---

## 3. Stack technologiczny

### 3.1 Backend

| Technologia | Wersja | Zastosowanie |
|-------------|---------|-------------|
| **Python** | 3.x | Język programowania |
| **Django** | 5.2.7 | Framework webowy |
| **SQLite** | 3.x | Baza danych (dev) |
| **PostgreSQL** | 14+ | Baza danych (prod - rekomendowane) |

### 3.2 Frontend

| Technologia | Zastosowanie |
|-------------|-------------|
| **HTML5** | Struktura stron |
| **Tailwind CSS** | Stylowanie UI |
| **JavaScript (Vanilla)** | Interaktywność (progress bar, AJAX) |
| **Django Templates** | Rendering po stronie serwera |

### 3.3 Zewnętrzne API i narzędzia

| Narzędzie | Wersja | Zastosowanie |
|-----------|---------|-------------|
| **FFmpeg** | 4.4+ | Cięcie i przetwarzanie wideo |
| **Google OAuth 2.0** | - | Logowanie użytkowników |
| **YouTube Data API v3** | - | Upload i zarządzanie wideo |

### 3.4 Zależności Python

```python
Django==5.2.7                    # Web framework
google-auth-oauthlib==1.2.0      # Google OAuth flow (własna implementacja)
google-api-python-client==2.123.0 # YouTube API client
google-auth==2.28.0              # Google authentication
Pillow==10.2.0                   # Przetwarzanie obrazów (miniatury)
python-dotenv==1.0.0             # Zarządzanie zmiennymi środowiskowymi
ffmpeg-python==0.2.0             # Python wrapper dla FFmpeg
PyJWT==2.8.0                     # JWT tokens
cryptography==42.0.5             # Szyfrowanie
```

---

## 4. Moduły aplikacji

### 4.1 Moduł: Authentication (`views.py`)

#### Funkcje:
- `register_view()`: Rejestracja użytkownika (email + hasło)
- `login_view()`: Logowanie tradycyjne
- `google_login_direct()`: Inicjalizacja Google OAuth
- `google_callback()`: Callback po autoryzacji Google
- `logout_view()`: Wylogowanie
- `profile_edit_view()`: Edycja profilu

#### Przepływ logowania przez Google:

```python
1. User klika "Zaloguj przez Google"
   → google_login_direct()
   
2. Przekierowanie do Google OAuth
   → Użytkownik wybiera konto
   
3. Google callback z kodem autoryzacyjnym
   → google_callback()
   
4. Pobierz dane użytkownika z Google API
   → email, google_id, name, picture
   
5. Sprawdź czy użytkownik istnieje:
   - Tak: Zaloguj
   - Nie: Utwórz nowego użytkownika
   
6. Sesja Django + przekierowanie do dashboard
```

### 4.2 Moduł: Video Processing (`video_processing.py`)

#### System Progress Tracking

**Nowe pola w modelu Video:**
- `processing_progress`: IntegerField (0-100%) - procent ukończenia
- `processing_message`: CharField(255) - tekstowy status (np. "Tworzenie shorta 3/7...")
- `shorts_total`: IntegerField - planowana liczba shortów
- `shorts_created`: IntegerField - liczba już utworzonych shortów

**Aktualizacja w czasie rzeczywistym:**
System aktualizuje postęp po każdym utworzonym shorcie, umożliwiając live monitoring przez frontend.

#### Klasa: VideoProcessingService

**Metody:**
```python
def get_video_metadata():
    """Pobiera metadane wideo używając ffprobe"""
    # Zwraca: duration, width, height, resolution, file_size

def update_video_metadata():
    """Aktualizuje metadane w bazie danych"""

def cut_into_shorts(crop_mode='center'):
    """
    Główna metoda - dzieli wideo na shorty z live progress tracking
    
    Args:
        crop_mode: 'center', 'smart', 'top'
    
    Process:
        1. Analiza wideo (ffprobe)
        2. Obliczenie liczby shortów
        3. Ustawienie shorts_total w modelu
        4. Tworzenie segmentów (ffmpeg) w pętli:
           - Aktualizacja processing_progress
           - Aktualizacja processing_message
           - Aktualizacja shorts_created
           - Zapisywanie po każdym shorcie
        5. Generowanie miniatur
        6. Finalizacja (status='completed', progress=100%)
    
    Progress tracking example:
        shorts_total = 7
        Loop iteration 1: shorts_created=1, progress=14%, message="Tworzenie shorta 1/7..."
        Loop iteration 2: shorts_created=2, progress=28%, message="Tworzenie shorta 2/7..."
        ...
        Loop iteration 7: shorts_created=7, progress=100%, message="Gotowe! Utworzono 7 shortów."
    """

def _create_short_segment(start_time, duration, output_path, crop_mode):
    """
    Tworzy pojedynczy segment
    
    FFmpeg command:
        - Crop do 9:16 (1080x1920)
        - Scale do odpowiedniej rozdzielczości
        - Codec: h264
        - Audio: AAC 128k
    """

def generate_thumbnail(short, time_offset=1):
    """Generuje miniaturkę z FFmpeg"""
```

#### Funkcja: process_video_async()
```python
def process_video_async(video_id, crop_mode='center'):
    """
    Uruchamiana w osobnym wątku (threading.Thread)
    
    Flow:
        1. Pobierz Video z bazy
        2. Utwórz VideoProcessingService
        3. Pobierz metadane
        4. Pociąj na shorty
        5. Wygeneruj miniatury
        6. Zaktualizuj status Video
    """
```

### 4.3 Moduł: YouTube Integration (`youtube_service.py`)

#### Funkcja: get_authenticated_service()
```python
def get_authenticated_service(yt_account):
    """
    Tworzy authenticated YouTube service
    
    Args:
        yt_account: YTAccount z user credentials
    
    Returns:
        googleapiclient.discovery.Resource
    
    Process:
        1. Sprawdź ważność tokenu
        2. Odśwież jeśli wygasł (refresh_credentials_if_needed)
        3. Utwórz Credentials z user data
        4. Build YouTube service
    """
```

#### Funkcja: upload_short_to_youtube()
```python
def upload_short_to_youtube(short, yt_account, tags=''):
    """
    Upload shorta na YouTube
    
    Args:
        short: Obiekt Short
        yt_account: YTAccount (user credentials)
        tags: String z tagami (oddzielone spacją)
    
    Returns:
        {
            'success': bool,
            'video_id': str,
            'video_url': str,
            'error': str
        }
    
    Process:
        1. Przygotuj metadata (title, description, tags)
        2. Dodaj hashtagi do opisu
        3. Utwórz MediaFileUpload
        4. Upload resumable (chunks 1MB)
        5. Zwróć video_id i URL
    """
```

#### Scopes YouTube API:
```python
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]
```

### 4.4 Moduł: User Management (`views.py`)

#### Widoki dla moderatorów i adminów:

```python
@login_required
def user_management_list(request):
    """
    Lista użytkowników
    
    Permissions:
        - Moderator: Widzi tylko użytkowników z rolą 'user'
        - Admin: Widzi wszystkich
    
    Features:
        - Wyszukiwanie (username, email, name)
        - Filtrowanie po roli
        - Statystyki (video_count, short_count, views)
    """

@login_required
def user_management_create(request):
    """
    Tworzenie użytkownika
    
    Forms:
        - Moderator: ModeratorUserCreateForm (tylko rola 'user')
        - Admin: AdminUserCreateForm (wybór roli)
    """

@login_required
def user_management_detail(request, user_id):
    """
    Szczegóły użytkownika
    
    Display:
        - Statystyki (wideo, shorty, wyświetlenia)
        - Ostatnia aktywność
        - Lista wideo i shortów
        - Połączone konta YouTube
    """

@login_required
def user_management_edit(request, user_id):
    """
    Edycja użytkownika
    
    Forms:
        - Moderator: ModeratorUserEditForm (bez zmiany roli)
        - Admin: AdminUserEditForm (zmiana roli, staff, superuser)
    """

@login_required
def user_management_delete(request, user_id):
    """
    Usunięcie użytkownika
    
    Permissions: Tylko Admin
    Validation: Nie można usunąć samego siebie
    """
```

### 4.5 Moduł: Dashboard (`views.py`)

#### Dashboardy według ról:

```python
@login_required
def dashboard_view(request):
    """
    Główny dashboard - router
    
    Redirects:
        - Admin → admin_dashboard
        - Moderator → moderator_dashboard
        - User → user_dashboard
    """

@login_required
def user_dashboard(request):
    """
    Dashboard użytkownika
    
    Stats:
        - Liczba wideo (total, processing, completed)
        - Liczba shortów (total, published, pending)
        - Suma wyświetleń
    
    Lists:
        - 5 ostatnich wideo
        - 10 ostatnich shortów
    """

@login_required
def moderator_dashboard(request):
    """
    Dashboard moderatora
    
    Stats:
        - Globalne statystyki (użytkownicy, wideo, shorty)
        - Użytkownicy z największą aktywnością
    
    Lists:
        - 10 ostatnich wideo (wszyscy użytkownicy)
        - 15 ostatnich shortów
    """

@login_required
def admin_dashboard(request):
    """
    Dashboard administratora
    
    Stats:
        - Użytkownicy według ról
        - Statystyki z ostatnich 30 dni
        - Średnia wyświetleń na short
    
    Lists:
        - Top 10 użytkowników (według wyświetleń)
        - Ostatnie wideo, shorty, użytkownicy
    """
```

---

## 5. API i integracje

### 5.1 Google OAuth 2.0 (Logowanie)

#### Własna implementacja Google OAuth
**Uwaga:** Projekt implementuje własny Google OAuth flow (bez django-allauth) dla większej kontroli.

#### Credentials:
```python
# W .env file (ujednolicone nazwy)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

#### Redirect URI:
```
http://localhost:8000/auth/google/callback/
```

#### Implementacja:
- `google_login_direct()`: Inicjalizacja OAuth flow z google_auth_oauthlib.flow.Flow
- `google_callback()`: Obsługa callback, pobranie user info, utworzenie/zalogowanie użytkownika
- State parameter zapisywany w sesji dla zabezpieczenia CSRF

#### Scopes:
```python
scopes = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]
```

### 5.2 YouTube Data API v3 (Publikacja)

#### Credentials (User-provided):
Każdy użytkownik dostarcza własne:
- `client_id`
- `client_secret`

Przechowywane w modelu `YTAccount`.

#### Endpoints używane:

**1. Channels list (get channel info)**
```python
youtube.channels().list(
    part="snippet,contentDetails,statistics",
    mine=True
).execute()
```

**2. Videos insert (upload short)**
```python
youtube.videos().insert(
    part='snippet,status',
    body={
        'snippet': {
            'title': 'Title',
            'description': 'Description',
            'categoryId': '24',
            'tags': ['shorts']
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    },
    media_body=MediaFileUpload(...)
).execute()
```

**3. Videos list (get stats)**
```python
youtube.videos().list(
    part='statistics',
    id='video_id'
).execute()
```

#### Quota limits:
- **10,000 units/day** per user (własne credentials)
- Upload video: **1600 units**
- ~6 uploadów dziennie per user

### 5.3 FFmpeg Integration

#### Komendy używane:

**1. ffprobe (metadata)**
```bash
ffprobe -v quiet -print_format json -show_format -show_streams video.mp4
```

**2. ffmpeg (cutting + crop to 9:16)**
```bash
ffmpeg -y \
  -ss 60 \                          # Start time
  -i input.mp4 \                     # Input
  -t 60 \                            # Duration
  -vf "crop=ih*9/16:ih:(iw-oh)/2:0,scale=-2:1920" \  # Crop + scale
  -c:v libx264 \                     # Video codec
  -preset medium \                   # Encoding speed
  -crf 23 \                          # Quality
  -c:a aac \                         # Audio codec
  -b:a 128k \                        # Audio bitrate
  -movflags +faststart \             # Streaming optimization
  output.mp4
```

**3. ffmpeg (thumbnail)**
```bash
ffmpeg -y \
  -ss 1 \                            # Time offset
  -i input.mp4 \
  -vframes 1 \                       # Single frame
  -vf "scale=-2:1920" \              # Scale
  thumbnail.jpg
```

### 5.4 Internal API Endpoints

#### GET `/api/video/<pk>/progress/`
**Opis:** Real-time endpoint do monitorowania postępu przetwarzania wideo.

**Response:**
```json
{
    "status": "processing",
    "progress": 75,
    "message": "Tworzenie shorta 7/10...",
    "shorts_total": 10,
    "shorts_created": 7,
    "is_processing": true,
    "is_completed": false,
    "is_failed": false
}
```

**Użycie:** 
- AJAX polling z frontend co 2 sekundy
- Aktualizacja progress bar, licznika shortów, komunikatu
- Toast notifications przy każdym nowym shorcie
- Auto-refresh strony po zakończeniu (completed/failed)

**Frontend implementation:**
```javascript
// Polling co 2 sekundy
setInterval(() => {
    fetch('/api/video/{{ video.pk }}/progress/')
        .then(response => response.json())
        .then(data => {
            // Update progress bar
            document.getElementById('progress-bar').style.width = data.progress + '%';
            
            // Update text
            document.getElementById('progress-percent').textContent = data.progress + '%';
            document.getElementById('progress-message').textContent = data.message;
            
            // Show notification for new shorts
            if (data.shorts_created > lastCount) {
                showToast('✅ Utworzono short ' + data.shorts_created + '/' + data.shorts_total);
                lastCount = data.shorts_created;
            }
            
            // Auto-reload when done
            if (data.is_completed || data.is_failed) {
                setTimeout(() => location.reload(), 2000);
            }
        });
}, 2000);
```

**Performance:**
- Jeden query do bazy per request
- Lightweight JSON response (~200 bytes)
- Automatyczne czyszczenie interwału przy opuszczeniu strony

---

## 6. Bezpieczeństwo

### 6.1 Autentykacja i Autoryzacja

#### Haszowanie haseł:
```python
# Django domyślnie używa PBKDF2 + SHA256
AUTH_PASSWORD_VALIDATORS = [
    'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    'django.contrib.auth.password_validation.MinimumLengthValidator',
    'django.contrib.auth.password_validation.CommonPasswordValidator',
    'django.contrib.auth.password_validation.NumericPasswordValidator',
]
```

#### Ochrona przed CSRF:
```python
# settings.py
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',  # Włączone
]

# W formularzach HTML:
{% csrf_token %}
```

#### Login Required Decorator:
```python
from django.contrib.auth.decorators import login_required

@login_required
def protected_view(request):
    # Dostęp tylko dla zalogowanych
    pass
```

#### Permissions Checking:
```python
def moderator_only_view(request):
    if not request.user.is_moderator():
        messages.error(request, '❌ Brak dostępu.')
        return redirect('uploader:dashboard')
    # Logic...
```

### 6.2 OAuth Security

#### State Parameter:
```python
# Zapobiega CSRF w OAuth flow
request.session['oauth_state'] = state
```

#### Token Storage:
- **Access token**: W bazie danych (YTAccount model)
- **Refresh token**: W bazie (umożliwia odświeżenie)
- **Expiry tracking**: `token_expiry` field

**Zalecenia produkcyjne:**
- Szyfrowanie tokenów w bazie (`django-fernet-fields`)
- Rotacja kluczy
- Token expiry monitoring

### 6.3 Walidacja danych

#### Walidacja formularzy:
```python
class VideoUploadForm(forms.ModelForm):
    def clean_video_file(self):
        video = self.cleaned_data.get('video_file')
        
        # Sprawdź rozmiar (max 2GB)
        if video.size > 2 * 1024 * 1024 * 1024:
            raise forms.ValidationError('Plik zbyt duży (max 2GB)')
        
        # Sprawdź rozszerzenie
        valid_extensions = ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv']
        ext = video.name.lower().split('.')[-1]
        if f'.{ext}' not in valid_extensions:
            raise forms.ValidationError(f'Nieprawidłowy format')
        
        return video
```

#### Django ORM Protection:
- Automatyczna ochrona przed SQL Injection
- Parametryzowane zapytania

### 6.4 File Upload Security

#### Ograniczenia:
```python
# settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB

# Custom walidacja w formularzu
MAX_UPLOAD_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB
```

#### Bezpieczne ścieżki:
```python
# models.py
video_file = models.FileField(upload_to='videos/%Y/%m/%d/')
# Automatyczne generowanie unikalnych nazw plików
```

### 6.5 Secrets Management

#### Zmienne środowiskowe (.env):
```bash
SECRET_KEY=django-secret-key-here
DEBUG=False
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
DATABASE_URL=postgresql://...
```

**Nigdy nie commituj `.env` do Git!**

```gitignore
.env
*.env
client_secrets.json
```

---

## 7. Instalacja i konfiguracja

### 7.1 Wymagania systemowe

- **Python**: 3.8+
- **FFmpeg**: 4.4+
- **PostgreSQL**: 14+ (prod) lub SQLite (dev)
- **System operacyjny**: Windows, Linux, macOS

### 7.2 Instalacja krok po kroku

#### 1. Clone repository
```bash
git clone https://github.com/dawid-gulczynski/YoutubeUploaderApp.git
cd YoutubeUploaderApp
```

#### 2. Utwórz virtual environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

#### 3. Zainstaluj zależności
```bash
pip install -r requirements.txt
```

#### 4. Zainstaluj FFmpeg
Zobacz: `FFMPEG_INSTALL.md`

**Windows:**
```bash
# Uruchom skrypt instalacyjny
install_ffmpeg.bat
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

#### 5. Konfiguracja Google OAuth

**Krok 1: Google Cloud Console**
1. Przejdź do https://console.cloud.google.com
2. Utwórz nowy projekt
3. Włącz "Google+ API"
4. OAuth Consent Screen → External → Wypełnij dane
5. Credentials → Create OAuth 2.0 Client ID → Web application
6. Redirect URI: `http://localhost:8000/auth/google/callback/`
7. Skopiuj Client ID i Client Secret

**Krok 2: .env file**
```bash
# Utwórz plik .env w katalogu głównym
echo "SECRET_KEY=your-django-secret-key" > .env
echo "DEBUG=True" >> .env
echo "GOOGLE_CLIENT_ID=your-client-id" >> .env
echo "GOOGLE_CLIENT_SECRET=your-client-secret" >> .env
```

#### 6. Migracje bazy danych
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py init_roles
```

#### 7. Utwórz superusera
```bash
python manage.py createsuperuser
```

#### 8. Uruchom serwer deweloperski
```bash
python manage.py runserver
```

Aplikacja dostępna pod: **http://localhost:8000**

### 7.3 Konfiguracja YouTube API (dla użytkowników)

**Każdy użytkownik musi:**
1. Utworzyć własny projekt w Google Cloud Console
2. Włączyć YouTube Data API v3
3. Utworzyć OAuth 2.0 Client ID
4. Redirect URI: `http://localhost:8000/youtube/oauth/callback/`
5. W aplikacji: Połącz YouTube → Wklej Client ID i Secret

Zobacz: `GOOGLE_API_SETUP.md`

---

## 8. Deployment

### 8.1 Produkcyjne ustawienia Django

#### settings.py
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 8.2 Baza danych - PostgreSQL

```python
# settings.py
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600
    )
}
```

```bash
# .env
DATABASE_URL=postgresql://user:password@localhost:5432/youtube_uploader
```

### 8.3 Serwer WSGI (Gunicorn)

```bash
pip install gunicorn
```

```bash
# Uruchomienie
gunicorn app.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 8.4 Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }

    client_max_body_size 2G;  # Dla dużych uploadów
}
```

### 8.5 SSL/TLS (Certbot)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 8.6 Background Tasks (Celery - opcjonalnie)

Dla lepszej wydajności, zamień `threading` na Celery:

```bash
pip install celery redis
```

```python
# celery.py
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
app = Celery('app')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

```python
# tasks.py
from celery import shared_task
from .video_processing import process_video_async

@shared_task
def process_video_task(video_id, crop_mode='center'):
    return process_video_async(video_id, crop_mode)
```

---

## 9. Testy i monitoring

### 9.1 Unit Tests

```python
# tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Video, Short, Role

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.user_role = Role.objects.create(name='User', symbol='user')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role=self.user_role
        )
    
    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.has_role('user'))
        self.assertFalse(self.user.is_moderator())

class VideoProcessingTest(TestCase):
    def test_video_metadata_extraction(self):
        # Mock FFmpeg calls
        pass
    
    def test_short_creation(self):
        # Test cutting logic
        pass
```

#### Uruchomienie testów:
```bash
python manage.py test
```

### 9.2 Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'uploader': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

#### Użycie:
```python
import logging
logger = logging.getLogger(__name__)

logger.info('Info message')
logger.error('Error occurred', exc_info=True)
```

### 9.3 Monitoring

#### Django Debug Toolbar (development)
```bash
pip install django-debug-toolbar
```

#### Sentry (production error tracking)
```bash
pip install sentry-sdk
```

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
)
```

### 9.4 Performance Monitoring

#### Database Query Optimization
```python
# Używaj select_related i prefetch_related
videos = Video.objects.select_related('user').prefetch_related('shorts')
```

#### Caching
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

---

## 10. User Experience - Progress Tracking

### 10.1 Wizualna prezentacja postępu

#### Progress Bar
```html
<!-- Animowany pasek postępu -->
<div class="progress-container">
    <div class="progress-bar" 
         style="width: {{ video.processing_progress }}%"
         class="transition-all duration-500">
    </div>
</div>
```

#### Informacje tekstowe
- **Procent:** `42%` - Aktualny postęp
- **Licznik shortów:** `3/7 shortów` - Ile utworzono z całkowitej liczby
- **Status:** `Tworzenie shorta 3/7...` - Co się dzieje w tym momencie

#### Toast Notifications
```
✅ Utworzono short 1/7
✅ Utworzono short 2/7
✅ Utworzono short 3/7
...
🎉 Przetwarzanie zakończone! Utworzono 7 shortów.
```

### 10.2 Stany przetwarzania

| Status | Opis | Progress | Kolory |
|--------|------|----------|--------|
| `uploaded` | Wideo wgrane, oczekuje | 0% | Żółty badge |
| `processing` | Przetwarzanie w toku | 0-99% | Niebieski badge + spinner |
| `completed` | Zakończone pomyślnie | 100% | Zielony badge + checkmark |
| `failed` | Błąd podczas przetwarzania | - | Czerwony badge + warning |

### 10.3 Typowy przepływ z timelineami

**Przykład: 5-minutowe wideo → 5 shortów po 60s**

```
00:00 - Upload wideo
00:01 - Status: processing, Message: "Rozpoczynanie..."
00:05 - Message: "Analiza wideo..."
00:10 - shorts_total = 5, Message: "Tworzenie 5 shortów..."

00:30 - Short 1/5 created → progress=20%, Toast: "✅ Utworzono short 1/5"
00:50 - Short 2/5 created → progress=40%, Toast: "✅ Utworzono short 2/5"
01:10 - Short 3/5 created → progress=60%, Toast: "✅ Utworzono short 3/5"
01:30 - Short 4/5 created → progress=80%, Toast: "✅ Utworzono short 4/5"
01:50 - Short 5/5 created → progress=100%, Toast: "✅ Utworzono short 5/5"

02:00 - Status: completed, Toast: "🎉 Przetwarzanie zakończone!"
02:02 - Auto-refresh strony → Lista 5 shortów widoczna
```

### 10.4 Dashboard Integration

Progress tracking widoczny również na dashboardzie:
- Mini progress bar przy każdym przetwarzanym wideo
- Status badge (Processing/Completed/Failed)
- Szybki podgląd bez wchodzenia w szczegóły

### 10.5 Metryki UX

✅ **Cele osiągnięte:**
- Użytkownik zawsze wie co się dzieje
- Brak niepewności czy proces trwa
- Instant feedback po każdym shorcie
- Brak konieczności ręcznego odświeżania
- Klarowna komunikacja błędów

⏱️ **Performance:**
- Polling: 2 sekundy (optimal balance)
- Toast duration: 4 sekundy
- Auto-reload delay: 2 sekundy po zakończeniu

## 11. Troubleshooting

### 11.1 Częste problemy

#### Problem: FFmpeg nie znaleziony
**Rozwiązanie:**
```bash
# Sprawdź instalację
ffmpeg -version
ffprobe -version

# Dodaj do PATH (Windows)
setx PATH "%PATH%;C:\ffmpeg\bin"
```

#### Problem: Google OAuth redirect mismatch
**Rozwiązanie:**
- Sprawdź Redirect URI w Google Cloud Console
- Musi być **dokładnie** to samo co w kodzie
- Development: `http://localhost:8000/auth/google/callback/`

#### Problem: YouTube upload fails (quota exceeded)
**Rozwiązanie:**
- Sprawdź quota w Google Cloud Console
- Upload = 1600 units
- Daily limit = 10,000 units
- Możliwe ~6 uploadów dziennie

#### Problem: Token expired
**Rozwiązanie:**
```python
# Automatyczne odświeżanie w youtube_service.py
refresh_credentials_if_needed(yt_account)
```

### 11.2 Debug commands

```bash
# Sprawdź migracje
python manage.py showmigrations

# Otwórz Django shell
python manage.py shell

# Sprawdź konfigurację
python manage.py check

# Sprawdź środowisko
python check_environment.py

# Sprawdź OAuth
python check_oauth.py
```

---

## 12. Stan implementacji

### 12.1 Zaimplementowane funkcje ✅

#### Autentykacja i autoryzacja
- ✅ Rejestracja użytkowników (email + hasło)
- ✅ Logowanie tradycyjne
- ✅ **Google OAuth** (własna implementacja bez django-allauth)
- ✅ System ról (User, Moderator, Admin)
- ✅ Edycja profilu użytkownika
- ✅ Zarządzanie użytkownikami (dla moderatorów/adminów)

#### Przetwarzanie wideo
- ✅ Upload wideo (max 2GB)
- ✅ **FFmpeg integration** - automatyczne cięcie
- ✅ Konfiguracja parametrów (długość shorta, liczba, tryb kadrowania)
- ✅ **Real-time progress tracking** z AJAX polling
- ✅ Live progress bar (0-100%)
- ✅ Toast notifications przy każdym shorcie
- ✅ Generowanie miniatur
- ✅ Crop do formatu 9:16 (YouTube Shorts)

#### YouTube Integration
- ✅ **User-provided credentials** - każdy użytkownik własne API
- ✅ YouTube OAuth flow
- ✅ Upload shortów na YouTube
- ✅ Zarządzanie metadanymi (tytuł, opis, tagi)
- ✅ Privacy settings (public/unlisted/private)
- ✅ Made for kids option
- ✅ Odświeżanie statystyk (views, likes, comments)
- ✅ Automatyczne odświeżanie tokenów

#### Dashboard i monitoring
- ✅ User dashboard z statystykami
- ✅ Moderator dashboard (global stats)
- ✅ Admin dashboard (szczegółowe metryki)
- ✅ Lista wideo z mini progress bars
- ✅ Lista shortów z filtrami
- ✅ Zarządzanie użytkownikami

#### API i endpointy
- ✅ `/api/video/<pk>/progress/` - Real-time progress
- ✅ REST-like endpoints dla CRUD operacji
- ✅ Zabezpieczenia (@login_required, permissions)

---

## 13. Dokumentacja dla developerów
### 13.1 Database Migrations

```bash
# Utwórz migrację
python manage.py makemigrations

# Sprawdź SQL
python manage.py sqlmigrate uploader 0001

# Zastosuj migrację
python manage.py migrate

# Rollback
python manage.py migrate uploader 0001
```

---

## 14. Licencja i autorzy

**Autorzy:** Dawid Gulczyński, Kajetan Szlenzak  
**Framework:** Django 5.2.7  
**Wersja:** 2.1  
**Data utworzenia:** 2025-01-20  
**Ostatnia aktualizacja:** 2025-12-01  

---

## 15. Kontakt i wsparcie

**GitHub:** https://github.com/dawid-gulczynski/YoutubeUploaderApp  
**Issues:** https://github.com/dawid-gulczynski/YoutubeUploaderApp/issues  

---

**Koniec dokumentacji technicznej**
