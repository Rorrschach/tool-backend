from django.db import models
from django.contrib.auth.models import User


# create default user class
# class User(AbstractUser):
#     # Inherits fields from AbstractUser model such as username, password, email, etc.
#     pass
    
 
class Annotation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    
    def __str__(self):
        return self.text
        
    