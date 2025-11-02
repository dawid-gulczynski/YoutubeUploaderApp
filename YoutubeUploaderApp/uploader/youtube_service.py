"""
Serwis do integracji z YouTube Data API v3
"""
import os
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Define scopes required for YouTube Data API access
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]


def refresh_credentials_if_needed(yt_account):
    """
    Odświeża credentials jeśli wygasły
    
    Args:
        yt_account: Obiekt YTAccount
        
    Returns:
        bool: True jeśli token jest ważny lub został odświeżony
    """
    try:
        # Sprawdź czy token wygasł
        if yt_account.token_expiry and timezone.now() >= yt_account.token_expiry:
            logger.info(f"Token expired for {yt_account.channel_name}, refreshing...")
            
            # Pobierz client_secrets dla refresh
            client_secrets_path = os.path.join(settings.BASE_DIR, 'client_secrets.json')
            
            if not os.path.exists(client_secrets_path):
                logger.error("client_secrets.json not found")
                return False
            
            # Załaduj dane klienta
            import json
            with open(client_secrets_path) as f:
                client_config = json.load(f)
                client_id = client_config['web']['client_id']
                client_secret = client_config['web']['client_secret']
            
            # Utwórz credentials z refresh token
            credentials = Credentials(
                token=yt_account.access_token,
                refresh_token=yt_account.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES
            )
            
            # Odśwież token
            credentials.refresh(Request())
            
            # Zapisz nowy token
            yt_account.access_token = credentials.token
            yt_account.token_expiry = credentials.expiry
            yt_account.save()
            
            logger.info(f"Token refreshed successfully for {yt_account.channel_name}")
            return True
        
        return True
        
    except Exception as e:
        logger.error(f"Error refreshing credentials: {str(e)}")
        return False


def get_authenticated_service(yt_account):
    """
    Tworzy authenticated YouTube service
    
    Args:
        yt_account: Obiekt YTAccount z tokenami OAuth
    
    Returns:
        googleapiclient.discovery.Resource: YouTube service object
    """
    # Odśwież token jeśli potrzeba
    if not refresh_credentials_if_needed(yt_account):
        raise Exception("Nie udało się odświeżyć tokena. Połącz konto ponownie.")
    
    # Pobierz client config
    client_secrets_path = os.path.join(settings.BASE_DIR, 'client_secrets.json')
    import json
    with open(client_secrets_path) as f:
        client_config = json.load(f)
        client_id = client_config['web']['client_id']
        client_secret = client_config['web']['client_secret']
    
    # Utwórz credentials
    credentials = Credentials(
        token=yt_account.access_token,
        refresh_token=yt_account.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    
    # Zbuduj service
    youtube = build('youtube', 'v3', credentials=credentials)
    return youtube


def upload_short_to_youtube(short, yt_account):
    """
    Upload shorta na YouTube
    
    Args:
        short: Obiekt Short z bazy danych
        yt_account: Obiekt YTAccount z tokenami OAuth
    
    Returns:
        dict: {'success': bool, 'video_id': str, 'error': str}
    """
    try:
        youtube = get_authenticated_service(yt_account)
        
        # Przygotuj metadata wideo
        request_body = {
            'snippet': {
                'title': short.title[:100],  # YouTube limit 100 znaków
                'description': short.description[:5000] if short.description else '',  # Limit 5000
                'categoryId': '24',  # Entertainment
                'tags': ['shorts', 'short', 'viral'],
            },
            'status': {
                'privacyStatus': short.privacy_status,
                'selfDeclaredMadeForKids': short.made_for_kids,
            }
        }
        
        # Dodaj harmonogram jeśli ustawiony
        if short.scheduled_at and short.scheduled_at > timezone.now():
            request_body['status']['publishAt'] = short.scheduled_at.isoformat()
            request_body['status']['privacyStatus'] = 'private'  # Musi być private dla scheduled
        
        # Przygotuj plik do uploadu
        media_file = MediaFileUpload(
            short.short_file.path,
            chunksize=1024*1024,  # 1MB chunks
            resumable=True,
            mimetype='video/mp4'
        )
        
        # Upload wideo
        logger.info(f"Uploading short {short.id} to YouTube...")
        request = youtube.videos().insert(
            part='snippet,status',
            body=request_body,
            media_body=media_file
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Upload progress: {int(status.progress() * 100)}%")
        
        video_id = response.get('id')
        video_url = f"https://youtu.be/{video_id}"
        
        logger.info(f"Short uploaded successfully! URL: {video_url}")
        
        return {
            'success': True,
            'video_id': video_id,
            'video_url': video_url,
            'error': None
        }
        
    except HttpError as e:
        error_msg = f"HTTP Error {e.resp.status}: {e.error_details}"
        logger.error(f"YouTube API error: {error_msg}")
        return {
            'success': False,
            'video_id': None,
            'error': error_msg
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Upload error: {error_msg}")
        return {
            'success': False,
            'video_id': None,
            'error': error_msg
        }


def get_youtube_trending_tags(category='gaming', region='PL'):
    """
    Pobiera trendujące tagi z YouTube
    
    Args:
        category: Kategoria wideo
        region: Kod regionu (PL, US, etc.)
    
    Returns:
        list: Lista trendujących tagów
    """
    # TODO: Implementacja z YouTube Data API
    # Tymczasowo zwracamy przykładowe tagi
    trending_tags = [
        'shorts', 'viral', 'trending', 'fyp', 'foryou',
        'gaming', 'minecraft', 'fortnite', 'roblox',
        'funny', 'comedy', 'challenge', 'prank',
        'tutorial', 'howto', 'tips', 'tricks'
    ]
    return trending_tags


def get_channel_info(yt_account):
    """Pobiera informacje o kanale YouTube"""
    try:
        youtube = get_authenticated_service(yt_account)
        
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            mine=True
        )
        response = request.execute()
        
        if response['items']:
            return response['items'][0]
        return None
    except Exception as e:
        logger.error(f"Error getting channel info: {str(e)}")
        return None


def get_video_analytics(yt_account, video_id):
    """Pobiera analitykę dla konkretnego wideo"""
    try:
        youtube = get_authenticated_service(yt_account)
        
        request = youtube.videos().list(
            part="statistics",
            id=video_id
        )
        response = request.execute()
        
        if response['items']:
            stats = response['items'][0]['statistics']
            return {
                'views': int(stats.get('viewCount', 0)),
                'likes': int(stats.get('likeCount', 0)),
                'comments': int(stats.get('commentCount', 0)),
            }
        return None
    except Exception as e:
        logger.error(f"Error getting video analytics: {str(e)}")
        return None
