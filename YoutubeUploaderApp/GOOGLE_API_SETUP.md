# 🔐 Konfiguracja Google API dla YouTube OAuth

## Przegląd
Aby móc publikować shorty na YouTube, aplikacja potrzebuje dostępu do YouTube Data API v3 przez OAuth 2.0.

## 📋 Krok po kroku: Tworzenie Google API credentials

### 1. Utwórz projekt w Google Cloud Console

1. Przejdź do [Google Cloud Console](https://console.cloud.google.com/)
2. Kliknij **"Select a project"** → **"NEW PROJECT"**
3. Nazwa projektu: `YouTube Shorts Uploader` (lub dowolna)
4. Kliknij **"CREATE"**

### 2. Włącz YouTube Data API v3

1. W menu bocznym: **"APIs & Services"** → **"Library"**
2. Wyszukaj: `YouTube Data API v3`
3. Kliknij na wynik, następnie **"ENABLE"**

### 3. Skonfiguruj OAuth consent screen

1. **"APIs & Services"** → **"OAuth consent screen"**
2. User Type: **External** → Kliknij **"CREATE"**
3. Wypełnij formularz:
   - **App name**: `YouTube Shorts Uploader`
   - **User support email**: Twój email
   - **Developer contact**: Twój email
4. Kliknij **"SAVE AND CONTINUE"**

#### Dodaj scopes:
5. Kliknij **"ADD OR REMOVE SCOPES"**
6. Wyszukaj i zaznacz:
   - `https://www.googleapis.com/auth/youtube.upload` - Umożliwia upload wideo
   - `https://www.googleapis.com/auth/youtube.readonly` - Umożliwia odczyt danych kanału
   - `https://www.googleapis.com/auth/youtube` - Pełny dostęp (opcjonalnie)
7. Kliknij **"UPDATE"** → **"SAVE AND CONTINUE"**

#### Dodaj test users (w trybie testowym):
8. Kliknij **"ADD USERS"**
9. Dodaj swój email Google (konto YouTube)
10. Kliknij **"SAVE AND CONTINUE"** → **"BACK TO DASHBOARD"**

### 4. Utwórz OAuth 2.0 credentials

1. **"APIs & Services"** → **"Credentials"**
2. Kliknij **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. Application type: **Web application**
4. Name: `YouTube Shorts Uploader Web Client`
5. **Authorized redirect URIs** → Kliknij **"+ ADD URI"**:
   - Dla rozwoju: `http://127.0.0.1:8000/youtube/oauth/callback/`
   - Dla produkcji: `https://yourdomain.com/youtube/oauth/callback/`
6. Kliknij **"CREATE"**

### 5. Pobierz credentials

1. Po utworzeniu zobaczysz modal z **Client ID** i **Client Secret**
2. Kliknij **"DOWNLOAD JSON"**
3. Pobierz plik (np. `client_secret_xxx.json`)

### 6. Skonfiguruj aplikację Django

1. Skopiuj pobrany plik do głównego katalogu projektu:
   ```powershell
   cp path/to/downloaded/client_secret_xxx.json client_secrets.json
   ```

2. Alternatywnie: skopiuj zawartość do `client_secrets.json` ręcznie

3. Struktura pliku `client_secrets.json`:
   ```json
   {
     "web": {
       "client_id": "1234567890-xxx.apps.googleusercontent.com",
       "project_id": "youtube-shorts-uploader",
       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
       "token_uri": "https://oauth2.googleapis.com/token",
       "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
       "client_secret": "GOCSPX-xxxxxxxxxxxxx",
       "redirect_uris": [
         "http://127.0.0.1:8000/youtube/oauth/callback/"
       ]
     }
   }
   ```

4. **WAŻNE**: Dodaj `client_secrets.json` do `.gitignore`:
   ```
   client_secrets.json
   ```

### 7. Testowanie OAuth flow

1. Uruchom serwer Django:
   ```powershell
   python manage.py runserver
   ```

2. Zaloguj się do aplikacji

3. Przejdź do: **Dashboard** → **Połącz konto YouTube**

4. Kliknij **"Autoryzuj z Google"**

5. Zaloguj się do Google (użyj konta dodanego jako test user)

6. Zaakceptuj uprawnienia

7. Zostaniesz przekierowany z powrotem - konto połączone! ✅

## 🔒 Bezpieczeństwo

### Nigdy nie commituj:
- ❌ `client_secrets.json` - zawiera client_secret
- ❌ Tokens w kodzie - przechowuj w bazie danych
- ❌ API keys w kodzie - używaj zmiennych środowiskowych

### Dobre praktyki:
- ✅ Używaj HTTPS w produkcji
- ✅ Regularnie rotuj secrets
- ✅ Ogranicz scopes do minimum
- ✅ Monitoruj użycie API w Google Console

## 📊 Limity YouTube Data API v3

### Quota dzienne (domyślnie):
- **10,000 units/dzień** (za darmo)

### Koszty operacji:
- **Video upload**: 1600 units
- **Video list**: 1 unit
- **Channel info**: 1 unit

### Przykład:
- **6 uploadów/dzień** = 9,600 units (96% limitu)
- **100+ uploadów/dzień** = Potrzebne zwiększenie limitu

### Zwiększenie limitu:
1. Google Cloud Console → **"YouTube Data API v3"** → **"Quotas"**
2. Kliknij **"ALL QUOTAS"**
3. Znajdź **"Queries per day"**
4. Kliknij ikonę edycji → **"APPLY FOR HIGHER QUOTA"**
5. Wypełnij formularz uzasadnienia

## 🐛 Troubleshooting

### Błąd: "Access blocked: This app's request is invalid"
**Rozwiązanie**: Sprawdź Authorized redirect URIs - musi dokładnie pasować do URL w aplikacji

### Błąd: "invalid_client"
**Rozwiązanie**: Sprawdź czy `client_secrets.json` ma poprawną strukturę i client_id

### Błąd: "403 Forbidden"
**Rozwiązanie**: 
- Sprawdź czy YouTube Data API v3 jest włączone
- Sprawdź czy token nie wygasł (aplikacja automatycznie odświeża)

### Błąd: "The user is not a test user"
**Rozwiązanie**: W OAuth consent screen → Test users → Dodaj swojego użytkownika

### Błąd: "Quota exceeded"
**Rozwiązanie**:
- Poczekaj do północy PST (quota resetuje się)
- Lub wystąp o zwiększenie limitu

## 🚀 Publikacja aplikacji (Production)

### Aby umożliwić każdemu użycie (nie tylko test users):

1. **Google Cloud Console** → **"OAuth consent screen"**
2. Kliknij **"PUBLISH APP"**
3. Przejdź weryfikację Google (wymaga):
   - Link do Privacy Policy
   - Link do Terms of Service
   - Uzupełnione domeny
   - Może wymagać weryfikacji (1-7 dni)

### Po publikacji:
- ✅ Każdy może autoryzować
- ✅ Bez ostrzeżenia "This app hasn't been verified"
- ✅ Większa wiarygodność

## 📝 Przydatne linki

- [Google Cloud Console](https://console.cloud.google.com/)
- [YouTube Data API v3 Docs](https://developers.google.com/youtube/v3)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [API Explorer](https://developers.google.com/youtube/v3/docs)
- [Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)

---

**Utworzono**: 2025-11-02  
**Wersja**: 1.0  
**Status**: Gotowe do użycia
