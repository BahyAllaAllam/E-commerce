from rest_framework import serializers
from users.models import Profile
from django.contrib.auth.models import User


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = Profile
        fields = ['username','first_name', 'last_name', 'image']


    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance