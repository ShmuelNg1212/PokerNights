"""What a member sends to the group chat after a session is closed: the card's data and a plain text.

Read-only, and built from what the session page already loaded. Every amount is formatted
here, so the card that share.js draws never formats money itself.
"""

from django.utils import timezone
from django.utils.text import slugify

from ledger import money

from .templatetags.table_tags import token


def card(night, outcome, recap) -> dict:
    unit = night.unit
    tokens = {s.member.pk: token(s, outcome.standings) for s in outcome.standings}

    def who(member) -> dict:
        label, colour = tokens[member.pk]
        return {"name": member.display_name, "chip": label, "k": colour}

    rows = [
        {
            **who(line.member), "place": line.place, "amount": money.format_signed_amount(line.net, unit),
            "sign": "plus" if line.net > 0 else "minus" if line.net < 0 else "even", "share": line.share,
        }
        for line in recap.ranking
    ]
    transfers = [
        {"payer": who(t.payer), "payee": who(t.payee), "amount": money.format_amount(t.amount, unit)}
        for t in outcome.transfers
    ]
    day = f"{night.game_date:%a, %b} {night.game_date.day}"
    foot = []
    if night.closed_at:
        closed = timezone.localtime(night.closed_at)
        foot.append(f"Closed {closed:%b} {closed.day}, {closed.hour % 12 or 12}:{closed:%M %p}")
    if recap.total_rake:
        foot.append("Results are after rake.")
    if outcome.carried_in:
        foot.append("With earlier unpaid transfers.")
    text = [f"{night.table.name} · {day}", "Results"]
    text += [f"{row['place']}. {row['name']} {row['amount']}" for row in rows]
    text.append("Who pays whom")
    text += [f"{t['payer']['name']} → {t['payee']['name']} {t['amount']}" for t in transfers] or ["Nobody owes anything."]
    if outcome.carried_in:
        text.append("Includes unpaid transfers from earlier sessions.")
    text.append("PokerNights")
    return {
        "title": night.table.name,
        "when": day + (f" · {night.location}" if night.location else ""),
        "facts": f"{recap.players} player{'' if recap.players == 1 else 's'} · "
        f"{recap.set_count} set{'' if recap.set_count == 1 else 's'} · "
        f"{money.format_amount(recap.total_buy_in, unit)} bought in",
        "rows": rows,
        "transfers": transfers,
        "foot": foot,
        "text": "\n".join(text),
        "lines": len(text),
        "file": f"pokernights-{slugify(night.table.name) or 'session'}-{night.game_date.isoformat()}.png",
    }
