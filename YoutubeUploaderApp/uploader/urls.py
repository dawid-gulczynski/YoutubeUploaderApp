from django.urls import path
from . import views

app_name = 'uploader'

urlpatterns = [
    # Strona główna
    path('', views.home_view, name='home'),
    
    # Autentykacja
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    
    # Google OAuth (własna implementacja)
    path('auth/google/', views.google_login_direct, name='google_login_direct'),
    path('auth/google/callback/', views.google_callback, name='google_callback'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/user/', views.user_dashboard, name='user_dashboard'),
    path('dashboard/moderator/', views.moderator_dashboard, name='moderator_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # Wideo
    path('videos/', views.VideoListView.as_view(), name='video_list'),
    path('videos/upload/', views.VideoUploadView.as_view(), name='video_upload'),
    path('videos/<int:pk>/', views.VideoDetailView.as_view(), name='video_detail'),
    path('videos/<int:pk>/delete/', views.video_delete, name='video_delete'),
    
    # Shorty
    path('shorts/', views.ShortListView.as_view(), name='short_list'),
    path('shorts/<int:pk>/', views.ShortDetailView.as_view(), name='short_detail'),
    path('shorts/<int:pk>/edit/', views.ShortEditView.as_view(), name='short_edit'),
    path('shorts/<int:pk>/publish/', views.short_publish, name='short_publish'),
    path('shorts/<int:pk>/refresh-stats/', views.short_refresh_stats, name='short_refresh_stats'),
    path('shorts/<int:pk>/delete/', views.short_delete, name='short_delete'),
    
    # YouTube Integration
    path('youtube/connect/', views.connect_youtube, name='connect_youtube'),
    path('youtube/oauth/', views.youtube_oauth, name='youtube_oauth'),
    path('youtube/oauth/start/', views.youtube_oauth_start, name='youtube_oauth_start'),
    path('youtube/oauth/callback/', views.youtube_oauth_callback, name='youtube_oauth_callback'),
    path('youtube/disconnect/', views.disconnect_youtube, name='youtube_disconnect'),
    path('youtube/refresh/', views.youtube_refresh_token, name='youtube_refresh'),
    
    # API Endpoints
    path('api/video/<int:pk>/status/', views.api_video_status, name='api_video_status'),
    path('api/video/<int:pk>/progress/', views.api_video_progress, name='api_video_progress'),
]
