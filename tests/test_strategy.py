"""
Spot-check basic strategy lookups against the published 6-deck S17 DAS chart.
Tests cover representative cells from each table section.
"""
import pytest
from blackjack.models import Card, Hand
from blackjack.strategy import get_correct_action


def make_hand(*rank_suit_pairs, from_split=False):
    h = Hand(bet=10)
    h.from_split = from_split
    for rank, suit in rank_suit_pairs:
        h.add_card(Card(rank, suit))
    return h


def action(hand, dealer_value):
    act, _ = get_correct_action(hand, dealer_value)
    return act


class TestHardTotals:
    def test_hard_8_vs_6_hit(self):
        h = make_hand(("5", "S"), ("3", "H"))
        assert action(h, 6) == "H"

    def test_hard_9_vs_3_double(self):
        h = make_hand(("5", "S"), ("4", "H"))
        assert action(h, 3) == "D"

    def test_hard_9_vs_2_hit(self):
        h = make_hand(("5", "S"), ("4", "H"))
        assert action(h, 2) == "H"

    def test_hard_10_vs_9_double(self):
        h = make_hand(("6", "S"), ("4", "H"))
        assert action(h, 9) == "D"

    def test_hard_10_vs_10_hit(self):
        h = make_hand(("6", "S"), ("4", "H"))
        assert action(h, 10) == "H"

    def test_hard_11_vs_ace_hit(self):
        h = make_hand(("7", "S"), ("4", "H"))
        assert action(h, 11) == "H"

    def test_hard_11_vs_10_double(self):
        h = make_hand(("7", "S"), ("4", "H"))
        assert action(h, 10) == "D"

    def test_hard_12_vs_4_stand(self):
        h = make_hand(("7", "S"), ("5", "H"))
        assert action(h, 4) == "S"

    def test_hard_12_vs_2_hit(self):
        h = make_hand(("7", "S"), ("5", "H"))
        assert action(h, 2) == "H"

    def test_hard_13_vs_2_stand(self):
        h = make_hand(("8", "S"), ("5", "H"))
        assert action(h, 2) == "S"

    def test_hard_13_vs_7_hit(self):
        h = make_hand(("8", "S"), ("5", "H"))
        assert action(h, 7) == "H"

    def test_hard_16_vs_10_hit(self):
        h = make_hand(("9", "S"), ("7", "H"))
        assert action(h, 10) == "H"

    def test_hard_17_vs_ace_stand(self):
        h = make_hand(("10", "S"), ("7", "H"))
        assert action(h, 11) == "S"


class TestSoftTotals:
    def test_soft_13_vs_5_double(self):
        h = make_hand(("A", "S"), ("2", "H"))
        assert h.is_soft
        assert h.total == 13
        assert action(h, 5) == "D"

    def test_soft_13_vs_4_hit(self):
        h = make_hand(("A", "S"), ("2", "H"))
        assert action(h, 4) == "H"

    def test_soft_17_vs_2_hit(self):
        h = make_hand(("A", "S"), ("6", "H"))
        assert h.total == 17
        assert h.is_soft
        assert action(h, 2) == "H"

    def test_soft_18_vs_2_double_stand(self):
        h = make_hand(("A", "S"), ("7", "H"))
        assert h.total == 18
        result, _ = get_correct_action(h, 2)
        assert result == "DS"

    def test_soft_18_vs_9_hit(self):
        h = make_hand(("A", "S"), ("7", "H"))
        assert action(h, 9) == "H"

    def test_soft_19_vs_6_stand(self):
        h = make_hand(("A", "S"), ("8", "H"))
        assert action(h, 6) == "S"

    def test_soft_20_always_stand(self):
        h = make_hand(("A", "S"), ("9", "H"))
        for dealer in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11):
            assert action(h, dealer) == "S"


class TestPairs:
    def test_aces_always_split(self):
        h = make_hand(("A", "S"), ("A", "H"))
        for dealer in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11):
            assert action(h, dealer) == "P"

    def test_eights_always_split(self):
        h = make_hand(("8", "S"), ("8", "H"))
        for dealer in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11):
            assert action(h, dealer) == "P"

    def test_tens_never_split(self):
        h = make_hand(("10", "S"), ("10", "H"))
        for dealer in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11):
            assert action(h, dealer) == "S"

    def test_fives_never_split_double_instead(self):
        h = make_hand(("5", "S"), ("5", "H"))
        # 5s treated like hard 10 — double vs 2-9, hit vs 10/A
        assert action(h, 6) == "D"
        assert action(h, 10) == "H"

    def test_nines_split_vs_9(self):
        h = make_hand(("9", "S"), ("9", "H"))
        assert action(h, 9) == "P"

    def test_nines_stand_vs_7(self):
        h = make_hand(("9", "S"), ("9", "H"))
        assert action(h, 7) == "S"

    def test_twos_split_vs_7(self):
        h = make_hand(("2", "S"), ("2", "H"))
        assert action(h, 7) == "P"

    def test_twos_hit_vs_8(self):
        h = make_hand(("2", "S"), ("2", "H"))
        assert action(h, 8) == "H"


class TestReasonString:
    def test_reason_not_empty(self):
        h = make_hand(("8", "S"), ("8", "H"))
        _, reason = get_correct_action(h, 10)
        assert len(reason) > 0

    def test_reason_includes_dealer(self):
        h = make_hand(("11", "S"), ("7", "H")) if False else make_hand(("7", "S"), ("4", "H"))
        _, reason = get_correct_action(h, 6)
        assert "6" in reason or "dealer" in reason.lower()
