"""
Widoki aplikacji YouTube Uploader
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.utils import timezone
import threading
import logging

from .models import User, Role, Video, Short, YTAccount
from .forms import UserRegistrationForm, UserLoginForm, VideoUploadForm, ShortEditForm, UserProfileForm
from .video_processing import process_video_async, check_ffmpeg_installed

logger = logging.getLogger(__name__)


# ============================================================================
# STRONA GŁÓWNA
# ============================================================================

def home_view(request):
    """Strona główna - przekierowuje do dashboard lub logowania"""
    if request.user.is_authenticated:
        return redirect('uploader:dashboard')
    return redirect('uploader:login')


def google_login_direct(request):
    """Bezpośrednie przekierowanie do Google OAuth"""
    from google_auth_oauthlib.flow import Flow
    from django.conf import settings
    import os
    
    # Wyłącz wymóg HTTPS w developmencie
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    # Pobierz credentials z .env
    client_id = os.getenv('GOOGLE_LOGIN_CLIENT_ID', '')
    client_secret = os.getenv('GOOGLE_LOGIN_CLIENT_SECRET', '')
    
    if not client_id or not client_secret:
        messages.error(request, '❌ Google OAuth nie jest skonfigurowany. Skontaktuj się z administratorem.')
        return redirect('uploader:login')
    
    try:
        # Utwórz client config
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [request.build_absolute_uri(reverse('uploader:google_callback'))]
            }
        }
        
        # Utwórz OAuth flow
        flow = Flow.from_client_config(
            client_config,
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
            redirect_uri=request.build_absolute_uri(reverse('uploader:google_callback'))
        )
        
        # Generuj authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='online',
            prompt='select_account'
        )
        
        # Zapisz state w sesji
        request.session['google_oauth_state'] = state
        
        # Przekieruj bezpośrednio do Google
        return redirect(authorization_url)
        
    except Exception as e:
        logger.error(f'Google OAuth error: {str(e)}')
        messages.error(request, f'❌ Błąd logowania przez Google: {str(e)}')
        return redirect('uploader:login')


def google_callback(request):
    """Callback po autoryzacji Google"""
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build as google_build
    import os
    
    # Wyłącz wymóg HTTPS w developmencie
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    state = request.session.get('google_oauth_state')
    if not state:
        messages.error(request, '❌ Błąd: Brak state w sesji. Spróbuj ponownie.')
        return redirect('uploader:login')
    
    client_id = os.getenv('GOOGLE_LOGIN_CLIENT_ID', '')
    client_secret = os.getenv('GOOGLE_LOGIN_CLIENT_SECRET', '')
    
    try:
        # Utwórz client config
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [request.build_absolute_uri(reverse('uploader:google_callback'))]
            }
        }
        
        # Utwórz OAuth flow
        flow = Flow.from_client_config(
            client_config,
            scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
            state=state,
            redirect_uri=request.build_absolute_uri(reverse('uploader:google_callback'))
        )
        
        # Fetch token
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials
        
        # Pobierz informacje o użytkowniku z Google
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build as google_build
        
        google_credentials = Credentials(
            token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            scopes=credentials.scopes
        )
        
        # Pobierz dane użytkownika
        people_service = google_build('oauth2', 'v2', credentials=google_credentials)
        user_info = people_service.userinfo().get().execute()
        
        google_id = user_info.get('id')
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        
        # Sprawdź czy użytkownik już istnieje
        user = None
        try:
            # Najpierw szukaj po google_id
            user = User.objects.get(google_id=google_id)
        except User.DoesNotExist:
            # Jeśli nie ma, szukaj po emailu
            try:
                user = User.objects.get(email=email)
                # Aktualizuj dane Google
                user.google_id = google_id
                user.auth_provider = 'google'
                user.google_email = email
                user.google_picture = picture
                user.save()
            except User.DoesNotExist:
                # Utwórz nowego użytkownika
                username = email.split('@')[0]
                # Upewnij się, że username jest unikalny
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Utwórz rolę jeśli nie istnieje
                user_role, created = Role.objects.get_or_create(
                    symbol='user',
                    defaults={'name': 'Użytkownik'}
                )
                
                user = User.objects.create(
                    username=username,
                    email=email,
                    google_id=google_id,
                    auth_provider='google',
                    google_email=email,
                    google_picture=picture,
                    role=user_role,
                    email_verified=True
                )
        
        # Zaloguj użytkownika
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        # Wyczyść state z sesji
        request.session.pop('google_oauth_state', None)
        
        messages.success(request, f'✅ Witaj, {user.username}!')
        return redirect('uploader:dashboard')
        
    except Exception as e:
        logger.error(f'Google callback error: {str(e)}')
        messages.error(request, f'❌ Błąd podczas logowania: {str(e)}')
        return redirect('uploader:login')


# ============================================================================
# AUTENTYKACJA
# ============================================================================

def register_view(request):
    """Widok rejestracji użytkownika"""
    if request.user.is_authenticated:
        return redirect('uploader:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                # Pobierz lub utwórz rolę 'user' jeśli nie istnieje
                user_role, created = Role.objects.get_or_create(
                    symbol='user',
                    defaults={'name': 'Użytkownik'}
                )
                user.role = user_role
                user.save()
                messages.success(request, '✅ Konto zostało utworzone! Możesz się teraz zalogować.')
                return redirect('uploader:login')
            except Exception as e:
                logger.error(f'Error during user registration: {str(e)}')
                messages.error(request, f'❌ Błąd podczas rejestracji: {str(e)}')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'uploader/auth/register.html', {'form': form})


def login_view(request):
    """Widok logowania"""
    if request.user.is_authenticated:
        return redirect('uploader:dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            try:
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f'✅ Witaj, {user.username}!')
                    return redirect('uploader:dashboard')
                else:
                    messages.error(request, '❌ Nieprawidłowa nazwa użytkownika lub hasło.')
            except Exception as e:
                logger.error(f'Error during login: {str(e)}')
                messages.error(request, '❌ Wystąpił błąd podczas logowania. Spróbuj ponownie.')
        else:
            messages.error(request, '❌ Nieprawidłowe dane logowania.')
    else:
        form = UserLoginForm()
    
    return render(request, 'uploader/auth/login.html', {'form': form})


@login_required
def logout_view(request):
    """Widok wylogowania"""
    logout(request)
    messages.info(request, 'Zostałeś wylogowany.')
    return redirect('uploader:login')


@login_required
def profile_edit_view(request):
    """Widok edycji profilu użytkownika"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, '✅ Profil został zaktualizowany.')
                return redirect('uploader:profile_edit')
            except Exception as e:
                logger.error(f'Error updating profile for user {request.user.id}: {str(e)}')
                messages.error(request, f'❌ Błąd podczas aktualizacji profilu: {str(e)}')
        else:
            messages.error(request, '❌ Formularz zawiera błędy. Sprawdź wprowadzone dane.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'uploader/auth/profile_edit.html', {'form': form})


# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
def dashboard_view(request):
    """Główny dashboard"""
    try:
        user = request.user
        videos = Video.objects.filter(user=user)
        shorts = Short.objects.filter(video__user=user)
        
        stats = {
            'total_videos': videos.count(),
            'processing_videos': videos.filter(status='processing').count(),
            'completed_videos': videos.filter(status='completed').count(),
            'total_shorts': shorts.count(),
            'published_shorts': shorts.filter(upload_status='published').count(),
            'pending_shorts': shorts.filter(upload_status='pending').count(),
            'total_views': shorts.aggregate(total=Sum('views'))['total'] or 0,
        }
        
        recent_videos = videos.order_by('-created_at')[:5]
        recent_shorts = shorts.order_by('-created_at')[:10]
        yt_account = YTAccount.objects.filter(user=user).first()
        
        context = {
            'stats': stats,
            'recent_videos': recent_videos,
            'recent_shorts': recent_shorts,
            'yt_account': yt_account,
            'ffmpeg_installed': check_ffmpeg_installed(),
        }
        
        return render(request, 'uploader/dashboard.html', context)
    except Exception as e:
        logger.error(f'Error loading dashboard for user {request.user.id}: {str(e)}')
        messages.error(request, '❌ Wystąpił błąd podczas ładowania dashboardu.')
        return render(request, 'uploader/dashboard.html', {'stats': {}, 'ffmpeg_installed': False})


# ============================================================================
# WIDEO
# ============================================================================

class VideoListView(LoginRequiredMixin, ListView):
    model = Video
    template_name = 'uploader/video/video_list.html'
    context_object_name = 'videos'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Video.objects.filter(user=self.request.user)
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        return queryset.order_by('-created_at')


class VideoUploadView(LoginRequiredMixin, CreateView):
    model = Video
    form_class = VideoUploadForm
    template_name = 'uploader/video/video_upload.html'
    success_url = reverse_lazy('uploader:video_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ffmpeg_installed'] = check_ffmpeg_installed()
        return context
    
    def form_valid(self, form):
        try:
            video = form.save(commit=False)
            video.user = self.request.user
            video.status = 'uploaded'
            video.save()
            
            if not check_ffmpeg_installed():
                messages.warning(self.request, '⚠️ Wideo zostało wgrane, ale FFmpeg nie jest zainstalowany. Shorty nie zostaną wygenerowane. Zobacz FFMPEG_INSTALL.md')
            else:
                messages.success(self.request, '✅ Wideo zostało wgrane! Rozpoczynam przetwarzanie...')
                crop_mode = self.request.POST.get('crop_mode', 'center')
                thread = threading.Thread(target=process_video_async, args=(video.id, crop_mode))
                thread.daemon = True
                thread.start()
            
            return redirect('uploader:video_detail', pk=video.pk)
        except Exception as e:
            logger.error(f'Error uploading video: {str(e)}')
            messages.error(self.request, f'❌ Błąd podczas wgrywania wideo: {str(e)}')
            return redirect('uploader:video_upload')


class VideoDetailView(LoginRequiredMixin, DetailView):
    model = Video
    template_name = 'uploader/video/video_detail.html'
    context_object_name = 'video'
    
    def get_queryset(self):
        return Video.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shorts'] = self.object.shorts.all().order_by('order')
        return context


@login_required
def video_delete(request, pk):
    video = get_object_or_404(Video, pk=pk, user=request.user)
    if request.method == 'POST':
        try:
            video_title = video.title
            video.delete()
            messages.success(request, f'✅ Wideo "{video_title}" zostało usunięte.')
            return redirect('uploader:video_list')
        except Exception as e:
            logger.error(f'Error deleting video {pk}: {str(e)}')
            messages.error(request, f'❌ Błąd podczas usuwania wideo: {str(e)}')
            return redirect('uploader:video_detail', pk=pk)
    return render(request, 'uploader/video/video_confirm_delete.html', {'video': video})


# ============================================================================
# SHORTY
# ============================================================================

class ShortListView(LoginRequiredMixin, ListView):
    model = Short
    template_name = 'uploader/short/short_list.html'
    context_object_name = 'shorts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Short.objects.filter(video__user=self.request.user)
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        
        if status:
            queryset = queryset.filter(upload_status=status)
        if search:
            queryset = queryset.filter(title__icontains=search)
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pobierz wszystkie shorty użytkownika (bez filtrów)
        all_shorts = Short.objects.filter(video__user=self.request.user)
        
        # Oblicz statystyki
        from django.db.models import Sum
        context['stats'] = {
            'total': all_shorts.count(),
            'pending': all_shorts.filter(upload_status='pending').count(),
            'published': all_shorts.filter(upload_status='published').count(),
            'total_views': all_shorts.filter(upload_status='published').aggregate(Sum('views'))['views__sum'] or 0,
        }
        
        return context


class ShortDetailView(LoginRequiredMixin, DetailView):
    model = Short
    template_name = 'uploader/short/short_detail.html'
    context_object_name = 'short'
    
    def get_queryset(self):
        return Short.objects.filter(video__user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        short = self.object
        
        # Automatycznie odśwież statystyki jeśli short jest opublikowany
        if short.is_published() and short.yt_video_id:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            import os
            
            # Wyłącz wymóg HTTPS w developmencie
            os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
            
            yt_account = YTAccount.objects.filter(user=self.request.user).first()
            if yt_account:
                try:
                    # Utwórz credentials z zapisanych tokenów
                    credentials = Credentials(
                        token=yt_account.access_token,
                        refresh_token=yt_account.refresh_token,
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=yt_account.client_id,
                        client_secret=yt_account.client_secret
                    )
                    
                    # Utwórz YouTube service
                    youtube = build('youtube', 'v3', credentials=credentials)
                    
                    # Pobierz statystyki wideo
                    video_response = youtube.videos().list(
                        part='statistics',
                        id=short.yt_video_id
                    ).execute()
                    
                    if video_response.get('items'):
                        # Zaktualizuj statystyki
                        stats = video_response['items'][0]['statistics']
                        short.views = int(stats.get('viewCount', 0))
                        short.likes = int(stats.get('likeCount', 0))
                        short.comments = int(stats.get('commentCount', 0))
                        short.save()
                except Exception as e:
                    logger.error(f'Error auto-refreshing stats: {str(e)}')
        
        return context


class ShortEditView(LoginRequiredMixin, UpdateView):
    model = Short
    form_class = ShortEditForm
    template_name = 'uploader/short/short_edit.html'
    
    def get_queryset(self):
        return Short.objects.filter(video__user=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('uploader:short_detail', kwargs={'pk': self.object.pk})


@login_required
def short_publish(request, pk):
    """Publikuje short na YouTube"""
    from .youtube_service import upload_short_to_youtube
    
    short = get_object_or_404(Short, pk=pk, video__user=request.user)
    
    # Sprawdź czy użytkownik ma połączone konto YouTube
    yt_account = YTAccount.objects.filter(user=request.user).first()
    
    if not yt_account:
        messages.error(request, 'Musisz najpierw połączyć konto YouTube!')
        return redirect('uploader:connect_youtube')
    
    # Sprawdź czy short już nie jest opublikowany
    if short.upload_status == 'published':
        messages.warning(request, 'Ten short jest już opublikowany na YouTube!')
        return redirect('uploader:short_detail', pk=pk)
    
    # Ustaw status "uploading"
    short.upload_status = 'uploading'
    short.save()
    
    try:
        # Upload na YouTube
        result = upload_short_to_youtube(short, yt_account)
        
        if result['success']:
            # Sukces - zapisz dane YouTube
            short.upload_status = 'published'
            short.yt_video_id = result['video_id']
            short.yt_url = result['video_url']
            short.published_at = timezone.now()
            short.save()
            
            messages.success(
                request,
                f'✅ Short został opublikowany na YouTube! <a href="{result["video_url"]}" target="_blank" class="underline">Zobacz na YouTube</a>',
                extra_tags='safe'
            )
        else:
            # Błąd uploadu
            short.upload_status = 'failed'
            short.save()
            
            messages.error(
                request,
                f'❌ Błąd podczas publikacji: {result["error"]}'
            )
    
    except Exception as e:
        # Nieoczekiwany błąd
        short.upload_status = 'failed'
        short.save()
        
        messages.error(request, f'Wystąpił błąd: {str(e)}')
        logger.error(f'Error publishing short {pk}: {str(e)}')
    
    return redirect('uploader:short_detail', pk=pk)


@login_required
def short_delete(request, pk):
    short = get_object_or_404(Short, pk=pk, video__user=request.user)
    if request.method == 'POST':
        try:
            video_id = short.video.id
            short_title = short.title
            yt_video_id = short.yt_video_id
            
            # Jeśli short jest opublikowany na YouTube, usuń go tam również
            if short.is_published() and yt_video_id:
                from googleapiclient.discovery import build
                from google.oauth2.credentials import Credentials
                import os
                
                # Wyłącz wymóg HTTPS w developmencie
                os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
                
                yt_account = YTAccount.objects.filter(user=request.user).first()
                if yt_account:
                    try:
                        # Utwórz credentials
                        credentials = Credentials(
                            token=yt_account.access_token,
                            refresh_token=yt_account.refresh_token,
                            token_uri="https://oauth2.googleapis.com/token",
                            client_id=yt_account.client_id,
                            client_secret=yt_account.client_secret
                        )
                        
                        # Utwórz YouTube service
                        youtube = build('youtube', 'v3', credentials=credentials)
                        
                        # Usuń wideo z YouTube
                        youtube.videos().delete(id=yt_video_id).execute()
                        logger.info(f'Successfully deleted video {yt_video_id} from YouTube')
                        
                    except Exception as e:
                        logger.error(f'Error deleting video from YouTube: {str(e)}')
                        # Kontynuuj usuwanie z bazy danych nawet jeśli usunięcie z YouTube nie powiodło się
            
            # Usuń short z bazy danych
            short.delete()
            messages.success(request, f'✅ Short "{short_title}" został usunięty z systemu i YouTube.')
            return redirect('uploader:video_detail', pk=video_id)
        except Exception as e:
            logger.error(f'Error deleting short {pk}: {str(e)}')
            messages.error(request, f'❌ Błąd podczas usuwania shorta: {str(e)}')
            return redirect('uploader:short_detail', pk=pk)
    return render(request, 'uploader/short/short_confirm_delete.html', {'short': short})


@login_required
def short_refresh_stats(request, pk):
    """Odświeża statystyki shorta z YouTube"""
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    import os
    
    # Wyłącz wymóg HTTPS w developmencie
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    short = get_object_or_404(Short, pk=pk, video__user=request.user)
    
    # Sprawdź czy short jest opublikowany
    if not short.is_published() or not short.yt_video_id:
        messages.error(request, '❌ Ten short nie jest jeszcze opublikowany na YouTube.')
        return redirect('uploader:short_detail', pk=pk)
    
    # Sprawdź czy użytkownik ma połączone konto YouTube
    yt_account = YTAccount.objects.filter(user=request.user).first()
    if not yt_account:
        messages.error(request, '❌ Musisz najpierw połączyć konto YouTube!')
        return redirect('uploader:connect_youtube')
    
    try:
        # Utwórz credentials z zapisanych tokenów
        credentials = Credentials(
            token=yt_account.access_token,
            refresh_token=yt_account.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=yt_account.client_id,
            client_secret=yt_account.client_secret
        )
        
        # Utwórz YouTube service
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # Pobierz statystyki wideo
        video_response = youtube.videos().list(
            part='statistics',
            id=short.yt_video_id
        ).execute()
        
        if not video_response.get('items'):
            messages.error(request, '❌ Nie znaleziono wideo na YouTube. Być może zostało usunięte.')
            return redirect('uploader:short_detail', pk=pk)
        
        # Zaktualizuj statystyki
        stats = video_response['items'][0]['statistics']
        short.views = int(stats.get('viewCount', 0))
        short.likes = int(stats.get('likeCount', 0))
        short.comments = int(stats.get('commentCount', 0))
        short.save()
        
        messages.success(request, f'✅ Statystyki zaktualizowane! Wyświetlenia: {short.views}, Polubienia: {short.likes}, Komentarze: {short.comments}')
        return redirect('uploader:short_detail', pk=pk)
        
    except Exception as e:
        logger.error(f'Error refreshing stats: {str(e)}')
        messages.error(request, f'❌ Błąd podczas pobierania statystyk: {str(e)}')
        return redirect('uploader:short_detail', pk=pk)


# ============================================================================
# YOUTUBE
# ============================================================================

@login_required
def connect_youtube(request):
    """Widok połączenia konta YouTube - użytkownik dostarcza własne Google API credentials"""
    yt_account = YTAccount.objects.filter(user=request.user).first()
    
    if request.method == 'POST' and 'disconnect' in request.POST:
        # Odłączanie konta
        return disconnect_youtube(request)
    
    return render(request, 'uploader/youtube/connect.html', {'yt_account': yt_account})


@login_required
def youtube_oauth(request):
    """Krok 1: Użytkownik dostarcza swoje Google API credentials (Client ID i Client Secret)"""
    yt_account = YTAccount.objects.filter(user=request.user).first()
    
    if request.method == 'POST':
        client_id = request.POST.get('client_id', '').strip()
        client_secret = request.POST.get('client_secret', '').strip()
        
        if not client_id or not client_secret:
            messages.error(request, '❌ Musisz podać Client ID i Client Secret.')
            return redirect('uploader:connect_youtube')
        
        # Zapisz credentials w sesji do użycia w callback
        request.session['yt_client_id'] = client_id
        request.session['yt_client_secret'] = client_secret
        
        # Przekieruj do procesu OAuth
        return redirect('uploader:youtube_oauth_start')
    
    return redirect('uploader:connect_youtube')


@login_required
def youtube_oauth_start(request):
    """Krok 2: Inicjuje proces OAuth 2.0 z credentials użytkownika"""
    from google_auth_oauthlib.flow import Flow
    from django.urls import reverse
    import json
    import tempfile
    import os
    
    # Wyłącz wymóg HTTPS w developmencie
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    client_id = request.session.get('yt_client_id')
    client_secret = request.session.get('yt_client_secret')
    
    if not client_id or not client_secret:
        messages.error(request, '❌ Brak credentials. Rozpocznij od początku.')
        return redirect('uploader:connect_youtube')
    
    try:
        # Utwórz tymczasowy plik client_secrets dla tego użytkownika
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [request.build_absolute_uri(reverse('uploader:youtube_oauth_callback'))]
            }
        }
        
        # Utwórz OAuth flow z credentials użytkownika
        flow = Flow.from_client_config(
            client_config,
            scopes=[
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube.readonly',
                'https://www.googleapis.com/auth/youtube.force-ssl'
            ],
            redirect_uri=request.build_absolute_uri(reverse('uploader:youtube_oauth_callback'))
        )
        
        # Generuj authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )
        
        # Zapisz state w sesji
        request.session['oauth_state'] = state
        
        return redirect(authorization_url)
        
    except Exception as e:
        logger.error(f'OAuth initialization error: {str(e)}')
        messages.error(request, f'❌ Błąd inicjalizacji OAuth: {str(e)}. Sprawdź czy Client ID i Secret są poprawne.')
        return redirect('uploader:connect_youtube')


@login_required
def youtube_oauth_callback(request):
    """Krok 3: Callback po autoryzacji OAuth - zapisz tokeny użytkownika"""
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    import os
    
    # Wyłącz wymóg HTTPS w developmencie
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    state = request.session.get('oauth_state')
    client_id = request.session.get('yt_client_id')
    client_secret = request.session.get('yt_client_secret')
    
    if not state or not client_id or not client_secret:
        messages.error(request, '❌ Błąd: Brak danych sesji. Spróbuj ponownie.')
        return redirect('uploader:connect_youtube')
    
    try:
        # Utwórz client config
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [request.build_absolute_uri(reverse('uploader:youtube_oauth_callback'))]
            }
        }
        
        # Utwórz OAuth flow ze state
        flow = Flow.from_client_config(
            client_config,
            scopes=[
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube.readonly',
                'https://www.googleapis.com/auth/youtube.force-ssl'
            ],
            state=state,
            redirect_uri=request.build_absolute_uri(reverse('uploader:youtube_oauth_callback'))
        )
        
        # Fetch token
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials
        
        # Pobierz informacje o kanale
        youtube = build('youtube', 'v3', credentials=credentials)
        channel_response = youtube.channels().list(
            part='snippet,contentDetails,statistics',
            mine=True
        ).execute()
        
        if not channel_response.get('items'):
            messages.error(request, '❌ Nie znaleziono kanału YouTube dla tego konta.')
            return redirect('uploader:connect_youtube')
        
        channel = channel_response['items'][0]
        channel_id = channel['id']
        channel_name = channel['snippet']['title']
        
        # Zapisz lub zaktualizuj YTAccount z credentials użytkownika
        yt_account, created = YTAccount.objects.update_or_create(
            user=request.user,
            defaults={
                'channel_id': channel_id,
                'channel_name': channel_name,
                'client_id': client_id,
                'client_secret': client_secret,
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token or '',
                'token_expiry': credentials.expiry,
                'is_active': True,
            }
        )
        
        # Wyczyść dane z sesji
        request.session.pop('oauth_state', None)
        request.session.pop('yt_client_id', None)
        request.session.pop('yt_client_secret', None)
        
        action = 'połączone' if created else 'zaktualizowane'
        messages.success(request, f'✅ Konto YouTube "{channel_name}" zostało {action}!')
        return redirect('uploader:connect_youtube')
        
    except Exception as e:
        logger.error(f'OAuth callback error: {str(e)}')
        messages.error(request, f'❌ Błąd podczas autoryzacji: {str(e)}')
        return redirect('uploader:connect_youtube')


@login_required
def youtube_refresh_token(request):
    """Odświeża token dostępu YouTube"""
    from .youtube_service import refresh_credentials_if_needed
    
    yt_account = YTAccount.objects.filter(user=request.user).first()
    
    if not yt_account:
        messages.error(request, 'Brak połączonego konta YouTube.')
        return redirect('uploader:connect_youtube')
    
    try:
        if refresh_credentials_if_needed(yt_account):
            messages.success(request, '✅ Token dostępu został odświeżony.')
        else:
            messages.error(request, '❌ Nie udało się odświeżyć tokena. Połącz konto ponownie.')
    except Exception as e:
        messages.error(request, f'Błąd odświeżania tokena: {str(e)}')
    
    return redirect('uploader:connect_youtube')


@login_required
def disconnect_youtube(request):
    if request.method == 'POST':
        try:
            yt_account = YTAccount.objects.filter(user=request.user).first()
            if yt_account:
                channel_name = yt_account.channel_name
                yt_account.delete()
                messages.success(request, f'✅ Konto YouTube "{channel_name}" zostało odłączone.')
            else:
                messages.info(request, 'ℹ️ Brak połączonego konta YouTube.')
        except Exception as e:
            logger.error(f'Error disconnecting YouTube account for user {request.user.id}: {str(e)}')
            messages.error(request, f'❌ Błąd podczas odłączania konta: {str(e)}')
        return redirect('uploader:connect_youtube')
    return redirect('uploader:connect_youtube')


# ============================================================================
# API
# ============================================================================

@login_required
def api_video_status(request, pk):
    try:
        video = get_object_or_404(Video, pk=pk, user=request.user)
        data = {
            'status': video.status,
            'shorts_count': video.get_shorts_count(),
            'duration': video.duration,
            'resolution': video.resolution,
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f'Error getting video status {pk}: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_video_progress(request, pk):
    """API endpoint zwracający postęp przetwarzania wideo"""
    try:
        video = get_object_or_404(Video, pk=pk, user=request.user)
        data = {
            'status': video.status,
            'progress': video.processing_progress,
            'message': video.processing_message,
            'shorts_total': video.shorts_total,
            'shorts_created': video.shorts_created,
            'is_processing': video.status == 'processing',
            'is_completed': video.status == 'completed',
            'is_failed': video.status == 'failed',
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f'Error getting video progress {pk}: {str(e)}')
        return JsonResponse({'error': str(e), 'is_failed': True}, status=500)
