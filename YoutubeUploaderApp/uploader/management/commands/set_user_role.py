from django.core.management.base import BaseCommand, CommandError
from uploader.models import Role, User


class Command(BaseCommand):
    help = 'Nadaje rolę użytkownikowi (user, moderator, admin)'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nazwa użytkownika')
        parser.add_argument('role', type=str, choices=['user', 'moderator', 'admin'], 
                          help='Rola do nadania (user/moderator/admin)')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        role_symbol = kwargs['role']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'❌ Użytkownik "{username}" nie istnieje!')
        
        try:
            role = Role.objects.get(symbol=role_symbol)
        except Role.DoesNotExist:
            raise CommandError(
                f'❌ Rola "{role_symbol}" nie istnieje! '
                f'Uruchom najpierw: python manage.py init_roles'
            )
        
        old_role = user.role.name if user.role else 'Brak'
        user.role = role
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Zmieniono rolę użytkownika "{username}"\n'
                f'  Poprzednia rola: {old_role}\n'
                f'  Nowa rola: {role.name}'
            )
        )
