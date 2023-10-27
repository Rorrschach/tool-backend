from django.db import models
from django.contrib.auth.models import User

class Label(models.Model):
    text = models.TextField()

    def __str__(self):
        return self.text

class Image(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='images')  #do not change :)
    annotations = models.TextField(null=True, blank=True)
    labels = models.ForeignKey(Label, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
