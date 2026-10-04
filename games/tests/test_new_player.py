import uuid
from unittest import mock
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse
from audit.models import AuditEvent
from games import services
from games.models import Participant, ParticipantBatch, PlayInterval
from games.tests.helpers import make_session
from games.tests.test_add_players import Roster
from groups.errors import RuleError, NotAllowed
from groups.models import Member
from groups.tests.helpers import make_group, make_user
from ledger.models import BuyIn, CashOut
from web.tests.test_concurrency import race, kinds


class NewPlayerTests(TestCase):
    def setUp(self):
        self.roster = Roster(state='running')

    def add(self, name='Late player', request_id=None):
        return services.add_new_player(self.roster.session.pk, self.roster.host, name, request_id or uuid.uuid4())

    def test_running_join_is_normalized_audited_timed_and_has_no_money(self):
        before = self.roster.version()
        p = self.add('  Late   player  ')[0]
        self.assertEqual(p.member.display_name, 'Late player')
        self.assertIsNone(p.member.user_id)
        self.assertEqual(p.status, 'joined')
        self.assertEqual(self.roster.version(), before + 1)
        self.assertEqual(PlayInterval.objects.filter(participant=p, ended_at__isnull=True).count(), 1)
        self.assertTrue(AuditEvent.objects.filter(action='member.added', target_id=str(p.member.pk)).exists())
        self.assertTrue(AuditEvent.objects.filter(action='participant.joined', session_id=self.roster.session.pk).exists())
        self.assertFalse(BuyIn.objects.exists())
        self.assertFalse(CashOut.objects.exists())
        self.roster.session.refresh_from_db()
        self.assertEqual(self.roster.session.state, 'running')

    def test_retry_even_after_end_does_not_write_twice(self):
        request_id = uuid.uuid4()
        first = self.add(request_id=request_id)[0]
        services.transition(self.roster.session.pk, self.roster.host, 'end')
        before = (Member.objects.count(), AuditEvent.objects.count(), self.roster.version())
        second = self.add(request_id=request_id)[0]
        self.assertEqual(second.pk, first.pk)
        self.assertEqual((Member.objects.count(), AuditEvent.objects.count(), self.roster.version()), before)
        self.assertEqual(ParticipantBatch.objects.count(), 1)
        self.assertEqual(PlayInterval.objects.filter(participant=first).count(), 1)

    def test_duplicate_name_recommends_roster_and_creates_nothing(self):
        before = (Member.objects.count(), self.roster.version())
        with self.assertRaisesMessage(RuleError, 'Choose that player from the roster'):
            self.add('aNA')
        self.assertEqual((Member.objects.count(), self.roster.version()), before)
        self.assertFalse(ParticipantBatch.objects.exists())

    def test_seated_duplicate_directs_back_to_set(self):
        self.roster.add('Ana')
        with self.assertRaisesMessage(RuleError, 'already at the table. Return to the set'):
            self.add('aNA')
        self.assertEqual(self.roster.at_table(), ['Ana'])

    def test_invalid_names_create_nothing(self):
        before = Member.objects.count()
        for name in ['', '   ', 'x' * 61]:
            with self.assertRaises(RuleError):
                self.add(name)
        self.assertEqual(Member.objects.count(), before)
        self.assertFalse(ParticipantBatch.objects.exists())

    def test_full_table_creates_no_orphan_member(self):
        r = Roster(state='running', seat_count=2)
        r.add('Ana', 'Ben')
        before = (Member.objects.count(), AuditEvent.objects.count(), r.version())
        with self.assertRaisesMessage(RuleError, 'table is full'):
            services.add_new_player(r.session.pk, r.host, 'Late', uuid.uuid4())
        self.assertEqual((Member.objects.count(), AuditEvent.objects.count(), r.version()), before)

    def test_ended_set_refuses_before_creating_member(self):
        services.transition(self.roster.session.pk, self.roster.host, 'end')
        before = Member.objects.count()
        with self.assertRaisesMessage(RuleError, 'cannot be added at this stage'):
            self.add()
        self.assertEqual(Member.objects.count(), before)

    def test_player_and_other_group_host_are_refused(self):
        with self.assertRaises(NotAllowed):
            services.add_new_player(self.roster.session.pk, self.roster.members['Ana'], 'Late', uuid.uuid4())
        _, host = make_group('other', 'Other')
        with self.assertRaises(RuleError):
            services.add_new_player(self.roster.session.pk, host, 'Late', uuid.uuid4())
        self.assertFalse(Participant.objects.filter(session=self.roster.session).exists())

    def test_downstream_failure_rolls_back_roster_timer_and_audits(self):
        before = (Member.objects.count(), AuditEvent.objects.count(), self.roster.version())
        real = services.audit.record
        def fail(action, **kwargs):
            if action == 'participant.joined':
                raise RuntimeError('Synthetic failure')
            return real(action, **kwargs)
        with mock.patch('games.services.audit.record', side_effect=fail):
            with self.assertRaises(RuntimeError):
                self.add()
        self.assertEqual((Member.objects.count(), AuditEvent.objects.count(), self.roster.version()), before)
        self.assertFalse(ParticipantBatch.objects.exists())
        self.assertFalse(PlayInterval.objects.filter(participant__session=self.roster.session).exists())

    def test_open_and_setup_have_no_running_interval(self):
        for state in ['open', 'setup']:
            r = Roster(state=state)
            p = services.add_new_player(r.session.pk, r.host, 'Late', uuid.uuid4())[0]
            self.assertFalse(PlayInterval.objects.filter(participant=p).exists())


class NewPlayerPageTests(TestCase):
    def setUp(self):
        self.r = Roster(state='running')
        self.url = reverse('participants_add', args=[self.r.session.pk])
        self.client.force_login(self.r.host.user)

    def post(self, name, **extra):
        return self.client.post(self.url, {'action': 'new', 'name': name, 'request_id': str(uuid.uuid4()), **extra}, follow=True)

    def test_empty_eligible_roster_keeps_entry_and_new_name_form(self):
        self.r.add()
        services.add_participant(self.r.session.pk, self.r.host, self.r.host.pk)
        page = self.client.get(reverse('session', args=[self.r.session.pk]))
        self.assertContains(page, self.url)
        page = self.client.get(self.url)
        self.assertContains(page, 'Every player of this group is already at the table')
        self.assertContains(page, 'Add new player')
        self.assertContains(page, 'Player name')
        self.assertContains(page, 'Record their buy-in separately')

    def test_success_returns_running_set_with_manual_buy_in(self):
        page = self.post('Late')
        self.assertRedirects(page, reverse('session', args=[self.r.session.pk]))
        self.assertContains(page, 'Added 1 player: Late.')
        self.assertContains(page, 'Buy-in for Late')
        self.assertContains(page, 'No buy-in yet')
        self.assertFalse(BuyIn.objects.exists())

    def test_duplicate_name_keeps_bound_value_and_field_error(self):
        page = self.post('aNA')
        self.assertContains(page, 'value="aNA"')
        self.assertContains(page, 'Choose that player from the roster')
        self.assertContains(page, 'aria-invalid="true"')

    def test_seated_duplicate_has_possible_recovery(self):
        self.r.add('Ana')
        page = self.post('aNA')
        self.assertContains(page, 'Return to the set.')
        self.assertNotContains(page, 'Choose that player from the roster')

    def test_blank_and_overlong_names_keep_error(self):
        self.assertContains(self.post(''), 'This field is required')
        self.assertContains(self.post('x'*61), 'at most 60 characters')

    def test_full_table_disables_add_and_keeps_refused_name(self):
        self.r.session.seat_count = 2
        self.r.session.save(update_fields=['seat_count'])  # fixture only
        self.r.add('Ana', 'Ben')
        page = self.post('Late')
        self.assertContains(page, '<fieldset class="picker-fields stack" disabled>')
        self.assertContains(page, 'value="Late"')
        self.assertFalse(Member.objects.filter(group=self.r.group, display_name='Late').exists())

    def test_ended_set_race_keeps_name_and_disables_form(self):
        services.transition(self.r.session.pk, self.r.host, 'end')
        page = self.post('Late')
        self.assertContains(page, 'value="Late"')
        self.assertContains(page, '<fieldset class="picker-fields stack" disabled>')
        self.assertContains(page, 'Players cannot be added now')

    def test_host_only_and_outsider_404(self):
        self.client.force_login(self.r.members['Ana'].user)
        self.assertEqual(self.client.post(self.url, {'action':'new','name':'Late'}).status_code,403)
        self.client.force_login(make_user('outsider'))
        self.assertEqual(self.client.post(self.url, {'action':'new','name':'Late'}).status_code,404)


@skipUnlessDBFeature('has_select_for_update')
class NewPlayerRaceTests(TransactionTestCase):
    def test_same_request_creates_one_identity_and_interval(self):
        r = Roster(state='running')
        request_id = uuid.uuid4()
        outcomes = race(*[lambda: services.add_new_player(r.session.pk,r.host,'Late',request_id)]*2)
        self.assertEqual(kinds(outcomes), ['ok','ok'],outcomes)
        self.assertEqual(Member.objects.filter(group=r.group,display_name='Late').count(),1)
        self.assertEqual(ParticipantBatch.objects.count(),1)
        self.assertEqual(PlayInterval.objects.filter(participant__session=r.session).count(),1)

    def test_new_and_existing_player_race_for_last_seat(self):
        r = Roster(state='running',seat_count=2)
        r.add('Ana')
        outcomes = race(lambda: services.add_new_player(r.session.pk,r.host,'Late',uuid.uuid4()),lambda:r.add('Ben'))
        self.assertEqual(kinds(outcomes), ['ok','refused'],outcomes)
        self.assertEqual(r.session.participants.filter(status='joined').count(),2)
        self.assertEqual(Member.objects.filter(group=r.group,display_name='Late').exists(),outcomes[0][0]=='ok')

    def test_two_sets_race_for_case_insensitive_name(self):
        r = Roster(state='running')
        second = make_session(r.host,state='running',table_name='Other table')
        outcomes = race(lambda:services.add_new_player(r.session.pk,r.host,'Late',uuid.uuid4()),lambda:services.add_new_player(second.pk,r.host,'lATE',uuid.uuid4()))
        self.assertEqual(kinds(outcomes), ['ok','refused'],outcomes)
        self.assertEqual(Member.objects.filter(group=r.group,display_name__iexact='Late').count(),1)
        self.assertEqual(Participant.objects.filter(session__in=[r.session,second]).count(),1)
