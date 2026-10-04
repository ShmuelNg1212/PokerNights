from django.contrib import admin

from audit.admin import ReadOnlyAdmin

from .models import (
    BalanceAdjustment, BuyIn, BuyInReversal, CashOut, CashOutBatch, CashOutReversal, FinalCount, Finalization, PlayerResult, RakeEntry,
)


@admin.register(BuyIn)
class BuyInAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "session", "participant", "amount")


@admin.register(BuyInReversal)
class BuyInReversalAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "buy_in", "reason")


@admin.register(CashOut)
class CashOutAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "session", "participant", "amount", "kind")


@admin.register(CashOutReversal)
class CashOutReversalAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "cash_out", "reason")


@admin.register(BalanceAdjustment)
class BalanceAdjustmentAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "session", "participant", "amount", "mode", "note", "voided_at")


@admin.register(Finalization)
class FinalizationAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "session", "revision", "is_current", "total_buy_in")


@admin.register(PlayerResult)
class PlayerResultAdmin(ReadOnlyAdmin):
    list_display = ("finalization", "member", "buy_in_total", "cash_out", "net", "is_current")


@admin.register(FinalCount)
class FinalCountAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "session", "participant", "amount", "version", "is_current", "voided_at")


@admin.register(CashOutBatch)
class CashOutBatchAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "session", "recorded_by")


@admin.register(RakeEntry)
class RakeEntryAdmin(ReadOnlyAdmin):
    list_display = ("buy_in", "account", "amount", "unit", "rake_mode")
