from rest_framework import viewsets
from users.models import Profile
from .serializers import ProfileSerializer
from .api_permissions import IsAdminOrOwnsAccount
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAdminOrOwnsAccount, IsAuthenticated]
    lookup_field = 'username'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Profile.objects.all().order_by('user__id')
        return Profile.objects.filter(user=user)

    def get_object(self):
        queryset = self.get_queryset()
        username = self.kwargs.get('username')
        return get_object_or_404(queryset, user__username=username)