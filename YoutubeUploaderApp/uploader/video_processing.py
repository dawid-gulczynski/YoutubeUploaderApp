"""
Serwis do cięcia wideo na shorty używając FFmpeg
"""
import subprocess
import os
import json
import shutil
from pathlib import Path
from django.conf import settings
from .models import Video, Short
import logging

logger = logging.getLogger(__name__)


def check_ffmpeg_installed():
    """Sprawdza czy FFmpeg jest zainstalowany"""
    ffmpeg_path = shutil.which('ffmpeg')
    ffprobe_path = shutil.which('ffprobe')
    
    if not ffmpeg_path or not ffprobe_path:
        logger.error("FFmpeg or FFprobe not found in PATH")
        return False
    
    logger.info(f"FFmpeg found at: {ffmpeg_path}")
    logger.info(f"FFprobe found at: {ffprobe_path}")
    return True


class VideoProcessingService:
    """Serwis do przetwarzania wideo"""
    
    def __init__(self, video: Video):
        self.video = video
        self.video_path = video.video_file.path
        
    def get_video_metadata(self):
        """Pobiera metadane wideo używając ffprobe"""
        if not check_ffmpeg_installed():
            raise Exception("FFmpeg nie jest zainstalowany! Zobacz FFMPEG_INSTALL.md")
        
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                self.video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)
            
            # Znajdź stream wideo
            video_stream = next(
                (s for s in metadata['streams'] if s['codec_type'] == 'video'),
                None
            )
            
            if not video_stream:
                raise Exception("Nie znaleziono streamu wideo")
            
            duration = float(metadata['format']['duration'])
            width = video_stream['width']
            height = video_stream['height']
            
            return {
                'duration': duration,
                'width': width,
                'height': height,
                'resolution': f"{width}x{height}",
                'file_size': int(metadata['format']['size'])
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error: {e.stderr}")
            raise Exception(f"Błąd analizy wideo: {e.stderr}")
        except Exception as e:
            logger.error(f"Metadata extraction error: {str(e)}")
            raise
    
    def update_video_metadata(self):
        """Aktualizuje metadane wideo w bazie danych"""
        metadata = self.get_video_metadata()
        self.video.duration = int(metadata['duration'])
        self.video.resolution = metadata['resolution']
        self.video.file_size = metadata['file_size']
        self.video.save()
        return metadata
    
    def cut_into_shorts(self, crop_mode='center'):
        """
        Dzieli wideo na shorty zgodnie z parametrami
        
        Args:
            crop_mode: Tryb kadrowania (center, smart, top)
        """
        if not check_ffmpeg_installed():
            self.video.status = 'failed'
            self.video.processing_message = 'FFmpeg nie jest zainstalowany'
            self.video.save()
            raise Exception("FFmpeg nie jest zainstalowany! Zobacz plik FFMPEG_INSTALL.md w głównym katalogu projektu.")
        
        # Aktualizuj status
        self.video.status = 'processing'
        self.video.processing_progress = 0
        self.video.processing_message = 'Rozpoczynanie przetwarzania...'
        self.video.save()
        
        try:
            # Pobierz metadane jeśli nie ma
            if not self.video.duration:
                self.video.processing_message = 'Analiza wideo...'
                self.video.save()
                self.update_video_metadata()
            
            duration = self.video.duration
            target_duration = self.video.target_duration
            max_shorts = self.video.max_shorts_count
            
            # Oblicz liczbę shortów
            num_shorts = min(int(duration / target_duration), max_shorts)
            
            if num_shorts == 0:
                raise Exception("Wideo jest zbyt krótkie do pocięcia")
            
            # Ustaw całkowitą liczbę shortów
            self.video.shorts_total = num_shorts
            self.video.processing_message = f'Tworzenie {num_shorts} shortów...'
            self.video.save()
            
            # Utwórz folder na shorty
            shorts_dir = Path(settings.MEDIA_ROOT) / 'shorts' / str(self.video.id)
            shorts_dir.mkdir(parents=True, exist_ok=True)
            
            # Generuj shorty
            shorts_created = []
            for i in range(num_shorts):
                start_time = i * target_duration
                
                # Nie przekraczaj długości wideo
                if start_time + target_duration > duration:
                    actual_duration = duration - start_time
                else:
                    actual_duration = target_duration
                
                # Nazwa pliku wyjściowego
                output_filename = f"short_{i+1}.mp4"
                output_path = shorts_dir / output_filename
                
                # Aktualizuj progress
                self.video.processing_message = f'Tworzenie shorta {i+1}/{num_shorts}...'
                self.video.processing_progress = int((i / num_shorts) * 100)
                self.video.save()
                
                # Wywołaj FFmpeg
                success = self._create_short_segment(
                    start_time=start_time,
                    duration=actual_duration,
                    output_path=str(output_path),
                    crop_mode=crop_mode
                )
                
                if success:
                    # Utwórz Short w bazie
                    short = Short.objects.create(
                        video=self.video,
                        title=f"{self.video.title} - Część {i+1}",
                        description=self.video.description,
                        short_file=f'shorts/{self.video.id}/{output_filename}',
                        start_time=start_time,
                        duration=int(actual_duration),
                        order=i+1
                    )
                    shorts_created.append(short)
                    
                    # Aktualizuj licznik utworzonych
                    self.video.shorts_created = i + 1
                    self.video.save()
                    
                    logger.info(f"Created short {i+1}/{num_shorts}")
            
            # Aktualizuj status - zakończono
            self.video.status = 'completed'
            self.video.processing_progress = 100
            self.video.processing_message = f'Gotowe! Utworzono {num_shorts} shortów.'
            self.video.save()
            
            return shorts_created
            
        except Exception as e:
            logger.error(f"Error cutting video: {str(e)}")
            self.video.status = 'failed'
            self.video.processing_message = f'Błąd: {str(e)}'
            self.video.save()
            raise
    
    def _create_short_segment(self, start_time, duration, output_path, crop_mode='center'):
        """
        Tworzy pojedynczy segment shorta z kadr

owaniem do 9:16
        
        Args:
            start_time: Czas rozpoczęcia w sekundach
            duration: Długość segmentu w sekundach
            output_path: Ścieżka do pliku wyjściowego
            crop_mode: Tryb kadrowania
        """
        try:
            # Filtry do kadrowania 9:16
            if crop_mode == 'center':
                # Wykadruj na środek
                crop_filter = "crop=ih*9/16:ih:x=(iw-oh)/2:y=0"
            elif crop_mode == 'top':
                # Wykadruj górę
                crop_filter = "crop=ih*9/16:ih:x=(iw-oh)/2:y=0"
            else:  # smart - można rozbudować o wykrywanie twarzy
                crop_filter = "crop=ih*9/16:ih:x=(iw-oh)/2:y=0"
            
            # Komenda FFmpeg
            cmd = [
                'ffmpeg',
                '-y',  # Nadpisz plik wyjściowy
                '-ss', str(start_time),  # Start time
                '-i', self.video_path,  # Input file
                '-t', str(duration),  # Duration
                '-vf', f"{crop_filter},scale=-2:1920",  # Crop i scale do 1080x1920
                '-c:v', 'libx264',  # Video codec
                '-preset', 'medium',  # Encoding preset
                '-crf', '23',  # Quality
                '-c:a', 'aac',  # Audio codec
                '-b:a', '128k',  # Audio bitrate
                '-movflags', '+faststart',  # Optimize for streaming
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return os.path.exists(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error creating short segment: {str(e)}")
            return False
    
    def generate_thumbnail(self, short: Short, time_offset=1):
        """Generuje miniaturkę dla shorta"""
        try:
            thumbnail_dir = Path(settings.MEDIA_ROOT) / 'thumbnails' / str(self.video.id)
            thumbnail_dir.mkdir(parents=True, exist_ok=True)
            
            thumbnail_filename = f"thumb_{short.order}.jpg"
            thumbnail_path = thumbnail_dir / thumbnail_filename
            
            # Wygeneruj miniaturkę z FFmpeg
            cmd = [
                'ffmpeg',
                '-y',
                '-ss', str(short.start_time + time_offset),
                '-i', self.video_path,
                '-vframes', '1',
                '-vf', 'scale=-2:1920',
                str(thumbnail_path)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Aktualizuj short
            short.thumbnail = f'thumbnails/{self.video.id}/{thumbnail_filename}'
            short.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating thumbnail: {str(e)}")
            return False


def process_video_async(video_id, crop_mode='center'):
    """
    Funkcja do asynchronicznego przetwarzania wideo
    Używana w tle (threading/celery)
    """
    try:
        video = Video.objects.get(id=video_id)
        service = VideoProcessingService(video)
        
        # Pobierz metadane
        service.update_video_metadata()
        
        # Pociąj na shorty
        shorts = service.cut_into_shorts(crop_mode=crop_mode)
        
        # Wygeneruj miniatury
        for short in shorts:
            service.generate_thumbnail(short)
        
        logger.info(f"Video {video_id} processed successfully. Created {len(shorts)} shorts.")
        return True
        
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        return False
