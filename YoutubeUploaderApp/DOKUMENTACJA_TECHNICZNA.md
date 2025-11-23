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
- Automatyczne cięcie na krótsze segmenty (YouTube Shorts)
- Zarządzanie metadanymi (tytuły, opisy, tagi)
- Automatyczna publikacja na YouTube
- Zarządzanie użytkownikami z systemem ról

### 1.2 Główne założenia
- **Modułowa architektura**: Separacja logiki biznesowej, prezentacji i danych
- **User-provided credentials**: Każdy użytkownik korzysta z własnych kluczy API YouTube
- **Asynchroniczne przetwarzanie**: Cięcie wideo w tle bez blokowania UI
- **System ról**: User, Moderator, Admin z różnymi uprawnieniami
- **Bezpieczeństwo**: OAuth 2.0, haszowanie haseł, walidacja danych

---

## 2. Architektura systemu

### 2.1 Diagram architektury

```
┌─────────────────────────────────────────────────────────────┐
│                       FRONTEND (Templates)                   │
│  HTML + Tailwind CSS + JavaScript + HTMX (opcjonalnie)      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    DJANGO APPLICATION LAYER                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Views      │  │    Forms     │  │   Context    │      │
│  │  (views.py)  │  │  (forms.py)  │  │  Processors  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Services   │  │  Utilities   │  │   Managers   │      │
│  │ (youtube_    │  │   (video_    │  │   (custom)   │      │
│  │  service.py) │  │ processing)  │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA ACCESS LAYER                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 Django ORM (models.py)                │   │
│  │  - User Model                                         │   │
│  │  - Video Model                                        │   │
│  │  - Short Model                                        │   │
│  │  - YTAccount Model                                    │   │
│  │  - Role Model                                         │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATABASE (SQLite)                       │
│  Przechowuje: użytkownicy, wideo, shorty, tokeny OAuth      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL INTEGRATIONS                      │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │  Google OAuth  │  │ YouTube Data   │  │    FFmpeg    │  │
│  │   (Login)      │  │   API v3       │  │ (Processing) │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Wzorce projektowe

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

### 2.3 Przepływ danych

#### Proces uploadu i publikacji:
```
1. User upload wideo → VideoUploadView
2. Zapisanie do bazy → Video.objects.create()
3. Uruchomienie przetwarzania → process_video_async() (w tle)
4. FFmpeg dzieli wideo → VideoProcessingService.cut_into_shorts()
5. Tworzenie obiektów Short → Short.objects.create()
6. User edytuje metadane → ShortEditView
7. Publikacja na YouTube → upload_short_to_youtube()
8. Aktualizacja statusu → Short.upload_status = 'published'
```

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
google-auth-oauthlib==1.2.0      # Google OAuth flow
google-api-python-client==2.123.0 # YouTube API client
google-auth==2.28.0              # Google authentication
Pillow==10.2.0                   # Przetwarzanie obrazów (miniatury)
python-dotenv==1.0.0             # Zarządzanie zmiennymi środowiskowymi
ffmpeg-python==0.2.0             # Python wrapper dla FFmpeg
PyJWT==2.8.0                     # JWT tokens
cryptography==42.0.5             # Szyfrowanie
```

---

## 4. Struktura bazy danych

### 4.1 Diagram ER

```
┌─────────────────┐
│      Role       │
├─────────────────┤
│ id (PK)         │
│ name            │
│ symbol (UNIQUE) │◄────────┐
└─────────────────┘         │
                            │ FK
┌─────────────────┐         │
│      User       │         │
├─────────────────┤         │
│ id (PK)         │         │
│ username        │         │
│ email (UNIQUE)  │         │
│ password        │         │
│ role_id (FK)    ├─────────┘
│ google_id       │
│ google_email    │
│ auth_provider   │
│ is_active       │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│   YTAccount     │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ channel_name    │
│ channel_id      │
│ client_id       │  ◄── User credentials
│ client_secret   │  ◄── User credentials
│ access_token    │
│ refresh_token   │
│ token_expiry    │
│ is_active       │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│      Video      │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │◄────────┐
│ title           │         │
│ description     │         │
│ video_file      │         │
│ duration        │         │
│ resolution      │         │
│ status          │         │
│ progress        │         │
│ shorts_total    │         │
│ shorts_created  │         │
│ created_at      │         │
└────────┬────────┘         │
         │                  │
         │ 1:N              │
         ▼                  │
┌─────────────────┐         │
│      Short      │         │
├─────────────────┤         │
│ id (PK)         │         │
│ video_id (FK)   ├─────────┘
│ title           │
│ description     │
│ short_file      │
│ thumbnail       │
│ start_time      │
│ duration        │
│ order           │
│ upload_status   │
│ yt_video_id     │
│ yt_url          │
│ privacy_status  │
│ views           │
│ likes           │
│ comments        │
│ created_at      │
│ published_at    │
└─────────────────┘
```

### 4.2 Opisy modeli

#### Model: User
**Rozszerzenie Django AbstractUser**

| Pole | Typ | Opis |
|------|-----|------|
| `id` | AutoField | Primary key |
| `username` | CharField(150) | Nazwa użytkownika (unique) |
| `email` | EmailField | Email (unique) |
| `password` | CharField(128) | Haszowane hasło |
| `role` | ForeignKey(Role) | Relacja do roli użytkownika |
| `google_id` | CharField(255) | ID użytkownika Google (dla OAuth) |
| `google_email` | EmailField | Email Google |
| `google_picture` | URLField | Avatar URL |
| `auth_provider` | CharField(20) | 'local' lub 'google' |
| `email_verified` | BooleanField | Czy email zweryfikowany |
| `is_active` | BooleanField | Czy konto aktywne |
| `created_at` | DateTimeField | Data utworzenia |
| `updated_at` | DateTimeField | Data aktualizacji |

**Metody:**
- `has_role(role_symbol)`: Sprawdza rolę użytkownika
- `is_moderator()`: Czy user jest moderatorem/adminem
- `is_admin_user()`: Czy user jest adminem

#### Model: Role
**Określa uprawnienia użytkownika**

| Pole | Typ | Opis |
|------|-----|------|
| `id` | AutoField | Primary key |
| `name` | CharField(255) | Nazwa roli (np. "Administrator") |
| `symbol` | CharField(20) | Symbol ('user', 'moderator', 'admin') |

**Dostępne role:**
- `user`: Zwykły użytkownik (upload, publikacja)
- `moderator`: Moderator (zarządzanie użytkownikami typu 'user')
- `admin`: Administrator (pełne uprawnienia)

#### Model: YTAccount
**Przechowuje credentials YouTube dostarczone przez użytkownika**

| Pole | Typ | Opis |
|------|-----|------|
| `id` | AutoField | Primary key |
| `user` | ForeignKey(User) | Powiązany użytkownik |
| `channel_name` | CharField(100) | Nazwa kanału YouTube |
| `channel_id` | CharField(100) | ID kanału |
| `client_id` | CharField(500) | Client ID od użytkownika |
| `client_secret` | CharField(500) | Client Secret od użytkownika |
| `access_token` | TextField | Token OAuth |
| `refresh_token` | TextField | Refresh token |
| `token_expiry` | DateTimeField | Data wygaśnięcia tokenu |
| `is_active` | BooleanField | Czy połączenie aktywne |
| `last_sync` | DateTimeField | Ostatnia synchronizacja |
| `created_at` | DateTimeField | Data połączenia |

**Metody:**
- `is_token_valid()`: Sprawdza ważność tokenu

#### Model: Video
**Źródłowe długie wideo**

| Pole | Typ | Opis |
|------|-----|------|
| `id` | AutoField | Primary key |
| `user` | ForeignKey(User) | Właściciel wideo |
| `title` | CharField(150) | Tytuł |
| `description` | TextField | Opis |
| `video_file` | FileField | Plik wideo |
| `duration` | IntegerField | Długość (sekundy) |
| `resolution` | CharField(20) | Rozdzielczość (np. "1920x1080") |
| `file_size` | BigIntegerField | Rozmiar w bajtach |
| `status` | CharField(20) | 'uploaded', 'processing', 'completed', 'failed' |
| `processing_progress` | IntegerField | Postęp (0-100%) |
| `processing_message` | CharField(255) | Wiadomość statusu |
| `shorts_total` | IntegerField | Planowana liczba shortów |
| `shorts_created` | IntegerField | Utworzone shorty |
| `target_duration` | IntegerField | Docelowa długość shorta (15-180s) |
| `max_shorts_count` | IntegerField | Max liczba shortów (1-50) |
| `created_at` | DateTimeField | Data utworzenia |
| `updated_at` | DateTimeField | Data aktualizacji |

**Metody:**
- `get_shorts_count()`: Zwraca liczbę wygenerowanych shortów

#### Model: Short
**YouTube Short wygenerowany z Video**

| Pole | Typ | Opis |
|------|-----|------|
| `id` | AutoField | Primary key |
| `video` | ForeignKey(Video) | Źródłowe wideo |
| `title` | CharField(100) | Tytuł (max 100 znaków) |
| `description` | TextField | Opis + tagi |
| `short_file` | FileField | Plik shorta |
| `thumbnail` | ImageField | Miniaturka (opcjonalne) |
| `start_time` | FloatField | Początek w źródłowym wideo |
| `duration` | IntegerField | Długość shorta (sekundy) |
| `order` | IntegerField | Kolejność |
| `upload_status` | CharField(20) | 'pending', 'uploading', 'published', 'failed', 'scheduled' |
| `yt_video_id` | CharField(255) | ID wideo na YouTube |
| `yt_url` | CharField(255) | Link do YouTube |
| `privacy_status` | CharField(20) | 'public', 'unlisted', 'private' |
| `scheduled_at` | DateTimeField | Zaplanowana publikacja |
| `made_for_kids` | BooleanField | Czy dla dzieci |
| `views` | IntegerField | Wyświetlenia |
| `likes` | IntegerField | Polubienia |
| `comments` | IntegerField | Komentarze |
| `created_at` | DateTimeField | Data utworzenia |
| `updated_at` | DateTimeField | Data aktualizacji |
| `published_at` | DateTimeField | Data publikacji |

**Metody:**
- `is_published()`: Czy short jest opublikowany
- `can_publish()`: Czy można publikować

---

## 5. Moduły aplikacji

### 5.1 Moduł: Authentication (`views.py`)

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

### 5.2 Moduł: Video Processing (`video_processing.py`)

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
    Główna metoda - dzieli wideo na shorty
    
    Args:
        crop_mode: 'center', 'smart', 'top'
    
    Process:
        1. Analiza wideo (ffprobe)
        2. Obliczenie liczby shortów
        3. Tworzenie segmentów (ffmpeg)
        4. Zapisywanie w bazie (Short objects)
        5. Generowanie miniatur
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

### 5.3 Moduł: YouTube Integration (`youtube_service.py`)

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

### 5.4 Moduł: User Management (`views.py`)

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

### 5.5 Moduł: Dashboard (`views.py`)

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

## 6. API i integracje

### 6.1 Google OAuth 2.0 (Logowanie)

#### Credentials:
```python
# W .env file
GOOGLE_LOGIN_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_LOGIN_CLIENT_SECRET=your-client-secret
```

#### Redirect URI:
```
http://localhost:8000/auth/google/callback/
```

#### Scopes:
```python
scopes = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]
```

### 6.2 YouTube Data API v3 (Publikacja)

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

### 6.3 FFmpeg Integration

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

### 6.4 Internal API Endpoints

#### GET `/api/video/<pk>/progress/`
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

**Użycie:** Polling z JavaScript do live update progress bar.

---

## 7. Bezpieczeństwo

### 7.1 Autentykacja i Autoryzacja

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

### 7.2 OAuth Security

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

### 7.3 Walidacja danych

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

### 7.4 File Upload Security

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

### 7.5 Secrets Management

#### Zmienne środowiskowe (.env):
```bash
SECRET_KEY=django-secret-key-here
DEBUG=False
GOOGLE_LOGIN_CLIENT_ID=...
GOOGLE_LOGIN_CLIENT_SECRET=...
DATABASE_URL=postgresql://...
```

**Nigdy nie commituj `.env` do Git!**

```gitignore
.env
*.env
client_secrets.json
```

---

## 8. Instalacja i konfiguracja

### 8.1 Wymagania systemowe

- **Python**: 3.8+
- **FFmpeg**: 4.4+
- **PostgreSQL**: 14+ (prod) lub SQLite (dev)
- **System operacyjny**: Windows, Linux, macOS

### 8.2 Instalacja krok po kroku

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
echo "GOOGLE_LOGIN_CLIENT_ID=your-client-id" >> .env
echo "GOOGLE_LOGIN_CLIENT_SECRET=your-client-secret" >> .env
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

### 8.3 Konfiguracja YouTube API (dla użytkowników)

**Każdy użytkownik musi:**
1. Utworzyć własny projekt w Google Cloud Console
2. Włączyć YouTube Data API v3
3. Utworzyć OAuth 2.0 Client ID
4. Redirect URI: `http://localhost:8000/youtube/oauth/callback/`
5. W aplikacji: Połącz YouTube → Wklej Client ID i Secret

Zobacz: `GOOGLE_API_SETUP.md`

---

## 9. Deployment

### 9.1 Produkcyjne ustawienia Django

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

### 9.2 Baza danych - PostgreSQL

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

### 9.3 Serwer WSGI (Gunicorn)

```bash
pip install gunicorn
```

```bash
# Uruchomienie
gunicorn app.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 9.4 Reverse Proxy (Nginx)

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

### 9.5 SSL/TLS (Certbot)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 9.6 Background Tasks (Celery - opcjonalnie)

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

## 10. Testy i monitoring

### 10.1 Unit Tests

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

### 10.2 Logging

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

### 10.3 Monitoring

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

### 10.4 Performance Monitoring

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

## 12. Dalszy rozwój

### 12.1 Planowane funkcje
- [ ] Celery dla background tasks
- [ ] Redis caching
- [ ] Batch upload (wiele shortów naraz)
- [ ] Planowanie publikacji (scheduler)
- [ ] Analytics dashboard (wykresy, statystyki)
- [ ] Webhook notifications (Discord, Slack)
- [ ] AI-powered thumbnail generation
- [ ] Smart cropping (face detection)
- [ ] Multi-language support (i18n)
- [ ] Mobile app (React Native)

### 12.2 Optymalizacje
- [ ] Database indexes
- [ ] Query optimization (N+1 problem)
- [ ] CDN dla media files
- [ ] Image optimization (WebP)
- [ ] Lazy loading
- [ ] Service workers (PWA)

---

## 13. Dokumentacja dla developerów

### 13.1 Code Style

#### PEP 8 Compliance
```python
# Używaj 4 spacji (nie tabulatorów)
# Maksymalna długość linii: 79 znaków
# Docstringi dla funkcji i klas

def example_function(param1, param2):
    """
    Krótki opis funkcji.
    
    Args:
        param1: Opis parametru 1
        param2: Opis parametru 2
    
    Returns:
        Opis zwracanej wartości
    """
    pass
```

#### Django Best Practices
```python
# Fat models, thin views
# Logika biznesowa w modelach lub serwisach
# Widoki tylko routing i rendering

# Dobra praktyka:
class Video(models.Model):
    def get_shorts_count(self):
        return self.shorts.count()

# Zła praktyka:
def video_detail(request, pk):
    video = Video.objects.get(pk=pk)
    shorts_count = Short.objects.filter(video=video).count()  # Niepotrzebne query
```

### 13.2 Git Workflow

```bash
# Feature branch
git checkout -b feature/new-feature

# Commit messages (Conventional Commits)
git commit -m "feat: Add batch upload feature"
git commit -m "fix: Fix YouTube OAuth callback"
git commit -m "docs: Update README"

# Push i Pull Request
git push origin feature/new-feature
```

### 13.3 Database Migrations

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
**Wersja:** 2.0  
**Data:** 2025-11-23

---

## 15. Kontakt i wsparcie

**GitHub:** https://github.com/dawid-gulczynski/YoutubeUploaderApp  
**Issues:** https://github.com/dawid-gulczynski/YoutubeUploaderApp/issues  

---

**Koniec dokumentacji technicznej**
