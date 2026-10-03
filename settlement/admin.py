from django.contrib import admin

from audit.admin import ReadOnlyAdmin

from .models import Payment, PaymentReversal, SettlementPlan, Transfer


@admin.register(SettlementPlan)
class SettlementPlanAdmin(ReadOnlyAdmin):
    list_display = ("finalization", "proven_minimal", "created_at")


@admin.register(Transfer)
class TransferAdmin(ReadOnlyAdmin):
    list_display = ("plan", "position", "payer", "payee", "amount")


@admin.register(Payment)
class PaymentAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "session", "payer", "payee", "amount", "active")


@admin.register(PaymentReversal)
class PaymentReversalAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "payment", "reason")
