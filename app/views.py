# from django.core.handlers.wsgi import WSGIRequest
import logging
import os
import tempfile
import zipfile
from collections import defaultdict
from io import BytesIO
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.utils import IntegrityError
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from pdf2image import convert_from_path
from rest_framework import status
# from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Label, Image, NLP_data
from .serializers import ImageSerializer, NLP_dataSerializer
from .serializers import UserSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def register(request):
    try:
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password'],
                email=serializer.validated_data['email']
            )

            # Automatically log in the user after registration
            login(request, user)

            token, created = Token.objects.get_or_create(user=user)

            return Response({'token': token.key, 'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError:
        return Response({'error': 'Username or email already exists'}, status=status.HTTP_409_CONFLICT)
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def login_view(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user': UserSerializer(user).data})
        else:
            return Response({'error': 'Unauthorized', 'message': 'Incorrect username or password.'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'error': 'Internal Server Error', 'message': 'The server encountered an unexpected condition which prevented it from fulfilling the request.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        # Log out the authenticated user
        logout(request._request)

        # Delete the Token to invalidate it
        Token.objects.filter(user=request.user).delete()

        return Response({'detail': 'Successfully logged out'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
@login_required
def upload_images(request):
    # Extract images from the uploaded files
    images = request.data.getlist('images') if 'images' in request.data else None

    if not images:
        return Response({"detail": "No images provided"}, status=status.HTTP_400_BAD_REQUEST)

    responses = []

    for image_file in images:
        if not image_file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
            responses.append({"detail": f"Invalid file type: {image_file.name}. Please upload an image file."})
            continue

        # Extract image name from the uploaded file
        image_name = image_file.name
        # Extract labels from the request
        labels_text = request.data.get('labels', '')  # If 'labels' is not in request, default to an empty string
        # Check if labels_text is a file
        if hasattr(labels_text, 'read'):
            # If it's a file, read the content
            labels_text = labels_text.read().decode('utf-8')

        # Open the image file with PIL and get its size
        width, height = get_image_dimensions(image_file)

        # Add the image name to the request data
        data = request.data.dict()
        data['name'] = image_name
        # Add the user to the request data
        data['user'] = request.user.id  # Use the user's ID instead of username
        data['labels'] = labels_text
        data['annotations'] = request.data.get('annotations', '')
        data['url'] = image_file
        data['width'] = width  # Add the width to the request data
        data['height'] = height  # Add the height to the request data
        serializer = ImageSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            # Create or update the Label instance for the uploaded image
            image = serializer.instance  # Get the created Image instance
            if labels_text:
                label, created = Label.objects.update_or_create(
                    text=labels_text,
                    defaults={'image': image}
                )
                if not created:
                    label.image = image
                    label.save()

                # Update the image to associate it with the new label
                image.labels = label
                image.save()

            # Serialize the image data
            serializer = ImageSerializer(image)
            responses.append(serializer.data)
        else:
            responses.append(serializer.errors)
            print(serializer.errors)

    return Response(responses, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
@login_required

def upload_pdfs(request):
    # Extract PDFs from the uploaded files
    pdfs = request.data.getlist('pdfs') if 'pdfs' in request.data else None

    if not pdfs:
        return Response({"detail": "No PDFs provided"}, status=status.HTTP_400_BAD_REQUEST)

    responses = []

    for pdf_file in pdfs:
        if not pdf_file.name.lower().endswith('.pdf'):
            responses.append({"detail": f"Invalid file type: {pdf_file.name}. Please upload a PDF file."})
            continue

        # Save the PDF in MEDIA_ROOT in folder called pdfs
        pdf_path = os.path.join(settings.MEDIA_ROOT, pdf_file.name)
        with open(pdf_path, 'wb+') as destination:
            for chunk in pdf_file.chunks():
                destination.write(chunk)

        # Convert the PDF to images
        images = convert_from_path(pdf_path)
        
        for i, image in enumerate(images, start=1):
            # Convert the image to bytes
            image_bytes = BytesIO()
            image.save(image_bytes, format='JPEG')
            # Get the size of the file
            file_size = image_bytes.tell()
            # Rewind the file pointer to the start
            image_bytes.seek(0)
            image_name = f"{os.path.splitext(pdf_file.name)[0]}_{i}.jpeg"
            image_file = InMemoryUploadedFile(image_bytes, None, image_name, 'image/jpeg', file_size, None)


            # Extract image name from the uploaded file
            image_name = image_file.name
            # Extract labels from the request
            labels_text = request.data.get('labels', '')  # If 'labels' is not in request, default to an empty string
            # Check if labels_text is a file
            if hasattr(labels_text, 'read'):
                # If it's a file, read the content
                labels_text = labels_text.read().decode('utf-8')
                
            # Open the image file with PIL and get its size
            width, height = get_image_dimensions(image_file)
            
            # Add the image name to the request data
            data = request.data.dict()
            data['name'] = image_name
            # Add the user to the request data
            data['user'] = request.user.id
            data['labels'] = labels_text
            data['annotations'] = request.data.get('annotations', '')
            data['url'] = image_file
            data['width'] = width
            data['height'] = height
            serializer = ImageSerializer(data=data)
            
            if serializer.is_valid():
                serializer.save()
                # Create or update the Label instance for the uploaded image
                image = serializer.instance
                if labels_text:
                    label, created = Label.objects.update_or_create(
                        text=labels_text,
                        defaults={'image': image}
                    )
                    if not created:
                        label.image = image
                        label.save()
                        
                    # Update the image to associate it with the new label
                    image.labels = label
                    image.save()
                    
                # Serialize the image data
                serializer = ImageSerializer(image)
                responses.append(serializer.data)
            else:
                
                responses.append(serializer.errors)
                print(serializer.errors)
                
    return Response(responses, status=status.HTTP_201_CREATED)



@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@login_required
@csrf_exempt
def update_annotations(request, pk):
    image = get_object_or_404(Image, pk=pk)
    serializer = ImageSerializer(image, data=request.data, partial=True)
    # print(image.user, request.user)

    if image.user != request.user:
        return Response({"detail": "You do not have permission to perform this action."},
                        status=status.HTTP_403_FORBIDDEN)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@csrf_exempt
@permission_classes([IsAuthenticated])
@login_required
def add_labels_to_images(request):
    image_ids = request.data.get('img_ids', [])

    if not image_ids:
        return Response({"detail": "No image IDs provided"}, status=status.HTTP_400_BAD_REQUEST)

    label_text = request.data.get('labels', '')

    responses = []

    # Retrieve the existing label or create a new one
    label, created = Label.objects.get_or_create(text=label_text)

    for image_id in image_ids:
        try:
            image = Image.objects.get(id=image_id)
        except Image.DoesNotExist:
            responses.append({"detail": f"Image with ID {image_id} does not exist."})
            continue

        if image.user != request.user:
            responses.append({"detail": f"You do not have permission to modify image {image_id}."})
            continue

        # Link the existing label to the image
        image.labels = label
        image.save()

        # Serialize the image data
        serializer = ImageSerializer(image)
        responses.append(serializer.data)

    return Response(responses, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@csrf_exempt
@permission_classes([IsAuthenticated])
@login_required
# get all images of the user
def get_all_images(request):
    images = Image.objects.filter(user=request.user)
    serializer = ImageSerializer(images, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@csrf_exempt
@permission_classes([IsAuthenticated])
@login_required
# get image by id
def get_image_by_id(request, pk):
    image = get_object_or_404(Image, pk=pk)
    if image.user != request.user:
        return Response({"detail": "You do not have permission to perform this action."},
                        status=status.HTTP_403_FORBIDDEN)
    serializer = ImageSerializer(image)
    return Response(serializer.data)




@api_view(['GET'])
@csrf_exempt
@permission_classes([IsAuthenticated])
@login_required
def get_all_images_annotations(request):
    # Get all images of the user
    images = Image.objects.filter(user=request.user)
    serializer = ImageSerializer(images, many=True)

    # Create a temporary directory to store the .txt files
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Keep track of duplicate image names
        image_names = defaultdict(int)

        # For each image, save its annotations in a .txt file
        for image in serializer.data:
            annotations = image['annotations']
            # Only process images that have annotations
            if annotations:
                # Remove the square brackets and quotes from the annotations
                annotations = annotations.replace('[', '').replace(']', '').replace('"', '')
                # Write each annotation on a new line
                image_name = image['name'].split('.')[0]
                image_names[image_name] += 1
                if image_names[image_name] > 1:
                    image_name = f"{image_name}({image_names[image_name]-1})"
                with open(os.path.join(tmpdirname, f"{image_name}.txt"), 'w') as f:
                    f.write('\n'.join(annotations.split(',')))

        # Create a zip file and add all the .txt files to it
        with zipfile.ZipFile(os.path.join(tmpdirname, 'annotations.zip'), 'w') as zipf:
            for file in os.listdir(tmpdirname):
                if file.endswith(".txt"):
                    zipf.write(os.path.join(tmpdirname, file), arcname=file)

        # Send the zip file to the frontend
        response = FileResponse(open(os.path.join(tmpdirname, 'annotations.zip'), 'rb'))
        response['Content-Disposition'] = 'attachment; filename=annotations.zip'
        return response
    
    
@api_view(['POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
@login_required

def upload_nlp_data(request):
    # Extract images from the uploaded files
    data = request.data.get('data') if 'data' in request.data else None

    if not data:
        return Response({"detail": "No data provided"}, status=status.HTTP_400_BAD_REQUEST)

    responses = []

    # Add the image name to the request data
    data = request.data
    # Add the user to the request data
    data['user'] = request.user.id  # Use the user's ID instead of username
    
    serializer = NLP_dataSerializer(data=data)
    
    if serializer.is_valid():
        instance = serializer.save()
        # Serialize the instance data
        serializer = NLP_dataSerializer(instance)
        responses.append(serializer.data)
    else:
        responses.append(serializer.errors)
        print(serializer.errors)
        
    return Response(responses, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@csrf_exempt
@permission_classes([IsAuthenticated])
@login_required

def get_all_nlp_data(request):
    data = NLP_data.objects.filter(user=request.user)
    serializer = NLP_dataSerializer(data, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)