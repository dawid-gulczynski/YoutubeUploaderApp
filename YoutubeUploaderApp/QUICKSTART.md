# 🚀 Szybki Start - Google OAuth Logowanie

## 📌 Ważne - Własna implementacja OAuth

Ta aplikacja używa **własnej implementacji Google OAuth** (bez django-allauth) dla większej kontroli nad procesem autoryzacji.

## ⚡ Krok 1: Uzyskaj Google OAuth Credentials (5 minut)

### A. Utwórz Google Cloud Project
1. Otwórz: https://console.cloud.google.com
2. Kliknij **"Select a project"** → **"NEW PROJECT"**
3. Nazwa: `YouTube Uploader Login`
4. Kliknij **"CREATE"**

### B. Skonfiguruj OAuth Consent Screen
1. Menu → **APIs & Services** → **OAuth consent screen**
2. Wybierz: **External**
3. Wypełnij:
   - App name: `YouTube Uploader`
   - User support email: twój email
   - Developer email: twój email
4. **SAVE AND CONTINUE**
5. W **Scopes**: kliknij **ADD OR REMOVE SCOPES**
   - Zaznacz: `userinfo.email`, `userinfo.profile` i `openid`
   - **UPDATE**
6. **SAVE AND CONTINUE**
7. W **Test users**: dodaj swój email
8. **SAVE AND CONTINUE** → **BACK TO DASHBOARD**

### C. Utwórz OAuth Client ID
1. Menu → **APIs & Services** → **Credentials**
2. **CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Web application**
4. Name: `YouTube Uploader - Login`
5. **Authorized redirect URIs** - kliknij **ADD URI**:
   ```
   http://localhost:8000/auth/google/callback/
   ```
   ⚠️ **UWAGA:** Zmieniony URL - nie `accounts/google` tylko `auth/google`
6. **CREATE**
7. **Skopiuj Client ID i Client Secret** (zapisz w notatniku)

## ⚡ Krok 2: Skonfiguruj Aplikację (1 minuta)

### A. Edytuj plik .env
Otwórz plik `.env` w katalogu głównym projektu i wklej swoje credentials:

```env
# Google OAuth dla logowania użytkowników (własna implementacja)
GOOGLE_LOGIN_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_LOGIN_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxx
```

### B. Uruchom migracje (jeśli jeszcze nie było)
```bash
python manage.py migrate
python manage.py init_roles
```

## ⚡ Krok 3: Testuj! (30 sekund)

### A. Uruchom serwer
```bash
python manage.py runserver
```

### B. Testuj logowanie
1. Otwórz przeglądarkę: http://localhost:8000/login/
2. Kliknij **"Zaloguj przez Google"**
3. Wybierz konto Google
4. Zatwierdź dostęp
5. 🎉 Zostaniesz przekierowany do Dashboard!

## 🎯 To wszystko!

Jeśli wszystko działa, możesz teraz:
- ✅ Logować się przez Google
- ✅ Rejestrować nowych użytkowników przez Google
- ✅ Uploadować wideo
- ✅ Publikować shorty na YouTube

## ❓ Problemy?

### Błąd: "redirect_uri_mismatch"
**Rozwiązanie:** W Google Cloud Console sprawdź czy redirect URI to dokładnie:
```
http://localhost:8000/auth/google/callback/
```
⚠️ Nie `accounts/google` - używamy własnej implementacji!

### Błąd: "Error 400: invalid_request"
**Rozwiązanie:** 
1. Sprawdź OAuth Consent Screen (czy wypełniony?)
2. Dodaj swój email jako Test User
3. Sprawdź czy scopes zawierają `openid`, `email` i `profile`

### Błąd: "Brak google_oauth_state w sesji"
**Rozwiązanie:** 
1. Wyczyść cookies przeglądarki
2. Spróbuj ponownie kliknąć "Zaloguj przez Google"
3. Sprawdź czy SECRET_KEY w .env jest ustawiony

### Logowanie nie działa w ogóle
**Rozwiązanie:**
1. Sprawdź `.env` - czy credentials są poprawne?
2. Sprawdź `python manage.py runserver` - czy są błędy?
3. Sprawdź console w przeglądarce (F12)

## 📚 Dodatkowe informacje

### Jak działa autoryzacja w tej aplikacji?

**Własna implementacja OAuth 2.0:**
- `google_login_direct()` - inicjalizuje OAuth flow z `google_auth_oauthlib`
- `google_callback()` - obsługuje callback, pobiera dane użytkownika z Google API
- Automatyczne tworzenie/logowanie użytkownika
- State parameter dla bezpieczeństwa CSRF

**Dlaczego nie django-allauth?**
- Większa kontrola nad procesem
- Mniej zależności
- Łatwiejsza konfiguracja
- Lepsze zrozumienie flow OAuth

---

**Czas konfiguracji: ~6 minut**  
**Poziom trudności: ⭐⭐☆☆☆**  
**Data aktualizacji: 2025-11-23**
