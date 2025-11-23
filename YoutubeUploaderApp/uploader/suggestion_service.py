"""
Serwis generujący sugestie optymalizacji dla shortów
"""
from .models import Short, ShortSuggestion
from django.db.models import Avg
import re
from datetime import datetime


class ShortSuggestionService:
    """Serwis generujący sugestie poprawy dla shortsów"""
    
    def __init__(self, short):
        self.short = short
        self.suggestions = []
    
    def generate_all_suggestions(self, force_refresh=False):
        """
        Generuj wszystkie sugestie dla shorta
        
        Args:
            force_refresh: Jeśli True, usuń stare sugestie i wygeneruj nowe
        """
        # Jeśli short nie jest opublikowany, nie generuj sugestii
        if not self.short.is_published():
            return []
        
        # Usuń stare sugestie jeśli force_refresh
        if force_refresh:
            ShortSuggestion.objects.filter(short=self.short, is_resolved=False).delete()
        
        # Sprawdź czy mamy już sugestie
        existing_suggestions = ShortSuggestion.objects.filter(short=self.short, is_resolved=False)
        if existing_suggestions.exists() and not force_refresh:
            return list(existing_suggestions)
        
        # Generuj nowe sugestie
        self.check_title()
        self.check_description()
        self.check_engagement()
        self.check_retention()
        self.check_ctr()
        self.check_timing()
        
        # Zapisz sugestie do bazy
        self._save_suggestions()
        
        return self.suggestions
    
    def check_title(self):
        """Sprawdź tytuł"""
        title = self.short.title or ""
        
        # Długość tytułu
        if len(title) < 30:
            self.suggestions.append({
                'category': 'title',
                'priority': 'high',
                'title': 'Tytuł jest za krótki',
                'description': f'Twój tytuł ma tylko {len(title)} znaków. Optymalna długość to 40-60 znaków. Dłuższy tytuł lepiej opisuje treść i może poprawić CTR.',
                'metric_name': 'title_length',
                'current_value': len(title),
                'target_value': 50,
            })
        
        if len(title) > 70:
            self.suggestions.append({
                'category': 'title',
                'priority': 'medium',
                'title': 'Tytuł może być skrócony',
                'description': f'Tytuł ma {len(title)} znaków. W mobilnych wynikach wyszukiwania może być obcięty. Rozważ skrócenie do 60-70 znaków.',
                'metric_name': 'title_length',
                'current_value': len(title),
                'target_value': 60,
            })
        
        # Brak liczb/emocji
        if not re.search(r'\d+', title) and not any(word in title.lower() for word in ['jak', 'dlaczego', 'najlepsze', 'top', '!', '?']):
            self.suggestions.append({
                'category': 'title',
                'priority': 'medium',
                'title': 'Dodaj liczby lub słowa kluczowe',
                'description': 'Tytuły z liczbami (np. "5 sposobów...") lub słowami typu "Jak", "Najlepsze", "Top" mają lepszy CTR (Click-Through Rate).',
                'metric_name': 'title_engagement',
                'current_value': 0,
                'target_value': 1,
            })
        
        # Brak wielkich liter na początku
        if title and not title[0].isupper():
            self.suggestions.append({
                'category': 'title',
                'priority': 'low',
                'title': 'Popraw kapitalizację',
                'description': 'Tytuł powinien zaczynać się wielką literą. To sprawia, że wygląda bardziej profesjonalnie.',
                'metric_name': 'title_format',
                'current_value': 0,
                'target_value': 1,
            })
    
    def check_description(self):
        """Sprawdź opis"""
        desc = self.short.description or ""
        
        if len(desc) < 100:
            self.suggestions.append({
                'category': 'description',
                'priority': 'high',
                'title': 'Opis jest za krótki',
                'description': f'Opis ma tylko {len(desc)} znaków. Dodaj więcej szczegółów (min. 200 znaków). Dłuższy opis pomaga w SEO i może zawierać więcej słów kluczowych.',
                'metric_name': 'description_length',
                'current_value': len(desc),
                'target_value': 200,
            })
        
        # Policz hashtagi używając regex (słowa zaczynające się od #)
        hashtag_pattern = r'#\w+'
        hashtags = re.findall(hashtag_pattern, desc) if desc else []
        hashtags_count = len(hashtags)
        
        # Sprawdź tagi (z pola tags) + hashtagi (z opisu)
        tags_list = []
        if self.short.tags:
            tags_list = [t.strip() for t in re.split(r'[,\s]+', self.short.tags) if t.strip()]
        
        total_tags = len(tags_list) + hashtags_count
        
        # Brak tagów/hashtagów lub za mało
        if total_tags == 0:
            self.suggestions.append({
                'category': 'description',
                'priority': 'high',
                'title': 'Dodaj tagi i hashtagi',
                'description': 'Brak tagów i hashtagów. Dodaj:\n• 5-10 tagów w polu "Tagi" (np. fitness motywacja trening)\n• 3-5 hashtagów w opisie (np. #shorts #fitness #tutorial)\n\nTo zwiększy odkrywalność wideo.',
                'metric_name': 'total_tags',
                'current_value': 0,
                'target_value': 8,
            })
        elif total_tags < 5:
            tags_info = []
            if tags_list:
                tags_info.append(f"{len(tags_list)} tagi: {' '.join(tags_list[:3])}")
            if hashtags:
                tags_info.append(f"{hashtags_count} hashtagi: {' '.join(hashtags[:3])}")
            
            self.suggestions.append({
                'category': 'description',
                'priority': 'medium',
                'title': 'Dodaj więcej tagów/hashtagów',
                'description': f'Masz tylko {total_tags} tagi/hashtagi:\n• {" + ".join(tags_info) if tags_info else "brak"}\n\nDodaj jeszcze {5 - total_tags}, żeby osiągnąć optymalne 5-15.',
                'metric_name': 'total_tags',
                'current_value': total_tags,
                'target_value': 8,
            })
        
        # Za dużo hashtagów w opisie (YouTube limit)
        if hashtags_count > 15:
            self.suggestions.append({
                'category': 'description',
                'priority': 'medium',
                'title': 'Za dużo hashtagów',
                'description': f'Masz {hashtags_count} hashtagów. YouTube ignoruje wszystkie hashtagi jeśli jest ich więcej niż 15. Ogranicz do 3-5 najważniejszych.',
                'metric_name': 'hashtags_count',
                'current_value': hashtags_count,
                'target_value': 5,
            })
        
        # Brak linków/CTA
        if 'http' not in desc.lower() and 'link' not in desc.lower():
            self.suggestions.append({
                'category': 'description',
                'priority': 'low',
                'title': 'Dodaj linki lub CTA',
                'description': 'Rozważ dodanie linków do innych twoich filmów, social media lub strony internetowej. To zwiększa zaangażowanie.',
                'metric_name': 'has_links',
                'current_value': 0,
                'target_value': 1,
            })
    
    def check_engagement(self):
        """Sprawdź engagement rate"""
        if self.short.views < 100:
            return  # Za mało danych
        
        engagement = self.short.engagement_rate
        
        # Średni engagement dla Shorts to ~3-5%
        if engagement < 2:
            self.suggestions.append({
                'category': 'engagement',
                'priority': 'critical',
                'title': 'Niski wskaźnik zaangażowania',
                'description': f'Twój engagement rate ({engagement:.2f}%) jest poniżej średniej (3-5%). Spróbuj:\n• Dodać pytanie w pierwszym komentarzu\n• Zachęcić do zostawienia lajka na końcu wideo\n• Odpowiadać na komentarze w pierwszych 24h',
                'metric_name': 'engagement_rate',
                'current_value': engagement,
                'target_value': 3.0,
            })
        
        # Mało komentarzy w stosunku do wyświetleń
        if self.short.views > 1000 and self.short.comments < 10:
            comment_ratio = (self.short.comments / self.short.views) * 100
            self.suggestions.append({
                'category': 'engagement',
                'priority': 'high',
                'title': 'Zachęć do komentowania',
                'description': f'Masz tylko {self.short.comments} komentarzy na {self.short.views} wyświetleń ({comment_ratio:.2f}%). Dodaj "call to action" - zadaj pytanie widzom w opisie lub w pierwszym komentarzu.',
                'metric_name': 'comments_ratio',
                'current_value': comment_ratio,
                'target_value': 1.0,
            })
    
    def check_retention(self):
        """Sprawdź retention rate"""
        if self.short.views < 100:
            return
        
        retention = self.short.retention_rate
        
        # Dla Shorts, retention powinno być >70%
        if retention < 50:
            self.suggestions.append({
                'category': 'content',
                'priority': 'critical',
                'title': 'Niska retencja widzów',
                'description': f'Tylko {retention:.1f}% widzów ogląda do końca. Dla Shorts cel to >70%. Spróbuj:\n• Przyciągnąć uwagę w pierwszych 3 sekundach (hook)\n• Usunąć nudne fragmenty\n• Dodać dynamiczne cięcia\n• Skrócić wideo',
                'metric_name': 'retention_rate',
                'current_value': retention,
                'target_value': 70.0,
            })
        elif retention < 70:
            self.suggestions.append({
                'category': 'content',
                'priority': 'high',
                'title': 'Popraw retencję',
                'description': f'Retencja {retention:.1f}% jest OK, ale może być lepsza. Cel dla Shorts: >70%. W YouTube Analytics sprawdź gdzie widzowie przestają oglądać i popraw te momenty.',
                'metric_name': 'retention_rate',
                'current_value': retention,
                'target_value': 70.0,
            })
    
    def check_ctr(self):
        """Sprawdź Click-Through Rate"""
        if self.short.views < 100:
            return
        
        ctr = self.short.click_through_rate
        
        # Średni CTR dla Shorts to ~4-6%
        if ctr > 0 and ctr < 3:
            self.suggestions.append({
                'category': 'thumbnail',
                'priority': 'high',
                'title': 'Niski CTR - optymalizuj miniaturę',
                'description': f'CTR ({ctr:.2f}%) jest niski (cel: >4%). Optymalizuj miniaturę:\n• Użyj jasnych, kontrastowych kolorów\n• Dodaj wyraźny tekst (duży, czytelny)\n• Pokaż emocje na twarzy\n• Stwórz intrygę',
                'metric_name': 'click_through_rate',
                'current_value': ctr,
                'target_value': 4.0,
            })
    
    def check_timing(self):
        """Sprawdź timing publikacji"""
        if not self.short.published_at:
            return
        
        if self.short.views < 100:
            return  # Za wcześnie na analizę timingu
        
        upload_hour = self.short.published_at.hour
        upload_day = self.short.published_at.weekday()
        
        # Najlepsze godziny: 12-15, 18-22
        # Najlepsze dni: piątek(4)-niedziela(6)
        if upload_hour < 12 or (upload_hour > 15 and upload_hour < 18) or upload_hour > 22:
            self.suggestions.append({
                'category': 'timing',
                'priority': 'medium',
                'title': 'Nieoptymalna godzina publikacji',
                'description': f'Opublikowałeś o {upload_hour}:00. Najlepsze godziny na Shorts to:\n• 12:00-15:00 (lunch break)\n• 18:00-22:00 (po pracy/szkole)\n\nRozważ publikację w tych godzinach przy następnym shorcie.',
                'metric_name': 'publish_hour',
                'current_value': upload_hour,
                'target_value': 19.0,
            })
        
        # Sprawdź dzień tygodnia (0=poniedziałek, 6=niedziela)
        if upload_day < 4:  # Poniedziałek-Czwartek
            days_pl = ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota', 'niedziela']
            self.suggestions.append({
                'category': 'timing',
                'priority': 'low',
                'title': 'Rozważ publikację w weekend',
                'description': f'Opublikowałeś w {days_pl[upload_day]}. Shorty często osiągają lepsze wyniki w weekend (piątek-niedziela), gdy ludzie mają więcej czasu na przeglądanie social media.',
                'metric_name': 'publish_day',
                'current_value': upload_day,
                'target_value': 5.0,
            })
    
    def _save_suggestions(self):
        """Zapisz wygenerowane sugestie do bazy danych"""
        for suggestion_data in self.suggestions:
            ShortSuggestion.objects.create(
                short=self.short,
                **suggestion_data
            )
