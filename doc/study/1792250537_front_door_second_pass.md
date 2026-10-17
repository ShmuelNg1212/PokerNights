# Front door, second pass: study

Date: 2026-10-17, Asia/Manila. Mode: design, with a small technical part. Shaped with `/impeccable shape`.

## Why

The front door was rebuilt on 2026-10-09 ([plan](../plan/1791542366_front_door_revamp.md)). The critique after it scored 29 of 40 ([snapshot](../../.impeccable/critique/2026-10-09T11-18-45Z__templates-registration-login-html.md)). It left three P1 and two P2 findings. Four of them need a decision from the human, so they went to TODO.md. This study takes those findings, records the human's answers, and defines the brief.

## Who arrives

- **A newcomer.** A friend sent an invite link in a group chat. The person has never seen PokerNights. They are on a phone, often in the chat app's browser, maybe at the table. They decide in seconds whether to trust the page.
- **A returning player or host.** They log in on a new phone or after a logout. They know the app. They want the form and nothing else.

Visitor mode: Operate. The visual authority is the built Rack in DESIGN.md and the 2026-10-09 front-door frame. No new colour, font, asset or motion world.

## Findings carried from the critique

| Finding | Severity | Today |
|---|---|---|
| The description is for the wrong audience | P1 | Top of Log in (every return visit); foot of Sign up, under the button |
| The invite gives no social proof | P1 | "Join {group}" names the group only |
| Four password rules are checked only after sending | P2 | Help text lists them; errors come back from the server |
| "Repeat password" is redundant beside Show | P2 | Two password fields on Sign up and on Set a new password |
| Forgot-password help shows only after a failure | Minor (heuristic 6) | `entry-forgot` is inside the error block |

The critique also computed that the phone keyboard may hide the chip's reactions. That stays on the phone checklist. It is not in this cycle.

## The human's answers (2026-10-17)

1. **Description:** move it. On Sign up it goes directly under the heading. On Log in it is removed; the chip and the name stay. This reverses decision 3 of the 2026-10-09 plan.
2. **Invite:** show the inviter and the count, for example "Hana invited you · 8 players". Anyone who holds the link sees this name and this count.
3. **Password fields:** all three changes. Live ticks for the rules the browser can judge. One password field, with no "Repeat password". The forgot-password line always shows on Log in.

## What the code already has

- `Invite.created_by` is stored (`groups/models.py`). The inviter's name in the group is that user's `Member.display_name`.
- `accounts/signup.py` has the `INVITERS` hook. `groups/apps.py` registers `invite_group_name` and `claim_group_name`. Each returns a group name only. The dependency direction `accounts → groups` stays correct if `groups` returns more data through the same hook.
- `accounts/forms.py` `PlainWords` has the app's wording for each rule. The validators are Django's four defaults: similarity to the username, minimum length 8, common passwords, entirely numeric.
- `RESET_LINKS` is on by default, so the forgot line reads "Ask a host of your group for a reset link."

## Which rules the browser can judge

| Rule | In the browser | Why |
|---|---|---|
| At least 8 characters | Yes | Count of characters |
| Not only digits | Yes | A pattern test |
| Not a common password | No | The list has 20,000 entries; shipping it costs about 200 KB |
| Not like your username | No, not exactly | Django uses a similarity ratio over parts of the username. A copy in JavaScript can disagree with the server |

Decision: tick the two that the browser can judge. Say that the other two are checked on sending. The server stays the only judge; a tick never allows a send that the server refuses. No new endpoint, so a signed-out visitor cannot probe the rules.

## Risks

- **Password managers.** Removing the second field changes the form that a manager sees. Managers handle one new-password field with `autocomplete="new-password"` well. The field names `password1` and `new_password1` stay.
- **A typo in the only password field.** The Show button and the manager cover this. The human accepted this.
- **Privacy of the inviter's name.** A leaked link shows a first name and a count. The human accepted this. A revoked, expired or used-up link shows neither, because the hook returns nothing for it.
- **The inviter left the group.** Then the page shows the count only.

## Out of this study

- The first step for a new player on the group page. This is a separate TODO item.
- The profile page's change-password form. It keeps its repeat field because it is not a front-door screen. See the plan's open questions.
- Claim links. A claim names the player whose history the newcomer takes. It keeps its own heading.
