import uuid

from django.test import TestCase, override_settings

from games.models import GameNight
from settlement import queries, services
from settlement.tests.test_carried import Club


@override_settings(DEBTS_VIEW=True)
class ClearanceStampTests(TestCase):
    def test_clearance_and_undo_change_both_stamps_and_page_stamp_matches_poll(self):
        club = Club('Ana', 'Ben')
        ids = [club.closed({'Ana': -500, 'Ben': 500}), club.closed({'Ana': 300, 'Ben': -300})]
        nights = list(GameNight.objects.filter(pk__in=ids).order_by('pk'))
        def stamps():
            return [queries.hub_stamp([club.group.pk])] + [queries.night_stamp(n) for n in nights]
        before = stamps()
        clearance = services.settle_pair(club.group.pk, club.host, 'php', club.members['Ana'].pk,
            club.members['Ben'].pk, [club.unpaid(n)[0].pk for n in ids], 20000, uuid.uuid4())
        cleared = stamps()
        self.assertTrue(all(a != b for a, b in zip(before, cleared)))
        for night in nights:
            outcome = queries.night_outcome(night)
            page = queries.stamp_from(night,
                list(night.sets.order_by('set_number').values_list('pk', 'state', 'finalized_at')),
                outcome.plan.pk, len(outcome.replaced), (len(outcome.payments), sum(p.active for p in outcome.payments)),
                cleared=outcome.cleared_count)
            self.assertEqual(page, queries.night_stamp(night))
        services.undo_clearance(club.group.pk, club.host, clearance.pk, 'Mistake')
        undone = stamps()
        self.assertTrue(all(a != b for a, b in zip(cleared, undone)))
        self.assertNotEqual(before[0], undone[0])  # the group's history keeps the reversal
        self.assertEqual(before[1:], undone[1:])  # no active clearance remains on these plans

    def test_empty_clearance_counts_do_not_change_legacy_stamp(self):
        club = Club('Ana', 'Ben')
        night_id = club.closed({'Ana': -500, 'Ben': 500})
        night = GameNight.objects.get(pk=night_id)
        sets = list(night.sets.order_by('set_number').values_list('pk', 'state', 'finalized_at'))
        plan_id = night.plans.get(is_current=True).pk
        self.assertEqual(queries.stamp_from(night, sets, plan_id, 0, (0, 0)),
                         queries.stamp_from(night, sets, plan_id, 0, (0, 0), cleared=0))
        other = Club('Elsewhere', 'Someone')
        other_id = other.closed({'Elsewhere': -10, 'Someone': 10})
        before = queries.hub_stamp([club.group.pk])
        services.settle_pair(other.group.pk, other.host, 'php', other.members['Elsewhere'].pk,
            other.members['Someone'].pk, [other.unpaid(other_id)[0].pk], 1000, uuid.uuid4())
        self.assertEqual(before, queries.hub_stamp([club.group.pk]))
