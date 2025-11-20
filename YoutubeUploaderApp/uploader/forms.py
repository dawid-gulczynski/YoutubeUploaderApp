from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Video, Short


class UserRegistrationForm(UserCreationForm):
    """Formularz rejestracji użytkownika"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Adres email'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa użytkownika'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Hasło'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Potwierdź hasło'})


class UserProfileForm(forms.ModelForm):
    """Formularz edycji profilu użytkownika"""
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent',
                'placeholder': 'Nazwa użytkownika'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent',
                'placeholder': 'Adres email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent',
                'placeholder': 'Imię'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent',
                'placeholder': 'Nazwisko'
            })
        }


class UserLoginForm(AuthenticationForm):
    """Formularz logowania"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nazwa użytkownika lub email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Hasło'
        })
    )


class VideoUploadForm(forms.ModelForm):
    """Formularz do uploadu źródłowego wideo"""
    
    class Meta:
        model = Video
        fields = ['title', 'description', 'video_file', 'target_duration', 'max_shorts_count']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tytuł wideo źródłowego'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Opis wideo...'
            }),
            'video_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*'
            }),
            'target_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 15,
                'max': 180,
                'value': 60
            }),
            'max_shorts_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 50,
                'value': 10
            })
        }
        help_texts = {
            'target_duration': 'Docelowa długość jednego shorta (15-180 sekund)',
            'max_shorts_count': 'Maksymalna liczba shortów do wygenerowania (1-50)',
            'video_file': 'Wybierz długi film do pocięcia na shorty (mp4, mov, avi, etc.)'
        }
    
    def clean_video_file(self):
        """Walidacja pliku wideo"""
        video = self.cleaned_data.get('video_file')
        if video:
            # Sprawdź rozmiar (maksymalnie 2GB)
            if video.size > 2 * 1024 * 1024 * 1024:  # 2 GB
                raise forms.ValidationError('Plik jest zbyt duży. Maksymalny rozmiar to 2GB.')
            
            # Sprawdź rozszerzenie
            valid_extensions = ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv']
            ext = video.name.lower().split('.')[-1]
            if f'.{ext}' not in valid_extensions:
                raise forms.ValidationError(f'Nieprawidłowy format pliku. Dozwolone formaty: {", ".join(valid_extensions)}')
        
        return video


class ShortEditForm(forms.ModelForm):
    """Formularz do edycji metadanych shorta"""
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'np. fitness motywacja trening'
        }),
        help_text='Oddziel tagi spacją (bez #)'
    )
    
    class Meta:
        model = Short
        fields = ['title', 'description', 'privacy_status', 'scheduled_at', 'made_for_kids']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tytuł shorta',
                'maxlength': 100
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Opis shorta...'
            }),
            'privacy_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'scheduled_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'made_for_kids': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        help_texts = {
            'scheduled_at': 'Pozostaw puste dla natychmiastowej publikacji',
            'made_for_kids': 'Zaznacz jeśli treść jest przeznaczona dla dzieci (wymóg YouTube)'
        }
