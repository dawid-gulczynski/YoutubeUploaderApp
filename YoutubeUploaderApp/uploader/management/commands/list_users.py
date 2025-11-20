from django.core.management.base import BaseCommand
from uploader.models import User


class Command(BaseCommand):
    help = 'Wyświetla listę wszystkich użytkowników z ich rolami'

    def add_arguments(self, parser):
        parser.add_argument('--role', type=str, choices=['user', 'moderator', 'admin'], 
                          help='Filtruj według roli')

    def handle(self, *args, **kwargs):
        role_filter = kwargs.get('role')
        
        users = User.objects.select_related('role').all()
        
        if role_filter:
            users = users.filter(role__symbol=role_filter)
        
        if not users.exists():
            self.stdout.write(self.style.WARNING('Brak użytkowników w systemie.'))
            return
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('LISTA UŻYTKOWNIKÓW'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        for user in users:
            role_name = user.role.name if user.role else 'Brak roli'
            role_symbol = user.role.symbol if user.role else 'none'
            
            # Koloruj według roli
            if role_symbol == 'admin':
                style = self.style.ERROR  # Czerwony
            elif role_symbol == 'moderator':
                style = self.style.WARNING  # Żółty
            else:
                style = self.style.SUCCESS  # Zielony
            
            superuser_mark = ' [SUPERUSER]' if user.is_superuser else ''
            active_mark = '' if user.is_active else ' [NIEAKTYWNY]'
            
            self.stdout.write(
                style(
                    f'\n{user.username}{superuser_mark}{active_mark}\n'
                    f'  Email: {user.email}\n'
                    f'  Rola: {role_name}\n'
                    f'  Data dołączenia: {user.date_joined.strftime("%Y-%m-%d %H:%M")}\n'
                    f'  Metoda logowania: {user.auth_provider}'
                )
            )
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(
            self.style.SUCCESS(f'Łącznie użytkowników: {users.count()}')
        )
