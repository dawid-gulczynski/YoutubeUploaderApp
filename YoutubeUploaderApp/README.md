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

## 🗄️ Struktura Bazy Danych

### **Tabele główne:**

#### 1. `uploader_user` - Użytkownicy
```sql
id              INTEGER PRIMARY KEY
username        VARCHAR(150) UNIQUE
email           VARCHAR(254) UNIQUE
password        VARCHAR(128)
first_name      VARCHAR(150)
last_name       VARCHAR(150)
role_id         INTEGER REFERENCES uploader_role(id)
google_id       VARCHAR(255) UNIQUE          -- Google OAuth ID
google_email    VARCHAR(254)                 -- Email z Google
google_picture  VARCHAR(200)                 -- URL avatara Google
auth_provider   VARCHAR(20)                  -- 'local' | 'google'
email_verified  BOOLEAN DEFAULT FALSE
is_staff        BOOLEAN DEFAULT FALSE
is_active       BOOLEAN DEFAULT TRUE
created_at      DATETIME
updated_at      DATETIME
```

#### 2. `uploader_role` - Role użytkowników
```sql
id      INTEGER PRIMARY KEY
name    VARCHAR(255)                     -- 'User' | 'Moderator' | 'Admin'
symbol  VARCHAR(20) UNIQUE               -- 'user' | 'moderator' | 'admin'
```

#### 3. `uploader_ytaccount` - Konta YouTube użytkowników
```sql
id              INTEGER PRIMARY KEY
user_id         INTEGER REFERENCES uploader_user(id)
channel_name    VARCHAR(100)
channel_id      VARCHAR(100)
client_id       VARCHAR(500)             -- User's Google Cloud OAuth Client ID
client_secret   VARCHAR(500)             -- User's Google Cloud OAuth Secret
access_token    TEXT
refresh_token   TEXT
token_expiry    DATETIME
is_active       BOOLEAN DEFAULT TRUE
last_sync       DATETIME
created_at      DATETIME
updated_at      DATETIME
```

#### 4. `uploader_video` - Źródłowe długie wideo
```sql
id                    INTEGER PRIMARY KEY
user_id               INTEGER REFERENCES uploader_user(id)
title                 VARCHAR(150)
description           TEXT
video_file            VARCHAR(100)       -- Ścieżka do pliku
duration              INTEGER            -- Sekundy
resolution            VARCHAR(20)        -- np. '1920x1080'
file_size             BIGINT             -- Bajty
status                VARCHAR(20)        -- 'uploaded' | 'processing' | 'completed' | 'failed'
processing_progress   INTEGER DEFAULT 0  -- 0-100%
processing_message    VARCHAR(255)
shorts_total          INTEGER DEFAULT 0  -- Planowana liczba shortów
shorts_created        INTEGER DEFAULT 0  -- Utworzone shorty
target_duration       INTEGER DEFAULT 60 -- Długość jednego shorta (sek)
max_shorts_count      INTEGER DEFAULT 10 -- Max liczba shortów do utworzenia
created_at            DATETIME
updated_at            DATETIME
```

#### 5. `uploader_short` - YouTube Shorts
```sql
id                      INTEGER PRIMARY KEY
video_id                INTEGER REFERENCES uploader_video(id)
title                   VARCHAR(100)
description             TEXT
tags                    VARCHAR(500)              -- Tagi oddzielone spacjami
short_file              VARCHAR(100)              -- Ścieżka do pliku
thumbnail               VARCHAR(100)              -- Ścieżka do miniaturki
start_time              FLOAT                     -- Start w źródłowym wideo (sek)
duration                INTEGER                   -- Długość shorta (sek)
order                   INTEGER DEFAULT 0         -- Kolejność w serii

-- STATUS I HARMONOGRAM
upload_status           VARCHAR(20)               -- 'pending' | 'scheduled' | 'uploading' | 'published' | 'failed'
scheduled_at            DATETIME                  -- Kiedy opublikować
published_at            DATETIME                  -- Kiedy faktycznie opublikowano

-- YOUTUBE DATA
yt_video_id             VARCHAR(255)              -- ID wideo na YouTube
yt_url                  VARCHAR(255)              -- Link do YouTube
privacy_status          VARCHAR(20)               -- 'public' | 'unlisted' | 'private'
made_for_kids           BOOLEAN DEFAULT FALSE

-- STATYSTYKI (z YouTube Analytics)
views                   INTEGER DEFAULT 0
likes                   INTEGER DEFAULT 0
comments                INTEGER DEFAULT 0
shares                  INTEGER DEFAULT 0
watch_time_minutes      FLOAT DEFAULT 0
average_view_duration   FLOAT DEFAULT 0           -- Sekundy
click_through_rate      FLOAT DEFAULT 0           -- Procent
engagement_rate         FLOAT DEFAULT 0           -- Procent
retention_rate          FLOAT DEFAULT 0           -- Procent

-- METADATA (auto-obliczane)
title_length            INTEGER DEFAULT 0
description_length      INTEGER DEFAULT 0
tags_count              INTEGER DEFAULT 0         -- Liczba tagów z pola 'tags'
hashtags_count          INTEGER DEFAULT 0         -- Liczba #hashtagów w opisie

-- DATY
created_at              DATETIME
updated_at              DATETIME
last_analytics_update   DATETIME                  -- Ostatnia aktualizacja statystyk
```

#### 6. `uploader_shortsuggestion` - Sugestie optymalizacji
```sql
id              INTEGER PRIMARY KEY
short_id        INTEGER REFERENCES uploader_short(id)
category        VARCHAR(20)        -- 'title' | 'description' | 'thumbnail' | 'timing' | 'content' | 'engagement'
priority        VARCHAR(10)        -- 'low' | 'medium' | 'high' | 'critical'
title           VARCHAR(200)       -- Tytuł sugestii
description     TEXT               -- Szczegółowy opis
metric_name     VARCHAR(50)        -- Nazwa metryki która wywołała sugestię
current_value   FLOAT              -- Aktualna wartość
target_value    FLOAT              -- Wartość docelowa
is_resolved     BOOLEAN DEFAULT FALSE
created_at      DATETIME
```

### **Relacje między tabelami:**

```
uploader_user (1) ──────< (∞) uploader_video
    │
    │
    └──────< (∞) uploader_ytaccount
    
uploader_video (1) ──────< (∞) uploader_short

uploader_short (1) ──────< (∞) uploader_shortsuggestion

uploader_role (1) ──────< (∞) uploader_user
```

### **Kluczowe indeksy dla wydajności:**

```sql
-- Indeksy na user_id dla szybkich zapytań użytkownika
CREATE INDEX idx_video_user ON uploader_video(user_id);
CREATE INDEX idx_ytaccount_user ON uploader_ytaccount(user_id);

-- Indeksy na statusy dla filtrowania
CREATE INDEX idx_video_status ON uploader_video(status);
CREATE INDEX idx_short_status ON uploader_short(upload_status);

-- Indeks na scheduled_at dla cron job
CREATE INDEX idx_short_scheduled ON uploader_short(scheduled_at, upload_status);

-- Indeks na video_id dla shortów
CREATE INDEX idx_short_video ON uploader_short(video_id);

-- Indeks na sugestie
CREATE INDEX idx_suggestion_short ON uploader_shortsuggestion(short_id, is_resolved);
```

### **Przykładowe zapytania:**

```sql
-- Znajdź shorty gotowe do publikacji (używane przez cron)
SELECT * FROM uploader_short 
WHERE upload_status = 'scheduled' 
AND scheduled_at <= datetime('now');

-- Statystyki użytkownika
SELECT 
    COUNT(DISTINCT v.id) as total_videos,
    COUNT(s.id) as total_shorts,
    SUM(s.views) as total_views
FROM uploader_video v
LEFT JOIN uploader_short s ON s.video_id = v.id
WHERE v.user_id = ?;

-- Najlepsze shorty użytkownika (po engagement)
SELECT id, title, views, likes, engagement_rate
FROM uploader_short
WHERE video_id IN (SELECT id FROM uploader_video WHERE user_id = ?)
AND upload_status = 'published'
ORDER BY engagement_rate DESC
LIMIT 10;

-- Sugestie krytyczne dla użytkownika
SELECT ss.*, s.title
FROM uploader_shortsuggestion ss
JOIN uploader_short s ON s.id = ss.short_id
JOIN uploader_video v ON v.id = s.video_id
WHERE v.user_id = ?
AND ss.priority = 'critical'
AND ss.is_resolved = 0;
```

### **⚡ Triggery bazodanowe:**

Aplikacja wykorzystuje **3 automatyczne triggery** do zarządzania danymi:

#### **1. Automatyczna aktualizacja licznika shortów w Video**
```sql
-- Trigger: update_video_shorts_count_on_insert
-- Trigger: update_video_shorts_count_on_delete

-- Co robi: Automatycznie aktualizuje pole 'shorts_created' w tabeli uploader_video
--          za każdym razem gdy short jest dodawany lub usuwany

-- Przykład: Gdy utworzysz nowy short z wideo o ID=5
INSERT INTO uploader_short (video_id, title, ...) VALUES (5, 'Mój Short', ...);
-- uploader_video.shorts_created dla video_id=5 automatycznie wzrośnie o 1

-- Gdy usuniesz short
DELETE FROM uploader_short WHERE id = 123;
-- uploader_video.shorts_created automatycznie zmniejszy się o 1
```

**Korzyści:**
- ✅ Zawsze aktualna liczba shortów bez ręcznego przeliczania
- ✅ Brak potrzeby dodatkowych zapytań COUNT(*) w aplikacji
- ✅ Gwarantowana spójność danych

#### **2. Automatyczne ustawianie daty publikacji**
```sql
-- Trigger: set_published_at_on_status_change

-- Co robi: Automatycznie ustawia pole 'published_at' na aktualną datę/czas
--          gdy upload_status zmienia się na 'published'

-- Przykład: Gdy short zostanie opublikowany
UPDATE uploader_short 
SET upload_status = 'published' 
WHERE id = 456;
-- Pole 'published_at' automatycznie ustawia się na datetime('now')
```

**Korzyści:**
- ✅ Precyzyjna data publikacji bez dodatkowego kodu
- ✅ Niemożliwe zapomnienie o ustawieniu daty
- ✅ Jedna źródło prawdy o czasie publikacji

#### **3. Automatyczny timestamp aktualizacji analityki**
```sql
-- Trigger: update_analytics_timestamp

-- Co robi: Automatycznie aktualizuje pole 'last_analytics_update' gdy zmienią się
--          jakiekolwiek statystyki (views, likes, comments, shares, engagement_rate, etc.)

-- Przykład: Gdy zaktualizujesz statystyki z YouTube Analytics
UPDATE uploader_short 
SET views = 1500, likes = 120, engagement_rate = 8.5 
WHERE id = 789;
-- Pole 'last_analytics_update' automatycznie ustawia się na datetime('now')
```

**Korzyści:**
- ✅ Wiesz dokładnie kiedy ostatnio pobrano statystyki z YouTube
- ✅ Możliwość optymalizacji - nie pobieraj danych jeśli były świeżo zaktualizowane
- ✅ Automatyczne śledzenie zmian bez dodatkowego kodu

**🔧 Zarządzanie triggerami:**

```bash
# Zastosuj triggery (automatycznie podczas migracji)
python manage.py migrate uploader

# Sprawdź listę triggerów w bazie
sqlite3 db.sqlite3 "SELECT name FROM sqlite_master WHERE type='trigger';"

# Usuń wszystkie triggery (rollback migracji)
python manage.py migrate uploader 0006

# Ponownie zastosuj triggery
python manage.py migrate uploader
```

**⚠️ Uwaga:** Triggery są specyficzne dla SQLite. Jeśli zmienisz bazę na PostgreSQL/MySQL, system Django automatycznie dostosuje składnię triggerów podczas migracji.

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
