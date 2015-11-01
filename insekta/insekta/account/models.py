from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    accepted_ethics = models.BooleanField(default=False)
