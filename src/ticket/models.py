from os import path
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db import models

from .utils.custom_thumbnails import has_changed, create_thumb, Image


class Ticket(models.Model):
    title = models.CharField(max_length=128, verbose_name='Titre')
    description = models.TextField(max_length=2048, blank=True, verbose_name='Description')
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(null=True, blank=True, verbose_name='Image', upload_to='ticket_images')
    time_created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # TODO : ajouter un validator sur le format d'image pris en charge en entrée
        # actuellement fait uniquement par le frontend
        # surcharge de la methode save pour convertir les images

        # TODO : a mettre dans le formulaire https://docs.djangoproject.com/en/5.0/ref/forms/validation/
        if self.image and has_changed(self, 'image'):
            # Convertir l'image en jpg et créé des miniatures
            # TODO : tester la chaine si diff de null
            filename = path.splitext(path.split(self.image.name)[-1])[0]
            filename = f"{filename}.jpg"

            image = Image.open(self.image)
            if image.mode not in ('L', 'RGB'):
                image = image.convert('RGB')

            # Redimensionner l'image principale
            self.image = create_thumb(image, settings.IMAGE_MAX_SIZE)
            self.image.name = filename

            # Redimensionner l'image pour la miniature
            self.thumbnail = create_thumb(image, settings.THUMB_MAX_SIZE)
            self.thumbnail.name = f'_{filename}'

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Review(models.Model):
    ticket = models.ForeignKey(to=Ticket, on_delete=models.CASCADE)
    headline = models.CharField(max_length=128)
    rating = models.PositiveSmallIntegerField(
        # validates that rating must be between 0 and 5
        # https://docs.djangoproject.com/fr/5.0/ref/validators/
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    body = models.TextField(max_length=8192, blank=True)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    time_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.headline


class UserFollows(models.Model):
    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following'
    )
    followed_user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followed_by'
    )

    class Meta:
        # class meta pour nom table, contraintes sur les champs, tri par défaut, ...

        # ensures we don't get multiple UserFollows instances
        # for unique user-user_followed pairs
        # unique_together = ('user', 'followed_user', )

        constraints = [
            models.UniqueConstraint(fields=['user', 'followed_user'], name='unique_user_follow')
        ]

    def __str__(self):
        return f"{self.user} suis {self.followed_user}"
