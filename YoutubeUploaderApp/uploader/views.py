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
# AUTENTYKACJA
# ============================================================================

def register_view(request):
    """Widok rejestracji użytkownika"""
    if request.user.is_authenticated:
        return redirect('uploader:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user_role = Role.objects.get(symbol='user')
            user.role = user_role
            user.save()
            messages.success(request, 'Konto zostało utworzone! Możesz się teraz zalogować.')
            return redirect('uploader:login')
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
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Witaj, {user.username}!')
                return redirect('uploader:dashboard')
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
            form.save()
            messages.success(request, 'Profil został zaktualizowany.')
            return redirect('uploader:profile_edit')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'uploader/auth/profile_edit.html', {'form': form})


# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
def dashboard_view(request):
    """Główny dashboard"""
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
        video = form.save(commit=False)
        video.user = self.request.user
        video.status = 'uploaded'
        video.save()
        
        if not check_ffmpeg_installed():
            messages.warning(self.request, 'Wideo zostało wgrane, ale FFmpeg nie jest zainstalowany. Shorty nie zostaną wygenerowane. Zobacz FFMPEG_INSTALL.md')
        else:
            messages.success(self.request, 'Wideo zostało wgrane! Rozpoczynam przetwarzanie...')
            crop_mode = self.request.POST.get('crop_mode', 'center')
            thread = threading.Thread(target=process_video_async, args=(video.id, crop_mode))
            thread.start()
        
        return redirect('uploader:video_detail', pk=video.pk)


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
        video.delete()
        messages.success(request, 'Wideo zostało usunięte.')
        return redirect('uploader:video_list')
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
        if status:
            queryset = queryset.filter(upload_status=status)
        return queryset.order_by('-created_at')


class ShortDetailView(LoginRequiredMixin, DetailView):
    model = Short
    template_name = 'uploader/short/short_detail.html'
    context_object_name = 'short'
    
    def get_queryset(self):
        return Short.objects.filter(video__user=self.request.user)


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
        video_id = short.video.id
        short.delete()
        messages.success(request, 'Short został usunięty.')
        return redirect('uploader:video_detail', pk=video_id)
    return render(request, 'uploader/short/short_confirm_delete.html', {'short': short})


# ============================================================================
# YOUTUBE
# ============================================================================

@login_required
def connect_youtube(request):
    yt_account = YTAccount.objects.filter(user=request.user).first()
    return render(request, 'uploader/youtube/connect.html', {'yt_account': yt_account})


@login_required
def youtube_oauth(request):
    """Inicjuje proces OAuth 2.0 z Google/YouTube"""
    from google_auth_oauthlib.flow import Flow
    from django.conf import settings
    import os
    
    # Sprawdź czy plik client_secrets.json istnieje
    client_secrets_path = os.path.join(settings.BASE_DIR, 'client_secrets.json')
    
    if not os.path.exists(client_secrets_path):
        messages.error(
            request, 
            'Brak pliku client_secrets.json! Zobacz plik GOOGLE_API_SETUP.md aby skonfigurować Google API.'
        )
        return redirect('uploader:connect_youtube')
    
    try:
        # Utwórz OAuth flow
        flow = Flow.from_client_secrets_file(
            client_secrets_path,
            scopes=[
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube.readonly',
                'https://www.googleapis.com/auth/youtube.force-ssl'
            ],
            redirect_uri=request.build_absolute_uri(reverse('uploader:youtube_oauth_callback'))
        )
        
        # Generuj authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',  # Offline access dla refresh token
            include_granted_scopes='true',
            prompt='consent'  # Zawsze pytaj o consent aby dostać refresh token
        )
        
        # Zapisz state w sesji dla weryfikacji w callback
        request.session['oauth_state'] = state
        
        # Przekieruj użytkownika do Google
        return redirect(authorization_url)
        
    except Exception as e:
        messages.error(request, f'Błąd inicjalizacji OAuth: {str(e)}')
        logger.error(f'OAuth initialization error: {str(e)}')
        return redirect('uploader:connect_youtube')


@login_required
def youtube_oauth_callback(request):
    """Callback po autoryzacji OAuth"""
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from django.conf import settings
    import os
    
    # Pobierz state z sesji
    state = request.session.get('oauth_state')
    if not state:
        messages.error(request, 'Błąd: Brak state w sesji. Spróbuj ponownie.')
        return redirect('uploader:connect_youtube')
    
    client_secrets_path = os.path.join(settings.BASE_DIR, 'client_secrets.json')
    
    try:
        # Utwórz OAuth flow ze state
        flow = Flow.from_client_secrets_file(
            client_secrets_path,
            scopes=[
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube.readonly',
                'https://www.googleapis.com/auth/youtube.force-ssl'
            ],
            state=state,
            redirect_uri=request.build_absolute_uri(reverse('uploader:youtube_oauth_callback'))
        )
        
        # Fetch token używając authorization response
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        
        # Pobierz credentials
        credentials = flow.credentials
        
        # Pobierz informacje o kanale YouTube
        youtube = build('youtube', 'v3', credentials=credentials)
        channel_response = youtube.channels().list(
            part='snippet,contentDetails,statistics',
            mine=True
        ).execute()
        
        if not channel_response.get('items'):
            messages.error(request, 'Nie znaleziono kanału YouTube dla tego konta.')
            return redirect('uploader:connect_youtube')
        
        channel = channel_response['items'][0]
        channel_id = channel['id']
        channel_name = channel['snippet']['title']
        
        # Zapisz lub zaktualizuj YTAccount
        yt_account, created = YTAccount.objects.get_or_create(
            user=request.user,
            channel_id=channel_id,
            defaults={
                'channel_name': channel_name,
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expiry': credentials.expiry
            }
        )
        
        if not created:
            # Zaktualizuj istniejące konto
            yt_account.channel_name = channel_name
            yt_account.access_token = credentials.token
            if credentials.refresh_token:  # Refresh token może nie być zwrócony jeśli już istnieje
                yt_account.refresh_token = credentials.refresh_token
            yt_account.token_expiry = credentials.expiry
            yt_account.save()
        
        # Wyczyść state z sesji
        del request.session['oauth_state']
        
        messages.success(request, f'✅ Konto YouTube "{channel_name}" zostało pomyślnie połączone!')
        return redirect('uploader:connect_youtube')
        
    except Exception as e:
        messages.error(request, f'Błąd podczas autoryzacji: {str(e)}')
        logger.error(f'OAuth callback error: {str(e)}')
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
        yt_account = YTAccount.objects.filter(user=request.user).first()
        if yt_account:
            yt_account.delete()
            messages.success(request, 'Konto YouTube zostało odłączone.')
        return redirect('uploader:connect_youtube')
    return redirect('uploader:connect_youtube')


# ============================================================================
# API
# ============================================================================

@login_required
def api_video_status(request, pk):
    video = get_object_or_404(Video, pk=pk, user=request.user)
    data = {
        'status': video.status,
        'shorts_count': video.get_shorts_count(),
        'duration': video.duration,
        'resolution': video.resolution,
    }
    return JsonResponse(data)


@login_required
def api_video_progress(request, pk):
    """API endpoint zwracający postęp przetwarzania wideo"""
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
