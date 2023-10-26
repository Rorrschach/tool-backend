from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .serializers import UserSerializer, ImageSerializer, LabelSerializer
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Image, Label
from rest_framework.permissions import IsAuthenticated




@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if username is None or password is None:
        return Response({'error': 'Please provide both username and password'},
                        status=status.HTTP_400_BAD_REQUEST)
    
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
        user = User.objects.create(username=serializer.data['username'])
        user.set_password(serializer.data['password'])
        user.save()
        
        token = Token.objects.create(user=user)
        
        return Response({'token': token.key, 'user': serializer.data}, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_image(request):
    # Extract image name from the uploaded file
    image_name = request.data.get('image').name if 'image' in request.data else None

    # Extract labels from the request
    labels_text = request.data.get('labels', '')  # If 'labels' is not in request, default to an empty string

    # Add the image name to the request data
    data = request.data.copy()
    data['name'] = image_name

    # Add the user to the request data
    data['user'] = request.user.id  # Use the user's ID instead of username
    
    data['labels'] = request.data.get('labels', '')
    
    data['annotations'] = request.data.get('annotations', '')
    

    serializer = ImageSerializer(data=data)
    
    if serializer.is_valid():
        serializer.save()
        # Create or update the Label instance for the uploaded image
        image = serializer.instance  # Get the created Image instance
        label, created = Label.objects.get_or_create(image=image, defaults={'text': labels_text})


        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# update the image annotations by id
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_image(request, pk):
    image = get_object_or_404(Image, pk=pk)
    serializer = ImageSerializer(image, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)