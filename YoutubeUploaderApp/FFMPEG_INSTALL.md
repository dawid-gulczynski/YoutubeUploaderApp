# Instalacja FFmpeg na Windows

FFmpeg jest wymagany do automatycznego cięcia wideo na shorty.

## Metoda 1: Instalacja przez Chocolatey (zalecana)

1. Otwórz PowerShell jako Administrator
2. Zainstaluj Chocolatey (jeśli nie masz):
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

3. Zainstaluj FFmpeg:
```powershell
choco install ffmpeg
```

4. Zrestartuj terminal i sprawdź:
```powershell
ffmpeg -version
```

## Metoda 2: Ręczna instalacja

1. Pobierz FFmpeg ze strony: https://www.gyan.dev/ffmpeg/builds/
2. Wybierz wersję "ffmpeg-release-essentials.zip"
3. Rozpakuj do `C:\ffmpeg`
4. Dodaj do PATH:
   - Otwórz "Edytuj zmienne środowiskowe systemu"
   - Kliknij "Zmienne środowiskowe"
   - W "Zmienne systemowe" znajdź "Path" i kliknij "Edytuj"
   - Dodaj: `C:\ffmpeg\bin`
   - Kliknij OK
5. Zrestartuj terminal i sprawdź:
```powershell
ffmpeg -version
```

## Weryfikacja

Po instalacji uruchom:
```bash
ffmpeg -version
ffprobe -version
```

Powinieneś zobaczyć informacje o wersji FFmpeg.

## Troubleshooting

Jeśli po instalacji nadal nie działa:
1. Zrestartuj komputer
2. Sprawdź czy `ffmpeg.exe` i `ffprobe.exe` są w folderze `C:\ffmpeg\bin`
3. Sprawdź czy ścieżka do FFmpeg jest w PATH (uruchom `echo $env:Path` w PowerShell)
