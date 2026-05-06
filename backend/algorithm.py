def compute_stats(group: dict) -> dict:
    """Per-member totals: how much each person paid and their net balance."""
    total = round(sum(s["amount"] for s in group["spendings"]), 2)
    paid = {m: 0.0 for m in group["members"]}
    for s in group["spendings"]:
        paid[s["paid_by"]] = round(paid[s["paid_by"]] + s["amount"], 2)
    balances = compute_balances(group)
    return {
        "total": total,
        "members": [
            {"name": m, "paid": paid[m], "balance": balances[m]}
            for m in group["members"]
        ],
    }


def compute_balances(group: dict) -> dict[str, float]:
    """Net balance per member. Positive = owed money. Negative = owes money."""
    balances = {m: 0.0 for m in group["members"]}
    for s in group["spendings"]:
        n = len(s["beneficiaries"])
        if n == 0:
            continue
        share = s["amount"] / n
        balances[s["paid_by"]] += s["amount"]
        for b in s["beneficiaries"]:
            balances[b] -= share
    return {m: round(b, 2) for m, b in balances.items()}


def compute_flows(group: dict) -> list[dict]:
    """Spending flows: total amount each payer covered for each beneficiary across all spendings."""
    paid_for: dict[tuple[str, str], float] = {}
    for s in group["spendings"]:
        n = len(s["beneficiaries"])
        if n == 0:
            continue
        share = s["amount"] / n
        for b in s["beneficiaries"]:
            if b != s["paid_by"]:
                key = (s["paid_by"], b)
                paid_for[key] = paid_for.get(key, 0) + share
    return [
        {"from": payer, "to": beneficiary, "amount": round(amount, 2)}
        for (payer, beneficiary), amount in paid_for.items()
        if amount > 0.005
    ]


def settle(balances: dict[str, float]) -> list[dict]:
    """Minimal transactions to clear all debts. Greedy: largest creditor meets largest debtor."""
    EPSILON = 0.005
    creditors = sorted(
        [(v, k) for k, v in balances.items() if v > EPSILON], reverse=True
    )
    debtors = sorted(
        [(-v, k) for k, v in balances.items() if v < -EPSILON], reverse=True
    )

    txns = []
    i, j = 0, 0

    while i < len(creditors) and j < len(debtors):
        credit, creditor = creditors[i]
        debt, debtor = debtors[j]
        amount = round(min(credit, debt), 2)
        txns.append({"payer": debtor, "payee": creditor, "amount": amount})
        creditors[i] = (round(credit - amount, 2), creditor)
        debtors[j] = (round(debt - amount, 2), debtor)
        if creditors[i][0] <= EPSILON:
            i += 1
        if debtors[j][0] <= EPSILON:
            j += 1

    return txns
