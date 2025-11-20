from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


# ============================================================================
# ROLE MODEL
# ============================================================================
class Role(models.Model):
    """Model reprezentujący rolę użytkownika (User, Moderator, Admin)"""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='Nazwa roli')
    symbol = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True, verbose_name='Symbol')
    
    class Meta:
        verbose_name = 'Rola'
        verbose_name_plural = 'Role'
    
    def __str__(self):
        return self.name


# ============================================================================
# CUSTOM USER MODEL
# ============================================================================
class User(AbstractUser):
    """Rozszerzony model użytkownika z integracją Google OAuth"""
    
    email = models.EmailField(unique=True, verbose_name='Email')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users', verbose_name='Rola')
    
    # Google OAuth dla logowania użytkownika
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True, verbose_name='Google ID')
    google_email = models.EmailField(blank=True, null=True, verbose_name='Google Email')
    google_picture = models.URLField(blank=True, null=True, verbose_name='Google Avatar URL')
    auth_provider = models.CharField(max_length=20, default='local', verbose_name='Metoda logowania', 
                                     choices=[('local', 'Email/Password'), ('google', 'Google OAuth')])
    email_verified = models.BooleanField(default=False, verbose_name='Email zweryfikowany')
    
    # Timestampy
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data utworzenia')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data aktualizacji')
    
    class Meta:
        verbose_name = 'Użytkownik'
        verbose_name_plural = 'Użytkownicy'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.username
    
    def has_role(self, role_symbol):
        """Sprawdza czy użytkownik ma daną rolę"""
        return self.role and self.role.symbol == role_symbol
    
    def is_moderator(self):
        return self.has_role('moderator') or self.has_role('admin')
    
    def is_admin_user(self):
        return self.has_role('admin')


# ============================================================================
# YOUTUBE ACCOUNT MODEL
# ============================================================================
class YTAccount(models.Model):
    """Model reprezentujący połączenie użytkownika z jego YouTube API (credentials dostarczone przez użytkownika)"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='yt_accounts', verbose_name='Użytkownik')
    channel_name = models.CharField(max_length=100, verbose_name='Nazwa kanału')
    channel_id = models.CharField(max_length=100, verbose_name='ID kanału')
    
    # Credentials dostarczone przez użytkownika (jego własny Google Cloud Project)
    client_id = models.CharField(max_length=500, verbose_name='Client ID (z user credentials)', blank=True, default='')
    client_secret = models.CharField(max_length=500, verbose_name='Client Secret (z user credentials)', blank=True, default='')
    
    # OAuth tokens wygenerowane dla użytkownika
    access_token = models.TextField(verbose_name='Access Token')
    refresh_token = models.TextField(blank=True, null=True, verbose_name='Refresh Token')
    token_expiry = models.DateTimeField(null=True, blank=True, verbose_name='Wygaśnięcie tokena')
    
    # Status połączenia
    is_active = models.BooleanField(default=True, verbose_name='Aktywne połączenie')
    last_sync = models.DateTimeField(null=True, blank=True, verbose_name='Ostatnia synchronizacja')
    
    # Timestampy
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data połączenia')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data aktualizacji')
    
    class Meta:
        verbose_name = 'Konto YouTube'
        verbose_name_plural = 'Konta YouTube'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.channel_name} ({self.user.username})"
    
    def is_token_valid(self):
        """Sprawdza czy token jest jeszcze ważny"""
        if not self.token_expiry:
            return False
        return timezone.now() < self.token_expiry


# ============================================================================
# VIDEO MODEL (źródłowe długie wideo)
# ============================================================================
class Video(models.Model):
    """Model reprezentujący źródłowe wideo do pocięcia na shorty"""
    
    STATUS_CHOICES = [
        ('uploaded', 'Wgrane'),
        ('processing', 'Przetwarzanie'),
        ('completed', 'Gotowe'),
        ('failed', 'Błąd'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos', verbose_name='Użytkownik')
    
    # Podstawowe informacje
    title = models.CharField(max_length=150, verbose_name='Tytuł')
    description = models.TextField(blank=True, verbose_name='Opis')
    video_file = models.FileField(upload_to='videos/%Y/%m/%d/', verbose_name='Plik wideo')
    
    # Metadane wideo
    duration = models.IntegerField(null=True, blank=True, verbose_name='Czas trwania (sekundy)')
    resolution = models.CharField(max_length=20, blank=True, verbose_name='Rozdzielczość')
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name='Rozmiar pliku (bajty)')
    
    # Status przetwarzania
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded', verbose_name='Status')
    processing_progress = models.IntegerField(default=0, verbose_name='Postęp przetwarzania (%)')
    processing_message = models.CharField(max_length=255, blank=True, verbose_name='Wiadomość statusu')
    shorts_total = models.IntegerField(default=0, verbose_name='Całkowita liczba shortów do utworzenia')
    shorts_created = models.IntegerField(default=0, verbose_name='Liczba utworzonych shortów')
    
    # Parametry cięcia
    target_duration = models.IntegerField(default=60, verbose_name='Docelowa długość shorta (sekundy)', 
                                          validators=[MinValueValidator(15), MaxValueValidator(180)])
    max_shorts_count = models.IntegerField(default=10, verbose_name='Maksymalna liczba shortów',
                                           validators=[MinValueValidator(1), MaxValueValidator(50)])
    
    # Timestampy
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data utworzenia')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data aktualizacji')
    
    class Meta:
        verbose_name = 'Wideo'
        verbose_name_plural = 'Wideo'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_shorts_count(self):
        """Zwraca liczbę wygenerowanych shortów"""
        return self.shorts.count()


# ============================================================================
# SHORT MODEL (krótkie wideo - YouTube Short)
# ============================================================================
class Short(models.Model):
    """Model reprezentujący krótkie wideo (YouTube Short)"""
    
    UPLOAD_STATUS_CHOICES = [
        ('pending', 'Oczekuje'),
        ('uploading', 'Uploadowanie'),
        ('published', 'Opublikowany'),
        ('failed', 'Błąd'),
        ('scheduled', 'Zaplanowany'),
    ]
    
    PRIVACY_CHOICES = [
        ('public', 'Publiczny'),
        ('unlisted', 'Niepubliczny'),
        ('private', 'Prywatny'),
    ]
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='shorts', verbose_name='Źródłowe wideo')
    
    # Podstawowe informacje
    title = models.CharField(max_length=100, verbose_name='Tytuł')
    description = models.TextField(blank=True, verbose_name='Opis')
    short_file = models.FileField(upload_to='shorts/%Y/%m/%d/', verbose_name='Plik shorta')
    thumbnail = models.ImageField(upload_to='thumbnails/%Y/%m/%d/', blank=True, null=True, verbose_name='Miniaturka')
    
    # Metadane
    start_time = models.FloatField(verbose_name='Czas rozpoczęcia w źródłowym wideo (sekundy)')
    duration = models.IntegerField(verbose_name='Czas trwania (sekundy)')
    order = models.IntegerField(default=0, verbose_name='Kolejność')
    
    # Status uploadu
    upload_status = models.CharField(max_length=20, choices=UPLOAD_STATUS_CHOICES, 
                                     default='pending', verbose_name='Status uploadu')
    
    # YouTube data
    yt_video_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='ID wideo na YouTube')
    yt_url = models.CharField(max_length=255, blank=True, null=True, verbose_name='Link YouTube')
    
    # Ustawienia publikacji
    privacy_status = models.CharField(max_length=20, choices=PRIVACY_CHOICES, 
                                      default='public', verbose_name='Widoczność')
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name='Zaplanowana publikacja')
    made_for_kids = models.BooleanField(default=False, verbose_name='Dla dzieci')
    
    # Statystyki (opcjonalne - z YouTube Analytics)
    views = models.IntegerField(default=0, verbose_name='Wyświetlenia')
    likes = models.IntegerField(default=0, verbose_name='Polubienia')
    comments = models.IntegerField(default=0, verbose_name='Komentarze')
    
    # Timestampy
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data utworzenia')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Data aktualizacji')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='Data publikacji')
    
    class Meta:
        verbose_name = 'Short'
        verbose_name_plural = 'Shorty'
        ordering = ['video', 'order']
    
    def __str__(self):
        return f"{self.title} (#{self.order})"
    
    def is_published(self):
        return self.upload_status == 'published'
    
    def can_publish(self):
        return self.upload_status in ['pending', 'failed']
