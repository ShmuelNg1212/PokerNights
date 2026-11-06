"""Presentation of the read-only debt balances. The settlement app owns every rule and write."""
from django.conf import settings

from ledger.money import format_amount
from settlement import queries
from settlement.models import Clearance


def section(me):
    if not settings.DEBTS_VIEW:
        return {}
    rows = queries.debts(me.group, me)
    members = {m.pk: m for row in rows for m in (row.member_a, row.member_b) if m}
    for row in rows:
        row.key = f'debt-{row.unit}-{row.member_a.pk}-{row.member_b.pk if row.member_b else "fund-" + str(row.transfers[0].pk)}'
        row.sessions = len({t.plan.night_id for t in row.transfers})
        row.can_settle = row.member_b is not None and (me.is_host or me.pk == row.payee.pk or row.net == 0)
        row.other = row.member_b if row.member_a.pk == me.pk else row.member_a
        row.token = row.other if row.member_b and me.pk in (row.member_a.pk, row.member_b.pk) else row.payer
        amount = format_amount(row.amount, row.unit)
        if row.member_b is None:
            row.direction = f'{row.payer.display_name} pays the Rake fund'
            row.waiting = 'A host confirms when paid.'
        elif row.net == 0:
            row.direction = (f'You and {row.other.display_name} cancel out' if me.pk in (row.member_a.pk, row.member_b.pk)
                             else f'{row.member_a.display_name} and {row.member_b.display_name} cancel out')
            row.action = f'Clear {amount}: these cancel out'
        elif me.pk == row.payer.pk:
            row.direction = f'You pay {row.payee.display_name}'
            row.waiting = f'{row.payee.display_name} confirms when paid'
        elif me.pk == row.payee.pk:
            row.direction = f'{row.payer.display_name} pays you'
        else:
            row.direction = f'{row.payer.display_name} pays {row.payee.display_name}'
        if row.member_b:
            row.with_name = (row.other.display_name if me.pk in (row.member_a.pk, row.member_b.pk)
                             else f'{row.member_a.display_name} and {row.member_b.display_name}')
            if row.net:
                row.action = f'Settle {amount}' if me.is_host else f'Got {amount} from {row.payer.display_name}'
    return {'debts_enabled': True, 'debt_rows': rows, 'debt_members': list(members.values())}


def receipt(request, me):
    """One accepted action's status, consumed by the next page draw, never by an unrelated group."""
    if not settings.DEBTS_VIEW:
        return None
    kept = request.session.get('debt_receipt')
    if not kept or kept.get('group') != me.group_id:
        return None
    request.session.pop('debt_receipt')
    clearance = Clearance.objects.select_related('payer', 'payee').filter(pk=kept['id'], group_id=me.group_id, active=True).first()
    if clearance is None or not (me.is_host or me.pk in (clearance.payer_id, clearance.payee_id)):
        return None
    clearance.with_name = (clearance.payee.display_name if me.pk == clearance.payer_id else clearance.payer.display_name)
    if me.pk not in (clearance.payer_id, clearance.payee_id):
        clearance.with_name = f'{clearance.payer.display_name} and {clearance.payee.display_name}'
    clearance.can_undo = me.is_host or clearance.recorded_by_id == me.user_id
    return clearance
