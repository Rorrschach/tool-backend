from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import UserSerializer, AnnotationSerializer
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Annotation



@api_view(['POST'])
def login(request):
    username = request.data['username']
    password = request.data['password']
    user = get_object_or_404(User, username=username)
    if user.check_password(password):
        token = Token.objects.get(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data})
    else:
        return Response({'error': 'Wrong password'}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['POST'])
def register(request):
    
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        user = User.objects.get(username=serializer.data['username'])
        token = Token.objects.create(user=user)
        user.set_password(serializer.data['password'])
        user.save()
        
        return Response({'token': token.key, 'user': serializer.data}, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['GET'])
def test_token(request):
    return Response({})



@api_view(['POST'])
def save_annotation(request):
    
    # find the user by the token in the request header
    token = request.META.get('HTTP_AUTHORIZATION').split()[1]
    user = Token.objects.get(key=token).user
    
    # create the annotation
    annotation = Annotation(user=user, text=request.data['annotations'])
    annotation.save()
    
    
    return Response({'annotation': AnnotationSerializer(annotation).data}, status=status.HTTP_201_CREATED)


    