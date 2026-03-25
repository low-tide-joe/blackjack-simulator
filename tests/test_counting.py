import pytest
from blackjack.models import Card, Shoe
from blackjack.counting import HiLoCounter


def card(rank):
    return Card(rank, "S")


class TestHiLoCounter:
    def setup_method(self):
        self.shoe = Shoe()
        self.counter = HiLoCounter(self.shoe)

    def test_starts_at_zero(self):
        assert self.counter.running_count == 0

    def test_low_cards_increment(self):
        for rank in ("2", "3", "4", "5", "6"):
            self.counter.update(card(rank))
        assert self.counter.running_count == 5

    def test_neutral_cards_no_change(self):
        for rank in ("7", "8", "9"):
            self.counter.update(card(rank))
        assert self.counter.running_count == 0

    def test_high_cards_decrement(self):
        for rank in ("10", "J", "Q", "K", "A"):
            self.counter.update(card(rank))
        assert self.counter.running_count == -5

    def test_balanced_deck(self):
        # A full deck has equal highs and lows — should sum to 0
        from blackjack.models import RANKS
        for rank in RANKS:
            self.counter.update(card(rank))
        assert self.counter.running_count == 0

    def test_true_count_calculation(self):
        # Set running count manually and check true count math
        self.counter.running_count = 6
        decks_rem = self.shoe.decks_remaining
        expected = 6 / decks_rem
        assert abs(self.counter.true_count - expected) < 0.01

    def test_reset(self):
        self.counter.update(card("A"))
        self.counter.update(card("2"))
        self.counter.reset()
        assert self.counter.running_count == 0
