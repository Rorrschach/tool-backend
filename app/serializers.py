from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Annotation

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        
class AnnotationSerializer(serializers.Serializer):
    user = serializers.CharField()
    text = serializers.CharField()
    
    def create(self, validated_data):
        return Annotation.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        instance.user = validated_data.get('user', instance.user)
        instance.text = validated_data.get('text', instance.text)
        instance.save()
        return instance