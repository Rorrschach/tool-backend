from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Image, Label

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        
class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = '__all__'

class ImageSerializer(serializers.ModelSerializer):
    labels = LabelSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())  # Allow all User instances

    class Meta:
        model = Image
        fields = ['id','user', 'name', 'annotations', 'labels']