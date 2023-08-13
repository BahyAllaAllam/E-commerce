from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(help_text='Required.', label='Email')
    first_name = forms.CharField(max_length=50, help_text='Required. 50 characters or fewer. Letters, digits and @/./+/-/_ only.')
    last_name = forms.CharField(max_length=50, help_text='Required. 50 characters or fewer. Letters, digits and @/./+/-/_ only.')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']


class EmailChangeForm(forms.ModelForm):
    email = forms.EmailField(help_text='Required.', label='Email')

    class Meta:
        model = User
        fields = ['email']
