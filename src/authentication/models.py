from django.contrib.auth.models import BaseUserManager, AbstractUser
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None):  # **kwargs
        if not email:
            raise ValueError("Entrer un email")

        user = self.model(
            email=self.normalize_email(email)
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(email=email, password=password)
        user.is_superuser = True
        # user.is_admin = True
        user.is_staff = True
        user.save()
        return user


class CustomUser(AbstractUser):

    # utilisation de l'email comme identifiant à la place du username par défaut dans AbstractUser
    email = models.EmailField(max_length=150, unique=True, blank=False)


    username = None
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    nickname = models.CharField(max_length=80, unique=True, blank=False, verbose_name='Pseudo')
    profil_photo = models.ImageField(verbose_name='Photo de profil')

    objects = CustomUserManager()

