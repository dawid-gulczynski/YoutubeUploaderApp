# YouTube Video Uploader - Django App

## 📌 Opis projektu

Aplikacja webowa Django działająca jako **serwer**, która umożliwia:
- 🔐 **Logowanie** przez Google OAuth lub tradycyjnie (email/hasło)
- 📹 **Przetwarzanie wideo** - automatyczne cięcie długich filmów na YouTube Shorts
- 🚀 **Publikację** - upload shortów na YouTube w imieniu użytkownika
- 📊 **Zarządzanie** - harmonogram publikacji, edycja metadanych, analityka

## 🏗️ Architektura (Ważne!)

Ta aplikacja używa **dwuetapowego procesu autoryzacji**:

### 1️⃣ Logowanie użytkownika do serwera
- **Email + hasło** (tradycyjnie)
- **Google OAuth** (przez django-allauth)
- Server używa własnych Google OAuth credentials

### 2️⃣ Połączenie z YouTube API użytkownika
- Użytkownik **dostarcza własne** Google API credentials (Client ID + Secret)
- Każdy użytkownik ma **swoje własne** YouTube API quota
- Pełna kontrola nad dostępem do swojego kanału

> 💡 **Dlaczego tak?** Każdy użytkownik ma własne limity YouTube API (10,000 units/dzień), 
> więc nie dzielimy jednego konta API między wszystkich użytkowników!

📖 **Szczegóły:** Zobacz [ARCHITECTURE.md](ARCHITECTURE.md) dla pełnego opisu architektury.

## 🏗️ Struktura projektu Django

```
YoutubeUploaderApp/
├── app/                          # Główna konfiguracja projektu Django
│   ├── __init__.py
│   ├── settings.py              # Ustawienia projektu
│   ├── urls.py                  # Główny routing URL
│   ├── wsgi.py                  # WSGI config
│   └── asgi.py                  # ASGI config
│
├── uploader/                     # Główna aplikacja Django
│   ├── migrations/              # Migracje bazy danych
│   │   └── __init__.py
│   ├── static/uploader/         # Pliki statyczne (CSS, JS, obrazy)
│   │   └── css/
│   │       └── style.css        # Własne style CSS
│   ├── templates/uploader/      # Szablony HTML
│   │   ├── base.html           # Szablon bazowy
│   │   ├── home.html           # Strona główna
│   │   ├── upload_form.html    # Formularz uploadu
│   │   ├── video_list.html     # Lista wideo
│   │   └── video_detail.html   # Szczegóły wideo
│   ├── __init__.py
│   ├── admin.py                 # Konfiguracja panelu admina
│   ├── apps.py                  # Konfiguracja aplikacji
│   ├── forms.py                 # Formularze Django
│   ├── models.py                # Modele bazy danych
│   ├── urls.py                  # Routing URL aplikacji
│   ├── views.py                 # Widoki (logika biznesowa)
│   └── youtube_service.py       # Serwis YouTube API
│
├── media/                        # Folder na uploadowane pliki
│   └── videos/                  # Folder na pliki wideo
│
├── manage.py                     # Skrypt zarządzania Django
├── db.sqlite3                    # Baza danych SQLite
├── requirements.txt              # Zależności projektu
└── client_secrets.json          # Klucze API YouTube (DO DODANIA!)
```

## 🔧 Jak działa struktura Django?

### 1. **Models (models.py)** - Warstwa danych
- Definiuje strukturę bazy danych
- Model `Video` przechowuje informacje o filmach
- Django automatycznie tworzy tabele w bazie danych

### 2. **Views (views.py)** - Logika biznesowa
- `VideoListView` - wyświetla listę filmów
- `VideoUploadView` - obsługuje formularz uploadu
- `VideoDetailView` - pokazuje szczegóły filmu
- Widoki komunikują się z modelami i renderują szablony

### 3. **Templates (templates/)** - Warstwa prezentacji
- `base.html` - szablon bazowy z nawigacją
- Pozostałe szablony dziedziczą z base.html
- Używają Django Template Language ({% %} i {{ }})

### 4. **Forms (forms.py)** - Walidacja danych
- `VideoUploadForm` - formularz do uploadu wideo
- Automatyczna walidacja i wyświetlanie błędów

### 5. **URLs (urls.py)** - Routing
- Mapowanie URL-i na widoki
- Struktura: URL → View → Template

### 6. **Static & Media**
- `static/` - CSS, JS, obrazy (część kodu)
- `media/` - pliki uploadowane przez użytkowników

### 7. **Admin (admin.py)** - Panel administracyjny
- Automatyczny interfejs do zarządzania danymi
- Dostępny pod `/admin/`

## 🚀 Szybki Start (7 minut)

### 1. Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### 2. Skonfiguruj Google OAuth (dla logowania)
📖 **Szczegółowy poradnik:** [QUICKSTART.md](QUICKSTART.md) (tylko 7 minut!)

**W skrócie:**
1. Utwórz projekt w [Google Cloud Console](https://console.cloud.google.com)
2. Skonfiguruj OAuth Consent Screen
3. Utwórz OAuth Client ID (Web application)
4. Redirect URI: `http://localhost:8000/accounts/google/login/callback/`
5. Wklej Client ID i Secret do `.env`

### 3. Inicjalizuj bazę danych
```bash
python manage.py migrate
python manage.py init_roles
python manage.py setup_google_oauth
```

### 4. Uruchom serwer
```bash
python manage.py runserver
```

### 5. Testuj!
1. Otwórz: http://localhost:8000/login/
2. Kliknij **"Zaloguj przez Google"**
3. Wybierz konto Google
4. 🎉 Gotowe!

## 📱 Funkcjonalności

### Dla użytkowników:
✅ **Logowanie:**
- Rejestracja przez email/hasło
- Logowanie przez Google OAuth
- Zarządzanie profilem

✅ **Wideo:**
- Upload długich filmów
- Automatyczne cięcie na Shorts (FFmpeg)
- Podgląd wygenerowanych shortów
- Edycja metadanych (tytuł, opis, tagi)

✅ **YouTube Integration:**
- Połączenie własnego konta YouTube (user-provided credentials)
- Automatyczna publikacja shortów
- Harmonogram publikacji
- Status uploadu w czasie rzeczywistym

✅ **Dashboard:**
- Statystyki (liczba wideo, shortów, wyświetleń)
- Ostatnie aktywności
- Status przetwarzania wideo

### Dla administratorów:
✅ Panel administracyjny Django  
✅ Zarządzanie użytkownikami i rolami  
✅ Monitoring statusów uploadów  
✅ Logi systemowe  

## 🎯 Przepływ działania aplikacji

### Dla nowych użytkowników:
1. **Rejestracja/Logowanie** → Email+hasło lub Google OAuth
2. **Upload wideo** → Prześlij długi film do przetworzenia
3. **Przetwarzanie** → FFmpeg automatycznie tnie wideo na Shorts
4. **Połącz YouTube** → Dostarcz własne Google API credentials
5. **Publikuj** → Kliknij "Publikuj" na shortach
6. **Monitoruj** → Śledź status i statystyki

### Jak połączyć YouTube? (dla użytkownika)
1. Utwórz projekt w [Google Cloud Console](https://console.cloud.google.com)
2. Włącz **YouTube Data API v3**
3. Utwórz **OAuth 2.0 Client ID** (Web application)
4. Dodaj Redirect URI: `http://localhost:8000/youtube/oauth/callback/`
5. Skopiuj **Client ID** i **Client Secret**
6. W aplikacji: Ustawienia → Połącz YouTube → Wklej credentials
7. Autoryzuj dostęp do swojego kanału
8. Gotowe! Możesz publikować shorty

> 📖 **Szczegółowy poradnik:** [GOOGLE_API_SETUP.md](GOOGLE_API_SETUP.md)

## 🔐 Wymagane API & Credentials

### Dla serwera (raz, podczas deployment):
- **Google OAuth Client** (dla logowania użytkowników)
  - Scope: `profile`, `email`
  - Konfiguracja: `.env` → `GOOGLE_LOGIN_CLIENT_ID`, `GOOGLE_LOGIN_CLIENT_SECRET`

### Dla każdego użytkownika (osobno):
- **YouTube Data API v3** credentials (własny Google Cloud Project)
  - Scope: `youtube.upload`, `youtube.readonly`, `youtube.force-ssl`
  - Dostarczane przez użytkownika w aplikacji (Client ID + Secret)
  - Każdy użytkownik ma własne quota (10,000 units/dzień)

### FFmpeg (opcjonalnie, dla przetwarzania wideo):
- Instalacja: Zobacz [FFMPEG_INSTALL.md](FFMPEG_INSTALL.md)
- Bez FFmpeg aplikacja działa, ale nie tworzy shortów automatycznie

## 📚 Kluczowe koncepcje Django

### MVT Pattern (Model-View-Template)
- **Model**: Dane (models.py)
- **View**: Logika (views.py)
- **Template**: Prezentacja (HTML)

### ORM (Object-Relational Mapping)
Django automatycznie tłumaczy obiekty Pythona na zapytania SQL.

### Admin Panel
Gotowy interfejs administracyjny - wystarczy zarejestrować model.

### URL Routing
Czytelne URL-e dzięki wzorcom w `urls.py`.

## 🎨 Dostosowywanie

- **Style**: Edytuj `uploader/static/uploader/css/style.css`
- **Szablony**: Modyfikuj pliki w `uploader/templates/uploader/`
- **Model**: Zmień `uploader/models.py` i wykonaj migracje
- **Logika**: Rozbuduj `uploader/views.py`

## 📝 Kolejne kroki

1. ✅ Wykonaj migracje
2. ✅ Dodaj client_secrets.json
3. ✅ Uruchom serwer
4. ✅ Przetestuj upload filmu
5. 🔄 Dodaj więcej funkcji (np. edycja filmów, usuwanie)

---

**Autor**: Dawid Gulczyński, Kajetan Szlenzak 
**Framework**: Django 5.2.7  
**Język**: Python 3.x
