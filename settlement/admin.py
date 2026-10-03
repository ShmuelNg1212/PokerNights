from django.contrib import admin

from audit.admin import ReadOnlyAdmin

from .models import SettlementPlan, Transfer


@admin.register(SettlementPlan)
class SettlementPlanAdmin(ReadOnlyAdmin):
    list_display = ("finalization", "proven_minimal", "created_at")


@admin.register(Transfer)
class TransferAdmin(ReadOnlyAdmin):
    list_display = ("plan", "position", "payer", "payee", "amount_centavos")
