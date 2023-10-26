from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Annotation, Image

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        
class AnnotationSerializer(serializers.Serializer):
    user = serializers.CharField()
    text = serializers.CharField()
    image = serializers.CharField()  # Add this line

    def create(self, validated_data):
        return Annotation.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.user = validated_data.get('user', instance.user)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)  # Add this line
        instance.save()
        return instance

    
    
    
class ImageSerializer(serializers.ModelSerializer):
    users = serializers.StringRelatedField(many=True)  # Serialize the users as a list of usernames

    class Meta:
        model = Image
        fields = ['id', 'users', 'image', 'name']