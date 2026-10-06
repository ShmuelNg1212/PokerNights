from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from audit.admin import ReadOnlyAdmin

from .models import PasswordResetLink, User

admin.site.register(User, UserAdmin)


@admin.register(PasswordResetLink)
class PasswordResetLinkAdmin(ReadOnlyAdmin):
    list_display = ("user", "created_by", "created_at", "expires_at", "used_at", "revoked_at")
    exclude = ("token_hash",)
