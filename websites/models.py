from django.db import models
from django.contrib.auth import get_user_model


class Website(models.Model):
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=255)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="websites"
    )

    def __str__(self) -> str:
        return f"{self.name}: {self.url}"
