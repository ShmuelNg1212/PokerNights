"""Settle-up: who pays whom. Pure functions on integers; no database, no float.

A *balance* is what a party is still owed (positive) or still owes (negative),
in the game's unit. Balances always sum to zero. ``settle`` returns the transfers that
make every balance zero, using the minimum possible number of transfers.

Why the result is minimal. Draw any settlement as a graph: parties are nodes
and transfers are edges. Money only moves inside a connected component, so the
balances in each component sum to zero, and a component with m parties needs
at least m − 1 edges. A settlement with c components therefore has at least
n − c transfers. c can be at most k, the largest number of zero-sum groups the
parties can be split into, so no settlement has fewer than n − k transfers.
``settle`` finds such a split with k groups and uses m − 1 transfers in each
group: n − k in all.
"""

# Above this many parties the exact search is skipped. A table has at most 12
# seats (13 parties with a banker), so the fallback is never reached in practice.
EXACT_LIMIT = 16


def balances(nets: dict, payments=()) -> dict:
    """What each party is still owed, from results and money that already moved.

    ``nets`` maps a party to its result (cash-out − buy-ins). ``payments`` is a
    list of ``(payer, payee, amount)`` already made. A payer is owed more by
    that amount and a payee less. A party that appears only in payments (for
    example a banker, whose own result is zero) is included.
    """
    result = dict(nets)
    for payer, payee, amount in payments:
        result[payer] = result.get(payer, 0) + amount
        result[payee] = result.get(payee, 0) - amount
    return result


def _zero_sum_groups(amounts: list[int]) -> list[list[int]]:
    """Split positions 0..n-1 into the largest number of groups that each sum to zero.

    Dynamic programming over subsets. ``best[mask]`` is the largest number of
    zero-sum groups that the positions in ``mask`` can form; it is only defined
    for masks that sum to zero. The group that holds the lowest position of a
    mask is tried in increasing subset order and the first best split is kept,
    so the same input always gives the same groups.
    """
    n = len(amounts)
    full = (1 << n) - 1
    sums = [0] * (1 << n)
    for mask in range(1, 1 << n):
        low = mask & -mask
        sums[mask] = sums[mask ^ low] + amounts[low.bit_length() - 1]

    best = {0: 0}
    choice = {}

    def solve(mask: int) -> int:
        if mask in best:
            return best[mask]
        low = mask & -mask
        rest = mask ^ low
        best_count, best_group = 1, mask  # the whole mask as one group always works
        sub = rest
        # Every proper subset of ``rest``, joined with the lowest position, as a candidate group.
        while True:
            sub = (sub - 1) & rest
            group = sub | low
            if sums[group] == 0:
                count = 1 + solve(mask ^ group)
                if count > best_count or (count == best_count and group < best_group):
                    best_count, best_group = count, group
            if sub == 0:
                break
        best[mask] = best_count
        choice[mask] = best_group
        return best_count

    solve(full)
    groups, mask = [], full
    while mask:
        group = choice[mask]
        groups.append([i for i in range(n) if group >> i & 1])
        mask ^= group
    return groups


def _settle_group(amounts: list[int], members: list[int]) -> list[tuple[int, int, int]]:
    """m − 1 transfers that clear one zero-sum group: the largest debtor pays the largest creditor."""
    left = {i: amounts[i] for i in members}
    transfers = []
    while True:
        debtor = min(members, key=lambda i: (left[i], i))  # most negative; ties to the earlier position
        creditor = max(members, key=lambda i: (left[i], -i))  # most positive; ties to the earlier position
        if left[debtor] == 0:
            return transfers
        amount = min(-left[debtor], left[creditor])
        transfers.append((debtor, creditor, amount))
        left[debtor] += amount
        left[creditor] -= amount


def settle(parties: list[tuple]) -> list[tuple]:
    """Transfers ``(payer, payee, amount)`` that make every balance zero.

    ``parties`` is a list of ``(key, balance)`` in a fixed order (join order).
    The order decides ties, so the same input always gives the same list.
    """
    if any(not isinstance(amount, int) or isinstance(amount, bool) for _, amount in parties):
        raise ValueError("Balances must be integers.")
    if sum(amount for _, amount in parties) != 0:
        raise ValueError("Balances must sum to zero.")
    open_parties = [(key, amount) for key, amount in parties if amount != 0]
    keys = [key for key, _ in open_parties]
    amounts = [amount for _, amount in open_parties]
    if not amounts:
        return []
    if len(amounts) <= EXACT_LIMIT:
        groups = _zero_sum_groups(amounts)
    else:
        groups = [list(range(len(amounts)))]  # one group: correct, but not proven minimal
    transfers = []
    for group in groups:
        transfers.extend((keys[a], keys[b], amount) for a, b, amount in _settle_group(amounts, group))
    return transfers


def is_proven_minimal(parties: list[tuple]) -> bool:
    """Whether ``settle`` used the exact search for this input."""
    return sum(1 for _, amount in parties if amount != 0) <= EXACT_LIMIT
