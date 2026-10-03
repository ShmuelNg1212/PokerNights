from django.contrib import admin

from audit.admin import ReadOnlyAdmin

from .models import BalanceAdjustment, BuyIn, BuyInReversal, CashOut, CashOutReversal


@admin.register(BuyIn)
class BuyInAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "session", "participant", "amount_centavos", "chips")


@admin.register(BuyInReversal)
class BuyInReversalAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "buy_in", "reason")


@admin.register(CashOut)
class CashOutAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "session", "participant", "chips")


@admin.register(CashOutReversal)
class CashOutReversalAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "cash_out", "reason")


@admin.register(BalanceAdjustment)
class BalanceAdjustmentAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "session", "participant", "chips_delta", "mode", "note", "voided_at")
