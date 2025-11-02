"""
Skrypt diagnostyczny - sprawdza konfigurację środowiska
"""
import sys
import shutil
from pathlib import Path

def check_ffmpeg():
    """Sprawdza FFmpeg"""
    print("🔍 Sprawdzam FFmpeg...")
    ffmpeg = shutil.which('ffmpeg')
    ffprobe = shutil.which('ffprobe')
    
    if ffmpeg and ffprobe:
        print(f"  ✅ FFmpeg: {ffmpeg}")
        print(f"  ✅ FFprobe: {ffprobe}")
        return True
    else:
        print("  ❌ FFmpeg NIE jest zainstalowany!")
        print("\n📝 Aby zainstalować FFmpeg:")
        print("   1. Otwórz PowerShell jako Administrator")
        print("   2. Uruchom: choco install ffmpeg")
        print("   3. Lub zobacz: FFMPEG_INSTALL.md")
        return False

def check_python():
    """Sprawdza wersję Pythona"""
    print("\n🔍 Sprawdzam Python...")
    version = sys.version_info
    print(f"  ✅ Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ⚠️  Zalecana wersja Python 3.8+")
        return False
    return True

def check_directories():
    """Sprawdza niezbędne katalogi"""
    print("\n🔍 Sprawdzam katalogi...")
    base_dir = Path(__file__).parent
    
    media_dir = base_dir / 'media'
    if not media_dir.exists():
        print(f"  ⚠️  Tworzę katalog: {media_dir}")
        media_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"  ✅ Media: {media_dir}")
    
    return True

def check_database():
    """Sprawdza bazę danych"""
    print("\n🔍 Sprawdzam bazę danych...")
    db_file = Path(__file__).parent / 'db.sqlite3'
    
    if db_file.exists():
        print(f"  ✅ Database: {db_file}")
        print(f"  📊 Rozmiar: {db_file.stat().st_size / 1024:.2f} KB")
        return True
    else:
        print("  ⚠️  Baza danych nie istnieje!")
        print("     Uruchom: python manage.py migrate")
        return False

def main():
    print("=" * 60)
    print("🔧 DIAGNOSTYKA YOUTUBE UPLOADER APP")
    print("=" * 60)
    
    results = {
        'python': check_python(),
        'ffmpeg': check_ffmpeg(),
        'directories': check_directories(),
        'database': check_database(),
    }
    
    print("\n" + "=" * 60)
    print("📊 PODSUMOWANIE")
    print("=" * 60)
    
    all_ok = all(results.values())
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name.capitalize()}")
    
    if all_ok:
        print("\n🎉 Wszystko działa poprawnie!")
        print("   Możesz uruchomić: python manage.py runserver")
    else:
        print("\n⚠️  Wykryto problemy - napraw je przed uruchomieniem serwera")
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
