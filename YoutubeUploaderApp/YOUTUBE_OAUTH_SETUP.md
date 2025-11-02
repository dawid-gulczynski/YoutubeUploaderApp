# 🚀 YouTube Shorts Uploader - Quick Start Guide

## YouTube OAuth Integration - Szybki Start

### ✅ Co zostało zaimplementowane:

1. **Pełny OAuth 2.0 flow**
   - Autoryzacja przez Google
   - Automatyczne odświeżanie tokenów
   - Bezpieczne przechowywanie credentials

2. **Upload shortów na YouTube**
   - Publikacja jednym kliknięciem
   - Wsparcie dla harmonogramu publikacji
   - Tracking statusu uploadu

3. **Zarządzanie kontem**
   - Połączenie/rozłączenie konta YouTube
   - Podgląd informacji o kanale
   - Automatyczne odświeżanie tokenów

---

## 📋 Konfiguracja (3 kroki)

### 1. Utwórz Google Cloud Project

Szczegółowa instrukcja w pliku: **`GOOGLE_API_SETUP.md`**

Krótko:
1. Przejdź do [Google Cloud Console](https://console.cloud.google.com/)
2. Utwórz nowy projekt
3. Włącz **YouTube Data API v3**
4. Skonfiguruj **OAuth consent screen**
5. Utwórz **OAuth 2.0 Client ID** (Web application)
6. Pobierz credentials jako JSON

### 2. Skonfiguruj credentials

Skopiuj pobrany plik do głównego katalogu projektu i zmień nazwę na `client_secrets.json`:

```json
{
  "web": {
    "client_id": "TWOJ_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "twoj-projekt-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "TWOJ_CLIENT_SECRET",
    "redirect_uris": [
      "http://127.0.0.1:8000/youtube/oauth/callback/"
    ]
  }
}
```

**WAŻNE**: Plik `client_secrets.json` jest automatycznie ignorowany przez git (.gitignore)

### 3. Testuj OAuth

1. Uruchom serwer:
   ```bash
   python manage.py runserver
   ```

2. Zaloguj się do aplikacji

3. Przejdź do: **Dashboard** → **Połącz konto YouTube** (`http://127.0.0.1:8000/youtube/connect/`)

4. Kliknij **"Połącz z Google/YouTube"**

5. Zaloguj się do Google (użyj konta dodanego jako test user w Google Console)

6. Zaakceptuj uprawnienia

7. ✅ Gotowe! Konto połączone

---

## 🎬 Publikacja shortów

### Jak opublikować short na YouTube:

1. **Wgraj wideo** → Automatyczne cięcie na shorty
2. Przejdź do **szczegółów shorta**
3. Kliknij **"Publikuj na YouTube"**
4. Poczekaj na upload (progress bar w tle)
5. ✅ Short opublikowany! Link do YouTube w szczegółach

### Co się dzieje podczas publikacji:

- Status shorta zmienia się na "Uploadowanie"
- Wideo jest uploadowane na YouTube
- Metadata (tytuł, opis, tagi) jest dodawana
- Status zmienia się na "Opublikowany"
- Zapisywany jest link do wideo na YouTube

---

## 🔐 Bezpieczeństwo

### ✅ Dobre praktyki zastosowane:

- Tokeny przechowywane w bazie danych (nie w kodzie)
- `client_secrets.json` w .gitignore
- Automatyczne odświeżanie tokenów
- OAuth 2.0 standard (Google)

### ❌ Nigdy nie commituj:

- `client_secrets.json`
- Tokenów dostępu
- API keys w kodzie

---

## 🐛 Rozwiązywanie problemów

### "Brak pliku client_secrets.json"
**Rozwiązanie**: Skopiuj plik credentials z Google Cloud Console do głównego katalogu projektu jako `client_secrets.json`

### "Access blocked: This app's request is invalid"
**Rozwiązanie**: Sprawdź **Authorized redirect URIs** w Google Console - musi być dokładnie `http://127.0.0.1:8000/youtube/oauth/callback/`

### "403 Forbidden" podczas uploadu
**Rozwiązanie**: 
- Sprawdź czy YouTube Data API v3 jest włączone
- Kliknij "Odśwież token" w ustawieniach konta YouTube

### "Quota exceeded"
**Rozwiązanie**: YouTube Data API ma limit 10,000 units/dzień. Upload wideo = 1600 units. Poczekaj do północy PST lub wystąp o zwiększenie limitu.

---

## 📊 Limity API

### YouTube Data API v3 Quota:

- **Domyślny limit**: 10,000 units/dzień (za darmo)
- **Upload wideo**: 1600 units
- **Maksymalnie**: ~6 uploadów/dzień

### Jak zwiększyć limit:

1. Google Cloud Console → YouTube Data API v3 → Quotas
2. Kliknij "ALL QUOTAS" → "Queries per day"
3. Kliknij edycja → "APPLY FOR HIGHER QUOTA"
4. Wypełnij formularz

---

## 📁 Struktura plików

```
YoutubeUploaderApp/
├── client_secrets.json          # Google API credentials (NIE commituj!)
├── client_secrets.json.example  # Szablon konfiguracji
├── GOOGLE_API_SETUP.md          # Szczegółowa instrukcja setup Google API
├── YOUTUBE_OAUTH_SETUP.md       # Ten plik - quick start
├── uploader/
│   ├── views.py                 # OAuth views (youtube_oauth, youtube_oauth_callback)
│   ├── youtube_service.py       # YouTube API functions (upload, refresh tokens)
│   ├── models.py                # YTAccount model z tokenami
│   └── templates/uploader/youtube/
│       └── connect.html         # UI połączenia konta YouTube
```

---

## 🎯 Co dalej?

### Dodatkowe funkcje do zaimplementowania:

- [ ] Batch upload shortów
- [ ] Analityka YouTube w czasie rzeczywistym
- [ ] Automatyczne tagowanie oparte na trendach
- [ ] Edycja metadanych po publikacji
- [ ] Thumbnail customization
- [ ] Playlist management

---

## 📞 Przydatne linki

- [GOOGLE_API_SETUP.md](./GOOGLE_API_SETUP.md) - Pełna instrukcja konfiguracji
- [Google Cloud Console](https://console.cloud.google.com/)
- [YouTube Data API Docs](https://developers.google.com/youtube/v3)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)

---

**Utworzono**: 2025-11-02  
**Status**: ✅ Gotowe do użycia  
**Wersja**: 1.0
