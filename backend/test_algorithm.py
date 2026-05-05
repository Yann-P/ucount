from algorithm import compute_balances, compute_stats, settle


def group(members, spendings=None):
    return {"members": members, "spendings": spendings or []}


def spending(paid_by, amount, beneficiaries):
    return {"paid_by": paid_by, "amount": amount, "beneficiaries": beneficiaries}


def apply_txns(balances, txns):
    """Apply transactions to balances and return resulting balances (should all be ~0)."""
    result = dict(balances)
    for t in txns:
        result[t["payer"]] += t["amount"]
        result[t["payee"]] -= t["amount"]
    return result


# --- compute_stats ---


def test_stats_empty_spendings():
    s = compute_stats(group(["Alice", "Bob"]))
    assert s["total"] == 0.0
    assert all(m["paid"] == 0.0 and m["balance"] == 0.0 for m in s["members"])


def test_stats_total_is_sum_of_spendings():
    g = group(
        ["Alice", "Bob"],
        [
            spending("Alice", 30, ["Alice", "Bob"]),
            spending("Bob", 10, ["Alice", "Bob"]),
        ],
    )
    assert compute_stats(g)["total"] == 40.0


def test_stats_paid_per_member():
    g = group(
        ["Alice", "Bob", "Charlie"],
        [
            spending("Alice", 30, ["Alice", "Bob", "Charlie"]),
            spending("Alice", 10, ["Alice", "Bob"]),
        ],
    )
    s = compute_stats(g)
    by_name = {m["name"]: m for m in s["members"]}
    assert by_name["Alice"]["paid"] == 40.0
    assert by_name["Bob"]["paid"] == 0.0
    assert by_name["Charlie"]["paid"] == 0.0


def test_stats_balance_matches_compute_balances():
    g = group(
        ["Alice", "Bob", "Charlie"],
        [
            spending("Alice", 30, ["Alice", "Bob", "Charlie"]),
        ],
    )
    s = compute_stats(g)
    expected = compute_balances(g)
    by_name = {m["name"]: m for m in s["members"]}
    for name, bal in expected.items():
        assert by_name[name]["balance"] == bal


def test_stats_member_order_matches_group():
    members = ["Charlie", "Alice", "Bob"]
    g = group(members, [spending("Alice", 30, members)])
    s = compute_stats(g)
    assert [m["name"] for m in s["members"]] == members


# --- compute_balances ---


def test_no_spendings_all_zero():
    b = compute_balances(group(["Alice", "Bob", "Charlie"]))
    assert b == {"Alice": 0.0, "Bob": 0.0, "Charlie": 0.0}


def test_single_spending_equal_split():
    g = group(
        ["Alice", "Bob", "Charlie"],
        [spending("Alice", 30, ["Alice", "Bob", "Charlie"])],
    )
    b = compute_balances(g)
    assert b["Alice"] == 20.0  # paid 30, owes 10
    assert b["Bob"] == -10.0
    assert b["Charlie"] == -10.0


def test_payer_not_in_beneficiaries():
    g = group(["Alice", "Bob", "Charlie"], [spending("Alice", 20, ["Bob", "Charlie"])])
    b = compute_balances(g)
    assert b["Alice"] == 20.0
    assert b["Bob"] == -10.0
    assert b["Charlie"] == -10.0


def test_payer_only_beneficiary_nets_zero():
    g = group(["Alice", "Bob"], [spending("Alice", 10, ["Alice"])])
    b = compute_balances(g)
    assert b["Alice"] == 0.0
    assert b["Bob"] == 0.0


def test_multiple_spendings_accumulate():
    g = group(
        ["Alice", "Bob", "Charlie"],
        [
            spending("Alice", 30, ["Alice", "Bob", "Charlie"]),
            spending("Bob", 30, ["Alice", "Bob", "Charlie"]),
        ],
    )
    b = compute_balances(g)
    assert b["Alice"] == 10.0
    assert b["Bob"] == 10.0
    assert b["Charlie"] == -20.0


def test_two_equal_payers_net_zero():
    g = group(
        ["Alice", "Bob"],
        [
            spending("Alice", 20, ["Alice", "Bob"]),
            spending("Bob", 20, ["Alice", "Bob"]),
        ],
    )
    b = compute_balances(g)
    assert b["Alice"] == 0.0
    assert b["Bob"] == 0.0


def test_balances_always_sum_to_zero():
    g = group(
        ["Alice", "Bob", "Charlie", "Dave"],
        [
            spending("Alice", 100, ["Alice", "Bob", "Charlie", "Dave"]),
            spending("Bob", 37, ["Bob", "Charlie"]),
            spending("Charlie", 15, ["Alice", "Dave"]),
        ],
    )
    b = compute_balances(g)
    assert abs(sum(b.values())) < 0.01


def test_non_divisible_amount_rounds_correctly():
    g = group(
        ["Alice", "Bob", "Charlie"],
        [spending("Alice", 10, ["Alice", "Bob", "Charlie"])],
    )
    b = compute_balances(g)
    assert abs(sum(b.values())) < 0.01
    assert b["Alice"] == round(10 - 10 / 3, 2)


# --- settle ---


def test_settle_empty_balances():
    assert settle({"Alice": 0.0, "Bob": 0.0}) == []


def test_settle_two_people():
    txns = settle({"Alice": 10.0, "Bob": -10.0})
    assert len(txns) == 1
    assert txns[0] == {"payer": "Bob", "payee": "Alice", "amount": 10.0}


def test_settle_one_creditor_two_debtors():
    txns = settle({"Alice": 20.0, "Bob": -10.0, "Charlie": -10.0})
    assert len(txns) == 2
    payees = {t["payee"] for t in txns}
    payers = {t["payer"] for t in txns}
    assert payees == {"Alice"}
    assert payers == {"Bob", "Charlie"}
    assert sum(t["amount"] for t in txns) == 20.0


def test_settle_two_creditors_one_debtor():
    txns = settle({"Alice": 10.0, "Bob": 10.0, "Charlie": -20.0})
    assert len(txns) == 2
    assert {t["payer"] for t in txns} == {"Charlie"}
    assert {t["payee"] for t in txns} == {"Alice", "Bob"}


def test_settle_transactions_clear_all_debts():
    balances = {"Alice": 20.0, "Bob": -5.0, "Charlie": -7.0, "Dave": -8.0}
    txns = settle(balances)
    result = apply_txns(balances, txns)
    assert all(abs(v) < 0.01 for v in result.values())


def test_settle_minimal_transactions_simple_chain():
    # Alice owed 30, Bob owes 10, Charlie owes 20 → 2 txns (not 3)
    balances = {"Alice": 30.0, "Bob": -10.0, "Charlie": -20.0}
    txns = settle(balances)
    assert len(txns) == 2


def test_settle_minimal_transactions_large_group():
    # 5 debtors all owe the same person → 5 txns, not more
    balances = {
        "Alice": 50.0,
        "B": -10.0,
        "C": -10.0,
        "D": -10.0,
        "E": -10.0,
        "F": -10.0,
    }
    txns = settle(balances)
    assert len(txns) == 5
    assert all(t["payee"] == "Alice" for t in txns)


def test_settle_perfectly_matching_pairs():
    # 2 creditors, 2 debtors with matching amounts → 2 txns (not 3)
    balances = {"Alice": 10.0, "Bob": 20.0, "Charlie": -10.0, "Dave": -20.0}
    txns = settle(balances)
    assert len(txns) == 2
    result = apply_txns(balances, txns)
    assert all(abs(v) < 0.01 for v in result.values())


def test_settle_amounts_are_correct():
    balances = {"Alice": 15.0, "Bob": -7.0, "Charlie": -8.0}
    txns = settle(balances)
    result = apply_txns(balances, txns)
    assert all(abs(v) < 0.01 for v in result.values())


def test_settle_full_pipeline_from_group():
    # Alice: +10, Bob: +10, Charlie: -20 → 2 txns, both from Charlie
    g = group(
        ["Alice", "Bob", "Charlie"],
        [
            spending("Alice", 30, ["Alice", "Bob", "Charlie"]),
            spending("Bob", 30, ["Alice", "Bob", "Charlie"]),
        ],
    )
    balances = compute_balances(g)
    txns = settle(balances)
    assert len(txns) == 2
    assert all(t["payer"] == "Charlie" for t in txns)
    assert sum(t["amount"] for t in txns) == 20.0


def test_settle_pipeline_clears_complex_group():
    g = group(
        ["Alice", "Bob", "Charlie", "Dave"],
        [
            spending("Alice", 120, ["Alice", "Bob", "Charlie", "Dave"]),
            spending("Bob", 40, ["Bob", "Charlie"]),
            spending("Charlie", 20, ["Alice", "Dave"]),
        ],
    )
    balances = compute_balances(g)
    txns = settle(balances)
    result = apply_txns(balances, txns)
    assert all(abs(v) < 0.01 for v in result.values())
