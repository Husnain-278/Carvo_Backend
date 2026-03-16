from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.



class CustomUser(AbstractUser):
    is_active = models.BooleanField(default=False)
    phone = models.CharField(max_length=15, blank=True, null=True)