"""
Adaptery dla django-allauth
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from .models import Role


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom adapter dla kont lokalnych"""
    
    def save_user(self, request, user, form, commit=True):
        """
        Zapisuje użytkownika i przypisuje domyślną rolę
        """
        user = super().save_user(request, user, form, commit=False)
        
        # Przypisz rolę 'user' jeśli nie ma roli
        if not user.role:
            user_role, created = Role.objects.get_or_create(
                symbol='user',
                defaults={'name': 'Użytkownik'}
            )
            user.role = user_role
        
        if commit:
            user.save()
        
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter dla kont społecznościowych (Google OAuth)"""
    
    def pre_social_login(self, request, sociallogin):
        """
        Wywoływane przed zalogowaniem przez social account
        """
        # Jeśli użytkownik już istnieje, nic nie robimy
        if sociallogin.is_existing:
            return
        
        # Sprawdź czy użytkownik z tym emailem już istnieje
        if sociallogin.email_addresses:
            email = sociallogin.email_addresses[0].email
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            try:
                existing_user = User.objects.get(email=email)
                # Połącz istniejące konto z social account
                sociallogin.connect(request, existing_user)
            except User.DoesNotExist:
                pass
    
    def populate_user(self, request, sociallogin, data):
        """
        Wypełnia dane użytkownika z social account
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Ustaw auth_provider na 'google'
        user.auth_provider = 'google'
        
        # Pobierz dodatkowe dane z Google
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            user.google_id = extra_data.get('sub') or extra_data.get('id')
            user.google_email = extra_data.get('email')
            user.google_picture = extra_data.get('picture')
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Zapisuje użytkownika z social account
        """
        user = super().save_user(request, sociallogin, form)
        
        # Przypisz domyślną rolę
        if not user.role:
            user_role, created = Role.objects.get_or_create(
                symbol='user',
                defaults={'name': 'Użytkownik'}
            )
            user.role = user_role
            user.save()
        
        return user
