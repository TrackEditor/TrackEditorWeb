from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Track(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    last_edit = models.DateTimeField(auto_now_add=True)
    creation = models.DateTimeField(auto_now_add=True)
    track = models.JSONField(blank=False)
    title = models.TextField(blank=False)

    def __str__(self):
        return f'{self.user.username} - {self.id} - {self.creation}'
