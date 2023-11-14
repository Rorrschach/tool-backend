from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Image, Label


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password']


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['text']

class ImageSerializer(serializers.ModelSerializer):
    labels = LabelSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())  # Allow all User instances
    url = serializers.ImageField(max_length=None, use_url=True)
    width = serializers.IntegerField()  # New field for width
    height = serializers.IntegerField()  # New field for height

    class Meta:
        model = Image
        fields = ['id', 'user', 'name', 'annotations', 'labels', 'url', 'width', 'height']  # Include new fields
