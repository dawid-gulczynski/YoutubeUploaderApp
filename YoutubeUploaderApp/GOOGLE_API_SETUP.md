# 🔐 Konfiguracja Google API dla YouTube (User-Provided Credentials)

## 📌 Ważne - Model User-Provided Credentials

Ta aplikacja używa modelu **user-provided credentials** - każdy użytkownik dostarcza własne klucze API YouTube, co oznacza:
- ✅ Każdy użytkownik ma własne YouTube API quota (10,000 units/dzień)
- ✅ Nie ma współdzielonego limitu między użytkownikami
- ✅ Pełna kontrola użytkownika nad dostępem do swojego kanału
- ✅ Brak `client_secrets.json` na serwerze

## 📋 Krok po kroku: Instrukcja dla użytkowników

Każdy użytkownik aplikacji musi wykonać te kroki, aby móc publikować shorty na swoim kanale YouTube:

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

### 5. Pobierz i zapisz credentials

1. Po utworzeniu zobaczysz modal z **Client ID** i **Client Secret**
2. **Skopiuj oba** - będą potrzebne w aplikacji
3. NIE pobieraj jako JSON - aplikacja przyjmuje credentials bezpośrednio

**⚠️ WAŻNE:** NIE umieszczaj tych credentials w `client_secrets.json` na serwerze. Wprowadzisz je bezpośrednio w aplikacji podczas łączenia konta YouTube.

### 6. Wprowadź credentials w aplikacji

1. Zaloguj się do aplikacji YouTube Uploader
2. Przejdź do: **Dashboard** → **Połącz konto YouTube**
3. Wypełnij formularz:
   - **Client ID**: wklej skopiowany Client ID
   - **Client Secret**: wklej skopiowany Client Secret
4. Kliknij **"Połącz z YouTube"**
5. Zostaniesz przekierowany do Google OAuth
6. Zaloguj się i zatwierdź uprawnienia
7. ✅ Konto połączone - możesz publikować shorty!

## 🔒 Bezpieczeństwo

### Model User-Provided Credentials:
- ✅ Credentials przechowywane w bazie danych (YTAccount model)
- ✅ Każdy użytkownik ma własne credentials
- ✅ Tokeny automatycznie odświeżane
- ✅ Brak shared credentials na serwerze

### Użytkownicy powinni:
- ✅ Nie udostępniać swojego Client ID i Client Secret
- ✅ Używać HTTPS w produkcji
- ✅ Regularnie monitorować użycie API w Google Console
- ✅ Odłączyć konto w aplikacji jeśli już nie jest używane

## 📊 Limity YouTube Data API v3

### Quota dzienne (domyślnie):
- **10,000 units/dzień PER USER** (za darmo)
- Każdy użytkownik ma własny limit dzięki user-provided credentials

### Koszty operacji:
- **Video upload**: 1600 units
- **Video list**: 1 unit
- **Channel info**: 1 unit

### Przykład (dla pojedynczego użytkownika):
- **6 uploadów/dzień** = 9,600 units (96% limitu)
- **100+ uploadów/dzień** = Potrzebne zwiększenie limitu

### Zwiększenie limitu (dla użytkownika):
Każdy użytkownik może wystąpić o zwiększenie limitu w swoim Google Cloud Project:
1. Google Cloud Console → **"YouTube Data API v3"** → **"Quotas"**
2. Kliknij **"ALL QUOTAS"**
3. Znajdź **"Queries per day"**
4. Kliknij ikonę edycji → **"APPLY FOR HIGHER QUOTA"**
5. Wypełnij formularz uzasadnienia

## 🐛 Troubleshooting

### Błąd: "Access blocked: This app's request is invalid"
**Rozwiązanie**: Sprawdź Authorized redirect URIs - musi dokładnie pasować do URL w aplikacji

### Błąd: "invalid_client"
**Rozwiązanie**: Sprawdź czy Client ID i Client Secret są poprawnie skopiowane w aplikacji (bez spacji na końcu)

### Błąd: "403 Forbidden"
**Rozwiązanie**: 
- Sprawdź czy YouTube Data API v3 jest włączone w Twoim Google Cloud Project
- Sprawdź czy token nie wygasł (aplikacja automatycznie odświeża)
- Kliknij "Odłącz konto" i połącz ponownie

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
**Zaktualizowano**: 2025-11-23  
**Wersja**: 2.0 (User-Provided Credentials)  
**Status**: Aktualna dokumentacja
