from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('custom_user_display', 'user_email')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def custom_user_display(self, obj):
        return obj.user.username

    custom_user_display.short_description = 'Username'