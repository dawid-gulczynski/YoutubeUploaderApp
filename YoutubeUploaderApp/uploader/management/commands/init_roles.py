from django.core.management.base import BaseCommand
from uploader.models import Role


class Command(BaseCommand):
    help = 'Inicjalizuje podstawowe role w systemie'

    def handle(self, *args, **kwargs):
        roles_data = [
            {'name': 'Użytkownik', 'symbol': 'user'},
            {'name': 'Moderator', 'symbol': 'moderator'},
            {'name': 'Administrator', 'symbol': 'admin'},
        ]
        
        for role_data in roles_data:
            role, created = Role.objects.get_or_create(
                symbol=role_data['symbol'],
                defaults={'name': role_data['name']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Utworzono rolę: {role.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'→ Rola już istnieje: {role.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n✓ Inicjalizacja ról zakończona!')
        )
