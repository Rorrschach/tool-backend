from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import UserSerializer, AnnotationSerializer, ImageSerializer
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Annotation, Image



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
    

@api_view(['POST'])
def save_annotation(request):
    try:
        # find the user by the token in the request header
        token = request.META.get('HTTP_AUTHORIZATION').split()[1]
        user = Token.objects.get(key=token).user

        # get the image
        image_name = request.data['image_name']
        image = Image.objects.get(user=user, name=image_name)

        # get or create the annotation
        annotation, created = Annotation.objects.get_or_create(user=user, image=image,
                                                               defaults={'text': request.data['annotations']})
        if not created:
            # if the annotation already exists, update its text
            annotation.text = request.data['annotations']
            annotation.save()

        return Response({'annotation': AnnotationSerializer(annotation).data, 'image': image_name}, status=status.HTTP_201_CREATED)
    except KeyError:
        return Response({'error': 'Invalid request data'}, status=status.HTTP_400_BAD_REQUEST)
    except (Token.DoesNotExist, Image.DoesNotExist):
        return Response({'error': 'Invalid token or image'}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def upload_image(request):
    try:
        # find the user by the token in the request header
        token = request.META.get('HTTP_AUTHORIZATION').split()[1]
        user = Token.objects.get(key=token).user

        # parse the image from the request
        parser_classes = (MultiPartParser, FormParser)
        image_file = request.data['file']

        # get or create the Image instance
        image, created = Image.objects.get_or_create(name=image_file.name,
                                                     defaults={'image': image_file})
        # add the user to the image's users
        image.users.add(user)

        return Response({'image': str(image)}, status=status.HTTP_201_CREATED)
    except KeyError:
        return Response({'error': 'Invalid request data'}, status=status.HTTP_400_BAD_REQUEST)
    except Token.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
# get all images and their annotations for a user
def get_images_and_annotations(request):
    try:
        # find the user by the token in the request header
        token = request.META.get('HTTP_AUTHORIZATION').split()[1]
        user = Token.objects.get(key=token).user
        
        print(user)

        # get all images for the user
        images = Image.objects.filter(users=user)
        
        print(images)

        # get all annotations for the images
        annotations = Annotation.objects.filter(image__in=images)
        
        print(annotations)

        # serialize the images and annotations
        images_serialized = ImageSerializer(images, many=True)
        annotations_serialized = AnnotationSerializer(annotations, many=True)

        return Response({'images': images_serialized.data, 'annotations': annotations_serialized.data})
    except KeyError:
        return Response({'error': 'Invalid request data'}, status=status.HTTP_400_BAD_REQUEST)
    except Token.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    