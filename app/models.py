from django.db import models
from django.contrib.auth.models import User


# create default user class
# class User(AbstractUser):
#     # Inherits fields from AbstractUser model such as username, password, email, etc.
#     pass
    
class Annotation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    image = models.ForeignKey('Image', on_delete=models.CASCADE, related_name='annotations')

    def __str__(self):
        return self.text


class Image(models.Model):
    users = models.ManyToManyField(User)
    image = models.ImageField(upload_to='images')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.image.url
