# YouTube Video Uploader - Django App

## 📌 Opis projektu

Aplikacja webowa Django do uploadowania filmów na YouTube za pomocą YouTube Data API v3. 
Projekt zawiera pełną strukturę Django z nowoczesnym interfejsem użytkownika opartym na Bootstrap 5.

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

## 🚀 Instalacja i uruchomienie

### 1. Zainstaluj zależności
```bash
pip install -r requirements.txt
```

### 2. Dodaj plik client_secrets.json
Umieść plik `client_secrets.json` z Google Cloud Console w głównym katalogu projektu.

### 3. Wykonaj migracje bazy danych
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Utwórz superusera (opcjonalnie)
```bash
python manage.py createsuperuser
```

### 5. Uruchom serwer deweloperski
```bash
python manage.py runserver
```

Aplikacja będzie dostępna pod adresem: `http://127.0.0.1:8000/`

## 📱 Funkcjonalności

✅ Upload filmów na YouTube  
✅ Formularz z tytułem, opisem i słowami kluczowymi  
✅ Lista wszystkich uploadowanych filmów  
✅ Podgląd szczegółów każdego filmu  
✅ Automatyczne śledzenie statusu uploadu  
✅ Możliwość ponowienia uploadu w przypadku błędu  
✅ Panel administracyjny Django  
✅ Responsywny interfejs (Bootstrap 5)  

## 🎯 Przepływ działania aplikacji

1. **Użytkownik wypełnia formularz** (`upload_form.html`)
2. **Django waliduje dane** (`forms.py`)
3. **Dane zapisywane do bazy** (`models.py`)
4. **Rozpoczyna się upload** (`youtube_service.py`)
5. **Status aktualizowany w tle** (threading)
6. **Użytkownik widzi wynik** (`video_list.html`)

## 🔐 Wymagane API

Musisz mieć:
- Google Cloud Project
- YouTube Data API v3 włączone
- OAuth 2.0 Client ID (Desktop app)
- Plik `client_secrets.json`

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
