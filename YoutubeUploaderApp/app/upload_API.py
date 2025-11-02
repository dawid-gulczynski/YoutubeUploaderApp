import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# working upload python script

# Define scopes required for YouTube Data API access
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    # Create the OAuth2 flow instance
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secrets.json', SCOPES)

    # Perform the OAuth2 flow
    credentials = flow.run_local_server()

    # Build the YouTube service
    youtube = build('youtube', 'v3', credentials=credentials)

    return youtube

def upload_youtube_short(video_path, title, description, keywords=[]):
    # Authenticate and build YouTube service
    youtube = get_authenticated_service()

    # Upload video
    request_body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': keywords,
            'categoryId': '24'  # Category ID for Short Films Entertainment
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    media_file = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    response_upload = youtube.videos().insert(
        part='snippet,status',
        body=request_body,
        media_body=media_file
    ).execute()

    video_id = response_upload.get('id')
    print(f"Video uploaded successfully! Video url: https://youtu.be/{video_id}")
    return video_id

if __name__ == "__main__":
    video_path = 'videoOUT1.mp4'
    title = 'videoOUT1 #shorts #minecraft #cave'
    description = 'videoOUT1 #shorts #minecraft #cave'
    keywords = 'minecraft'
    # keywords = input("Enter keywords (comma-separated) for the YouTube Short: ").split(",")

    upload_youtube_short(video_path, title, description, keywords)
