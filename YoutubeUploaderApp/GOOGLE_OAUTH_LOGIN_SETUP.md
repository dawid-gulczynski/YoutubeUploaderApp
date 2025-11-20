# 🔐 Konfiguracja Google OAuth dla Logowania

## Przegląd

Ta aplikacja używa **Google OAuth** do logowania użytkowników. Aby to działało, musisz skonfigurować Google Cloud Project i otrzymać credentials.

## 📋 Krok po kroku

### 1. Utwórz Google Cloud Project

1. Przejdź do [Google Cloud Console](https://console.cloud.google.com)
2. Kliknij **Select a project** → **New Project**
3. Nazwij projekt (np. "YouTube Uploader Login")
4. Kliknij **Create**

### 2. Włącz Google+ API (dla logowania)

1. W menu bocznym wybierz **APIs & Services** → **Library**
2. Wyszukaj "Google+ API" lub "People API"
3. Kliknij **Enable**

### 3. Skonfiguruj OAuth Consent Screen

1. Przejdź do **APIs & Services** → **OAuth consent screen**
2. Wybierz **External** (lub Internal jeśli to workspace)
3. Wypełnij wymagane pola:
   - **App name**: YouTube Shorts Uploader
   - **User support email**: twój email
   - **Developer contact email**: twój email
4. Kliknij **Save and Continue**
5. W **Scopes** kliknij **Add or Remove Scopes**
6. Dodaj:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
   - `openid`
7. Kliknij **Save and Continue**
8. W **Test users** dodaj swój email (dla developmentu)
9. Kliknij **Save and Continue**

### 4. Utwórz OAuth 2.0 Client ID

1. Przejdź do **APIs & Services** → **Credentials**
2. Kliknij **Create Credentials** → **OAuth client ID**
3. Wybierz **Application type**: **Web application**
4. Nazwij: "YouTube Uploader - Login"
5. W **Authorized JavaScript origins** dodaj:
   ```
   http://localhost:8000
   ```
6. W **Authorized redirect URIs** dodaj:
   ```
   http://localhost:8000/accounts/google/login/callback/
   ```
7. Kliknij **Create**
8. Skopiuj **Client ID** i **Client Secret**

### 5. Skonfiguruj aplikację Django

1. Otwórz plik `.env` w katalogu głównym projektu
2. Wklej swoje credentials:
   ```env
   GOOGLE_LOGIN_CLIENT_ID=twój-client-id.apps.googleusercontent.com
   GOOGLE_LOGIN_CLIENT_SECRET=twój-client-secret
   ```

### 6. Dodaj Social App w Django Admin

1. Uruchom serwer: `python manage.py runserver`
2. Przejdź do panelu admina: `http://localhost:8000/admin/`
3. Zaloguj się jako superuser
4. Przejdź do **Sites** → kliknij **example.com**
5. Zmień:
   - **Domain name**: `localhost:8000`
   - **Display name**: `localhost:8000`
6. Kliknij **Save**
7. Przejdź do **Social applications** → **Add social application**
8. Wypełnij:
   - **Provider**: Google
   - **Name**: Google OAuth
   - **Client id**: (wklej Client ID)
   - **Secret key**: (wklej Client Secret)
   - **Sites**: Przenieś `localhost:8000` do **Chosen sites**
9. Kliknij **Save**

### 7. Testuj logowanie

1. Wyloguj się z panelu admina
2. Przejdź do `http://localhost:8000/login/`
3. Kliknij **Zaloguj przez Google**
4. Powinno przekierować do Google
5. Zaloguj się i zatwierdź dostęp
6. Powinno przekierować z powrotem do aplikacji

## 🚀 Deployment (Produkcja)

Dla produkcji musisz zaktualizować:

### 1. Authorized redirect URIs w Google Console:
```
https://twoja-domena.com/accounts/google/login/callback/
```

### 2. Site w Django Admin:
- Domain name: `twoja-domena.com`
- Display name: `Twoja Nazwa Aplikacji`

### 3. OAuth Consent Screen:
- Zmień z **Testing** na **In production**
- Wypełnij wszystkie wymagane pola
- Prześlij do weryfikacji Google (jeśli wymagane)

## ❓ Rozwiązywanie problemów

### Błąd: "redirect_uri_mismatch"
✅ **Rozwiązanie:** Upewnij się, że redirect URI w Google Console **dokładnie** pasuje do tego w aplikacji:
```
http://localhost:8000/accounts/google/login/callback/
```

### Błąd: "Error 400: invalid_request"
✅ **Rozwiązanie:** Sprawdź czy:
- OAuth Consent Screen jest skonfigurowany
- Twój email jest dodany jako test user
- Scopes zawierają `email` i `profile`

### Błąd: "SocialApp matching query does not exist"
✅ **Rozwiązanie:** 
- Przejdź do Django Admin
- Dodaj Social Application dla Google
- Upewnij się, że jest przypisana do właściwego Site

### Logowanie działa, ale użytkownik nie ma roli
✅ **Rozwiązanie:** 
- Uruchom: `python manage.py init_roles`
- Custom adapter automatycznie przypisze rolę przy następnym logowaniu

## 📚 Dodatkowe zasoby

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [django-allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google Cloud Console](https://console.cloud.google.com)

## 🔒 Bezpieczeństwo

⚠️ **WAŻNE:**
- **NIE commituj** pliku `.env` do repozytorium
- **NIE udostępniaj** Client Secret publicznie
- Używaj **HTTPS** w produkcji
- Regularnie rotuj credentials
- Monitoruj logi Google Cloud Console

---

**Powodzenia!** 🎉
