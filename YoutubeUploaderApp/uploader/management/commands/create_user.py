from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from uploader.models import Role, User


class Command(BaseCommand):
    help = 'Tworzy nowego użytkownika z przypisaną rolą'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nazwa użytkownika')
        parser.add_argument('email', type=str, help='Email użytkownika')
        parser.add_argument('password', type=str, help='Hasło użytkownika')
        parser.add_argument('--role', type=str, choices=['user', 'moderator', 'admin'], 
                          default='user', help='Rola użytkownika (domyślnie: user)')
        parser.add_argument('--superuser', action='store_true', 
                          help='Utworz jako superuser (dostęp do Django admin)')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        email = kwargs['email']
        password = kwargs['password']
        role_symbol = kwargs['role']
        is_superuser = kwargs['superuser']
        
        # Sprawdź czy użytkownik już istnieje
        if User.objects.filter(username=username).exists():
            raise CommandError(f'❌ Użytkownik "{username}" już istnieje!')
        
        if User.objects.filter(email=email).exists():
            raise CommandError(f'❌ Email "{email}" jest już zajęty!')
        
        # Pobierz rolę
        try:
            role = Role.objects.get(symbol=role_symbol)
        except Role.DoesNotExist:
            raise CommandError(
                f'❌ Rola "{role_symbol}" nie istnieje! '
                f'Uruchom najpierw: python manage.py init_roles'
            )
        
        # Utwórz użytkownika
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            role=role,
            is_staff=is_superuser,
            is_superuser=is_superuser,
            is_active=True,
            email_verified=True,
            auth_provider='local'
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Utworzono użytkownika:\n'
                f'  Username: {username}\n'
                f'  Email: {email}\n'
                f'  Rola: {role.name}\n'
                f'  Superuser: {"Tak" if is_superuser else "Nie"}'
            )
        )
