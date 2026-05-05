import translations as i18n


def test_empty_header_returns_english():
    assert i18n.get_translations("")["create_group"] == "Create group"


def test_no_header_returns_english():
    assert i18n.get_translations()["create_group"] == "Create group"


def test_french_detected():
    assert (
        i18n.get_translations("fr-FR,fr;q=0.9,en;q=0.8")["create_group"]
        == "Créer un groupe"
    )


def test_french_short_tag():
    assert i18n.get_translations("fr")["create_group"] == "Créer un groupe"


def test_english_explicit():
    assert i18n.get_translations("en-US,en;q=0.9")["create_group"] == "Create group"


def test_unknown_locale_falls_back_to_english():
    assert i18n.get_translations("zh-CN,zh;q=0.9")["create_group"] == "Create group"


def test_french_as_second_preference_when_first_unknown():
    assert (
        i18n.get_translations("zh;q=0.9,fr;q=0.8")["create_group"] == "Créer un groupe"
    )


def test_both_langs_have_identical_keys():
    en = i18n.get_translations("en")
    fr = i18n.get_translations("fr")
    assert set(en.keys()) == set(fr.keys())


def test_all_keys_present():
    t = i18n.get_translations("en")
    expected = {
        "group_name",
        "members_hint",
        "member_placeholder",
        "add_member",
        "create_group",
        "description",
        "amount",
        "for",
        "add_spending",
        "spendings",
        "paid",
        "no_spendings",
        "owes",
        "all_settled",
        "copy_link",
        "copied",
        "new_spending",
        "paid_by",
        "delete",
        "confirm_delete",
        "total",
        "all",
        "spending_added",
        "history",
        "no_history",
        "my_groups",
        "refresh",
        "confirm_remove_group",
        "date",
        "reasons",
    }
    assert expected == set(t.keys())


def test_reasons_is_list_of_100():
    for lang in ("en", "fr"):
        t = i18n.get_translations(lang)
        assert isinstance(t["reasons"], list), f"{lang}: reasons should be a list"
        assert len(t["reasons"]) == 109, (
            f"{lang}: expected 109 reasons, got {len(t['reasons'])}"
        )
