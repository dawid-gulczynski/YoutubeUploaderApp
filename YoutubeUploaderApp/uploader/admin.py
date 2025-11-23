from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, YTAccount, Video, Short, ShortSuggestion


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol')
    search_fields = ('name', 'symbol')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'email_verified', 'is_staff', 'date_joined')
    list_filter = ('role', 'email_verified', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Dodatkowe informacje', {
            'fields': ('role', 'email_verified', 'google_id')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Dodatkowe informacje', {
            'fields': ('email', 'role')
        }),
    )


@admin.register(YTAccount)
class YTAccountAdmin(admin.ModelAdmin):
    list_display = ('channel_name', 'user', 'channel_id', 'created_at', 'is_token_valid')
    list_filter = ('created_at',)
    search_fields = ('channel_name', 'channel_id', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informacje o kanale', {
            'fields': ('user', 'channel_name', 'channel_id')
        }),
        ('Tokeny OAuth', {
            'fields': ('access_token', 'refresh_token', 'token_expiry'),
            'classes': ('collapse',)
        }),
        ('Daty', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'get_shorts_count', 'duration', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'get_shorts_count')
    
    fieldsets = (
        ('Informacje o wideo', {
            'fields': ('user', 'title', 'description', 'video_file')
        }),
        ('Metadane', {
            'fields': ('duration', 'resolution', 'file_size')
        }),
        ('Parametry cięcia', {
            'fields': ('target_duration', 'max_shorts_count')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Daty', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Short)
class ShortAdmin(admin.ModelAdmin):
    list_display = ('title', 'video', 'upload_status', 'order', 'duration', 'views', 'tags_count', 'hashtags_count', 'created_at')
    list_filter = ('upload_status', 'privacy_status', 'made_for_kids', 'created_at')
    search_fields = ('title', 'description', 'tags', 'yt_video_id', 'video__title')
    readonly_fields = ('created_at', 'updated_at', 'published_at', 'yt_url', 'tags_count', 'hashtags_count')
    
    fieldsets = (
        ('Informacje podstawowe', {
            'fields': ('video', 'title', 'description', 'tags', 'short_file', 'thumbnail')
        }),
        ('Parametry cięcia', {
            'fields': ('start_time', 'duration', 'order')
        }),
        ('Publikacja', {
            'fields': ('upload_status', 'privacy_status', 'scheduled_at', 'made_for_kids')
        }),
        ('YouTube', {
            'fields': ('yt_video_id', 'yt_url')
        }),
        ('Statystyki', {
            'fields': ('views', 'likes', 'comments', 'shares', 'engagement_rate', 'retention_rate'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('title_length', 'description_length', 'tags_count', 'hashtags_count'),
            'classes': ('collapse',)
        }),
        ('Daty', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ShortSuggestion)
class ShortSuggestionAdmin(admin.ModelAdmin):
    list_display = ('short', 'category', 'priority', 'title', 'is_resolved', 'created_at')
    list_filter = ('category', 'priority', 'is_resolved', 'created_at')
    search_fields = ('title', 'description', 'short__title')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('short', 'category', 'priority', 'title', 'description')
        }),
        ('Metryki', {
            'fields': ('metric_name', 'current_value', 'target_value'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_resolved', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('short', 'short__video')
