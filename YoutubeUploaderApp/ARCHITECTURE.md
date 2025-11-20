# 🏗️ Architektura Aplikacji YouTube Uploader

## 📋 Przegląd

Ta aplikacja działa jako **serwer** (backend), który umożliwia użytkownikom:
1. **Logowanie** przez Google OAuth lub tradycyjnie (email/hasło)
2. **Przetwarzanie wideo** - cięcie długich filmów na YouTube Shorts
3. **Publikację** - automatyczny upload shortów na YouTube w imieniu użytkownika

## 🔐 Dwa rodzaje autoryzacji

### 1. Logowanie użytkownika (django-allauth)
**Cel:** Autoryzacja użytkownika do aplikacji serwerowej

**Metody logowania:**
- ✅ Email + hasło (tradycyjnie)
- ✅ Google OAuth (logowanie przez Google)

**Używane credentials:**
- Server-side Google OAuth credentials (GOOGLE_LOGIN_CLIENT_ID, GOOGLE_LOGIN_CLIENT_SECRET)
- Te credentials są ustawione w `.env` na serwerze
- Służą tylko do weryfikacji tożsamości użytkownika

**Scopes:** `profile`, `email` (minimalne uprawnienia)

### 2. Połączenie z YouTube API (User Credentials)
**Cel:** Dostęp do YouTube API użytkownika do publikacji treści

**Jak działa:**
1. Użytkownik tworzy własny Google Cloud Project
2. Włącza YouTube Data API v3
3. Tworzy OAuth 2.0 Client ID
4. Dostarcza Client ID i Client Secret w aplikacji
5. Autoryzuje aplikację do uploadu na jego kanał

**Używane credentials:**
- User-provided credentials (Client ID i Client Secret od użytkownika)
- Przechowywane w bazie danych (model `YTAccount`)
- Każdy użytkownik ma swoje własne credentials

**Scopes:** 
- `youtube.upload`
- `youtube.readonly`
- `youtube.force-ssl`

## 🔄 Przepływ działania

```
┌─────────────────┐
│  Użytkownik     │
└────────┬────────┘
         │
         ├─── [KROK 1] Rejestracja/Logowanie
         │    ├─ Opcja A: Email + hasło
         │    └─ Opcja B: Google OAuth (server credentials)
         │
         ├─── [KROK 2] Upload wideo do przetworzenia
         │    └─ Wideo zapisywane na serwerze
         │
         ├─── [KROK 3] Przetwarzanie (FFmpeg)
         │    └─ Cięcie na YouTube Shorts
         │
         ├─── [KROK 4] Połączenie z YouTube (user credentials)
         │    ├─ Użytkownik dostarcza swoje Client ID/Secret
         │    └─ OAuth flow z użyciem credentials użytkownika
         │
         └─── [KROK 5] Publikacja
              └─ Upload na YouTube używając API użytkownika
```

## 📊 Modele bazy danych

### User (Użytkownik aplikacji)
```python
- username
- email
- password (hashed)
- auth_provider: 'local' lub 'google'
- google_id (jeśli zalogowany przez Google)
- role: User/Moderator/Admin
```

### YTAccount (Połączenie YouTube)
```python
- user (ForeignKey)
- channel_name
- channel_id
- client_id (od użytkownika!)
- client_secret (od użytkownika!)
- access_token (wygenerowany)
- refresh_token (wygenerowany)
- token_expiry
```

### Video (Źródłowe wideo)
```python
- user (ForeignKey)
- title, description
- video_file
- status: uploaded/processing/completed/failed
- duration, resolution
```

### Short (Wygenerowany short)
```python
- video (ForeignKey)
- title, description
- short_file
- upload_status: pending/uploading/published/failed
- yt_video_id (po publikacji)
- yt_url
```

## 🔒 Bezpieczeństwo

### Server Credentials (Google OAuth dla logowania)
- Przechowywane w zmiennych środowiskowych (`.env`)
- Nie są widoczne dla użytkownika
- Używane tylko do weryfikacji tożsamości

### User Credentials (YouTube API)
- Dostarczone przez użytkownika
- Przechowywane w bazie (zaszyfrowane w produkcji!)
- Każdy użytkownik ma własne
- Pełna kontrola użytkownika

### Tokeny OAuth
- Access token: krótkotrwały (1 godzina)
- Refresh token: długotrwały (możliwość odświeżenia)
- Automatyczne odświeżanie tokenów

## 🚀 Instalacja i konfiguracja

### 1. Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### 2. Utwórz plik `.env` w katalogu głównym
```env
# Django
SECRET_KEY=your-django-secret-key
DEBUG=True

# Google OAuth dla LOGOWANIA (server credentials)
GOOGLE_LOGIN_CLIENT_ID=your-google-login-client-id
GOOGLE_LOGIN_CLIENT_SECRET=your-google-login-secret

# Database
DATABASE_URL=sqlite:///db.sqlite3
```

### 3. Migracje
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py init_roles
```

### 4. Uruchom serwer
```bash
python manage.py runserver
```

### 5. Konfiguracja Google Cloud Console (dla logowania)

**Dla deweloperów serwera (raz):**
1. Utwórz projekt w [Google Cloud Console](https://console.cloud.google.com)
2. Włącz "Google+ API"
3. Utwórz OAuth 2.0 Client ID (Web application)
4. Redirect URI: `http://localhost:8000/accounts/google/login/callback/`
5. Zapisz Client ID i Secret w `.env`

**Dla użytkowników aplikacji (każdy osobno):**
1. Użytkownik tworzy własny Google Cloud Project
2. Włącza YouTube Data API v3
3. Tworzy OAuth 2.0 Client ID
4. Redirect URI: `http://localhost:8000/youtube/oauth/callback/`
5. Dostarcza Client ID i Secret w aplikacji

## 📁 Struktura projektu

```
YoutubeUploaderApp/
├── app/                      # Główna konfiguracja Django
│   ├── settings.py          # Ustawienia (INSTALLED_APPS, allauth)
│   └── urls.py              # Routing główny
│
├── uploader/                 # Aplikacja główna
│   ├── models.py            # User, YTAccount, Video, Short
│   ├── views.py             # Logika biznesowa
│   ├── youtube_service.py   # Integracja z YouTube API
│   └── templates/           # Szablony HTML
│
├── media/                    # Przesłane pliki
│   ├── videos/              # Źródłowe wideo
│   └── shorts/              # Wygenerowane shorty
│
├── .env                      # Zmienne środowiskowe (NIE COMMITUJ!)
├── requirements.txt          # Zależności Python
└── README.md                # Dokumentacja użytkownika
```

## 🎯 Kluczowe różnice

| Aspekt | Stara architektura | Nowa architektura |
|--------|-------------------|-------------------|
| **Logowanie** | Tylko email/hasło | Email/hasło + Google OAuth |
| **YouTube Credentials** | Server-side (jeden dla wszystkich) | User-provided (każdy swoje) |
| **client_secrets.json** | Na serwerze | Nie potrzebny! |
| **Bezpieczeństwo** | Wszystkie requesty przez server token | Każdy użytkownik własny token |
| **Limity API** | Współdzielone (problem!) | Indywidualne (każdy ma swoje) |
| **Kontrola** | Serwer ma pełen dostęp | Użytkownik kontroluje dostęp |

## 🔧 Kluczowe zmiany w kodzie

### settings.py
```python
# Dodano django-allauth
INSTALLED_APPS += [
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

# Konfiguracja Google OAuth dla logowania
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_LOGIN_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_LOGIN_CLIENT_SECRET'),
        }
    }
}
```

### models.py - User
```python
class User(AbstractUser):
    auth_provider = models.CharField(
        max_length=20, 
        default='local',
        choices=[('local', 'Email/Password'), ('google', 'Google OAuth')]
    )
    google_id = models.CharField(max_length=255, unique=True, null=True)
```

### models.py - YTAccount
```python
class YTAccount(models.Model):
    # Credentials od użytkownika!
    client_id = models.CharField(max_length=500)
    client_secret = models.CharField(max_length=500)
    
    # Tokeny OAuth
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField()
```

### views.py - youtube_oauth
```python
# Użytkownik dostarcza credentials w formularzu
client_id = request.POST.get('client_id')
client_secret = request.POST.get('client_secret')

# Tworzymy flow z jego credentials
flow = Flow.from_client_config(
    {"web": {
        "client_id": client_id,
        "client_secret": client_secret,
        ...
    }},
    scopes=[...]
)
```

## 🎓 Dla deweloperów

### Testowanie lokalnie
1. Użyj ngrok dla callback URL: `ngrok http 8000`
2. Zaktualizuj Redirect URI w Google Console
3. Testuj z prawdziwym Google OAuth

### Deployment
1. Ustaw `DEBUG=False` w produkcji
2. Użyj PostgreSQL zamiast SQLite
3. Włącz HTTPS (wymagane dla OAuth)
4. Zaszyfruj credentials w bazie (django-fernet-fields)

## 📝 TODO
- [ ] Dodać szyfrowanie credentials w bazie
- [ ] Implementować rate limiting
- [ ] Dodać 2FA dla bezpieczeństwa
- [ ] Cache dla tokenów YouTube
- [ ] Webhook notifications dla uploadów
- [ ] Bulk operations (upload wielu shortów)

---

**Autor:** Dawid Gulczyński, Kajetan Szlenzak  
**Wersja:** 2.0  
**Data:** 2025-01-20
