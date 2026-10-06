# Host-issued password reset: study

Date: 2026-10-06, Asia/Manila.

## Request

The human asked to build "the password reset by a host-issued link". It is the open item in TODO.md and the one P1 the repeat critique of the entry pages left standing ([plan](../plan/1791134687_entry_flow_critique_fixes.md), AC9).

## What exists today

- A person who forgets their password cannot get back in by themselves. Only the site administrator can set a new password, in `/admin/`.
- Sign up says "There is no password reset yet." A refused login says "Forgot your password? There is no reset yet. Tell your host, who can ask the site administrator to set a new one."
- The app holds no email address or phone number for anyone. `Member.contact` is free text a host types for a roster player. So the app cannot send anything; a person must carry the link.
- Hosts already carry links: an invite link is created in Group settings, shown once, and pasted into the group chat. `Invite` stores only the SHA-256 hash of a 32-byte random token, with an expiry, a use limit and a revoke time (`groups/models.py`, `groups/services.py`).
- An account (`accounts.User`) is not owned by a group. One account can be a member of several groups and a host of some of them.
- There is no screen to change a password while logged in.

## Constraints

1. **App direction** (AGENTS.md rule 11): `accounts → groups`. `accounts` cannot import `groups`. A password belongs to `accounts`; "who is a host" belongs to `groups`. So the link and the password change live in `accounts`, and the permission check lives in `groups`, which calls down.
2. **Only services write** (rule 2), **each write is audited** (rule 6). `accounts` has no `services.py` yet; `audit` is a leaf that any app may call.
3. **`request_id`** (rule 3). Invite creation carries none. A second tap creates a second invite. This cycle follows that precedent with one difference: a new reset link cancels the earlier one, so a double tap leaves one live link.
4. **A link is opened by more than its reader.** Chat apps fetch a pasted address to build a preview. Opening the link (GET) must change nothing and must not name the account in the page title.
5. **The link is a credential.** Whoever opens it first sets the password. It must work once, expire soon, be stored as a hash, and be cancellable.
6. **Partial unique constraints are not deferrable** ([footgun](../wiki/footguns/partial_unique_constraints_are_not_deferrable.md)). "One live link per account" is kept by the service under a row lock, cancelling the old row before creating the new one, not by a constraint.
7. **Missing locks pass on SQLite** ([footgun](../wiki/footguns/sqlite_hides_missing_locks.md)). Two people using one link at the same moment needs a PostgreSQL test.
8. **No preview deployments.** The human tests on the live site. The change must be additive and have a switch that turns it off without a release, as `NUMPAD` and `ANSWER_IN_PLACE` do.
9. **Entry pages** are built (DESIGN.md, Entry pages addendum): one centred column, the mark, a task heading, 48 px controls, a Show button for passwords, plain words by Django's error code. The new page uses that frame; no new colour, font or asset.

## The risk that shapes the design

A reset link lets its holder become the account. The host creates the link and sees it, so **a host can take over the account of any player they can issue a link for**. In one group of friends this is the accepted trade: the host already keeps everyone's money records. Across groups it is not:

- A person creates a group and invites someone. That someone joins.
- The new "host" issues a reset link for them, opens it, and is now logged in as them.
- If the victim hosts another group, the attacker now holds host power over that group's money records.

The victim would notice (their password stops working), and the audit log names the issuer, but the damage is done by then. The design must limit who a host can issue a link for.

## Options

**Who a host may issue a link for**

- **A. Any member of their group with a login.** Simplest. Leaves the takeover above open.
- **B. Any member with a login, except a site administrator and anyone who hosts another group (recommended).** Closes the path to host power in a group the issuer does not host, and to `/admin/`. A person who hosts two groups and forgets their password asks the site administrator, as today.
- **C. Only people whose single group is this one.** Safest, but a player in two friend groups could never be helped by either host.

With B, a host can still read another group's pages as a player they took over. Players cannot write money records, so the harm is a privacy one among people who accepted both invitations. That remainder is stated in the plan for the human to accept.

**Where the link's life is kept**

- **A. A table in `accounts` (recommended):** the hash, the account, expiry, used and cancelled times, the issuer, and the issuing group's id as a plain number for the audit log (as `AuditEvent` does). `groups` checks the host and calls `accounts`.
- **B. Django's built-in reset token.** It is signed, not stored, so it cannot be cancelled or listed, and it stays valid until the password changes or its time runs out. Rejected for constraint 5.

**After the new password is saved**

- **A. Log the person in and open Your groups (recommended).** Holding the link already proves as much as the new password would.
- **B. Send them to Log in to type it again.** One more screen for no gain.

Django signs every other device out when a password changes; that is wanted here.

**How long a link lasts**

Invites last 7 days because a group chat is slow. A reset link is asked for by someone waiting to get in. **24 hours** is recommended; a host can issue another at any time.

## What stays outside this cycle

A "change my password" screen for a logged-in person, reset by email or SMS, a sole host who forgets (still the site administrator), and claim links for roster players (they need the same token idea but a different rule about history).
