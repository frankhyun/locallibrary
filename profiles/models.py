from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="profile",
        on_delete=models.CASCADE,
    )
    display_name = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.display_name or self.user.get_username()
