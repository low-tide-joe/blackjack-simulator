import pytest
from blackjack.models import Card, Hand, Shoe


def card(rank, suit="S"):
    return Card(rank, suit)


class TestCard:
    def test_number_value(self):
        assert card("7").value == 7
        assert card("2").value == 2

    def test_face_value(self):
        assert card("J").value == 10
        assert card("Q").value == 10
        assert card("K").value == 10

    def test_ace_value(self):
        assert card("A").value == 11

    def test_hi_lo_low(self):
        for rank in ("2", "3", "4", "5", "6"):
            assert card(rank).hi_lo_value == 1

    def test_hi_lo_neutral(self):
        for rank in ("7", "8", "9"):
            assert card(rank).hi_lo_value == 0

    def test_hi_lo_high(self):
        for rank in ("10", "J", "Q", "K", "A"):
            assert card(rank).hi_lo_value == -1

    def test_is_red(self):
        assert card("A", "H").is_red
        assert card("A", "D").is_red
        assert not card("A", "S").is_red
        assert not card("A", "C").is_red

    def test_str_includes_suit_symbol(self):
        c = card("A", "S")
        assert "A" in str(c)
        assert "♠" in str(c)


class TestHand:
    def test_simple_total(self):
        h = Hand()
        h.add_card(card("7"))
        h.add_card(card("8"))
        assert h.total == 15

    def test_soft_ace(self):
        h = Hand()
        h.add_card(card("A"))
        h.add_card(card("6"))
        assert h.total == 17
        assert h.is_soft

    def test_hard_ace_when_bust_would_occur(self):
        h = Hand()
        h.add_card(card("A"))
        h.add_card(card("9"))
        h.add_card(card("5"))
        assert h.total == 15
        assert not h.is_soft

    def test_two_aces(self):
        h = Hand()
        h.add_card(card("A"))
        h.add_card(card("A"))
        assert h.total == 12

    def test_blackjack(self):
        h = Hand()
        h.add_card(card("A"))
        h.add_card(card("K"))
        assert h.is_blackjack
        assert h.total == 21

    def test_no_blackjack_on_split(self):
        h = Hand()
        h.add_card(card("A"))
        h.add_card(card("K"))
        h.from_split = True
        assert not h.is_blackjack

    def test_busted(self):
        h = Hand()
        h.add_card(card("K"))
        h.add_card(card("Q"))
        h.add_card(card("5"))
        assert h.is_busted
        assert h.total > 21

    def test_can_split(self):
        h = Hand()
        h.add_card(card("8", "H"))
        h.add_card(card("8", "S"))
        assert h.can_split

    def test_cannot_split_different_ranks(self):
        h = Hand()
        h.add_card(card("8"))
        h.add_card(card("9"))
        assert not h.can_split

    def test_cannot_split_three_cards(self):
        h = Hand()
        h.add_card(card("8"))
        h.add_card(card("8"))
        h.add_card(card("2"))
        assert not h.can_split

    def test_can_double_two_cards(self):
        h = Hand()
        h.add_card(card("5"))
        h.add_card(card("6"))
        assert h.can_double

    def test_cannot_double_three_cards(self):
        h = Hand()
        h.add_card(card("5"))
        h.add_card(card("6"))
        h.add_card(card("2"))
        assert not h.can_double


class TestShoe:
    def test_shoe_size(self):
        shoe = Shoe(num_decks=6)
        assert len(shoe.cards) == 6 * 52

    def test_deal_one(self):
        shoe = Shoe()
        initial = len(shoe.cards)
        shoe.deal_one()
        assert len(shoe.cards) == initial - 1

    def test_needs_reshuffle_after_penetration(self):
        shoe = Shoe(num_decks=6)
        total = 6 * 52
        # Deal past 75% penetration
        for _ in range(int(total * 0.76)):
            shoe.deal_one()
        assert shoe.needs_reshuffle

    def test_not_needs_reshuffle_initially(self):
        shoe = Shoe()
        assert not shoe.needs_reshuffle

    def test_decks_remaining_positive(self):
        shoe = Shoe()
        assert shoe.decks_remaining > 0
