from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Project user model, defined up front as Django recommends so it can grow later."""
