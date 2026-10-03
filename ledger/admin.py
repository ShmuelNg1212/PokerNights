from django.contrib import admin

from audit.admin import ReadOnlyAdmin

from .models import BuyIn, BuyInReversal


@admin.register(BuyIn)
class BuyInAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "session", "participant", "amount_centavos", "chips")


@admin.register(BuyInReversal)
class BuyInReversalAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "buy_in", "reason")
