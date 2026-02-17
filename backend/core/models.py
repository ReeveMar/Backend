from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db.models import JSONField
from django_cryptography.fields import encrypt
class CustomUserManager(models.Manager):

    def create_or_login_user(self, spotify_id,**extra_fields):
        if not spotify_id:
            raise ValueError("The Spotify ID must be set")
        elif self.model.objects.filter(spotify_id=spotify_id).exists():
            return self.model.objects.get(spotify_id=spotify_id)
        user= self.model(spotify_id=spotify_id, **extra_fields)
        print(user.is_active)
        user.set_unusable_password()
        user.save(using=self._db)
        return user
    
    def create_superuser(self,spotify_id, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")


        return self.create_user(spotify_id=spotify_id, **extra_fields)





class AppUser(AbstractBaseUser, PermissionsMixin):
    spotify_id= models.CharField(max_length=255, unique=True)
    access_token= encrypt(models.CharField(max_length=255, unique=True))
    refresh_token= encrypt(models.CharField(max_length=255, unique=True))
    token_expiry= models.DateTimeField()
    favourite_genres= JSONField(blank=True,default=list)
    favourite_artists= JSONField(blank=True,default=list)
    favourite_tracks= JSONField(blank=True,default=list)
    stats_retrieved_date= models.DateTimeField(null=True, blank=True)
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'spotify_id'
    is_active= models.BooleanField(default=True)
    is_staff= models.BooleanField(default=False)
    is_superuser= models.BooleanField(default=False)

    objects= CustomUserManager()

    def __str__(self):
        return self.spotify_id
    



