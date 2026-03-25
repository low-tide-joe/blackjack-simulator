import random
from dataclasses import dataclass, field
from typing import List, Optional

SUITS = {"S": "\u2660", "H": "\u2665", "D": "\u2666", "C": "\u2663"}
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RED_SUITS = {"H", "D"}

NUM_DECKS = 6
PENETRATION = 0.75  # reshuffle after 75% of shoe dealt


@dataclass
class Card:
    rank: str
    suit: str

    @property
    def value(self) -> int:
        if self.rank in ("J", "Q", "K"):
            return 10
        if self.rank == "A":
            return 11
        return int(self.rank)

    @property
    def hi_lo_value(self) -> int:
        if self.rank in ("2", "3", "4", "5", "6"):
            return 1
        if self.rank in ("7", "8", "9"):
            return 0
        return -1  # 10, J, Q, K, A

    @property
    def is_red(self) -> bool:
        return self.suit in RED_SUITS

    def __str__(self) -> str:
        return f"{self.rank}{SUITS[self.suit]}"

    def __repr__(self) -> str:
        return self.__str__()


class Hand:
    def __init__(self, bet: int = 0):
        self.cards: List[Card] = []
        self.bet: int = bet
        self.doubled: bool = False
        self.from_split: bool = False
        self.split_from_aces: bool = False  # aces split — only one card each

    def add_card(self, card: Card) -> None:
        self.cards.append(card)

    @property
    def total(self) -> int:
        total = sum(c.value for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == "A")
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    @property
    def is_soft(self) -> bool:
        total = sum(c.value for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == "A")
        while total > 21 and aces:
            total -= 10
            aces -= 1
        # soft if at least one ace still counting as 11
        return total <= 21 and any(c.rank == "A" for c in self.cards) and (total - sum(
            c.value for c in self.cards if c.rank != "A"
        ) - sum(1 for c in self.cards if c.rank == "A")) >= 0 and self._has_soft_ace()

    def _has_soft_ace(self) -> bool:
        """True if an ace is counting as 11 in the current total."""
        hard_total = sum(1 if c.rank == "A" else c.value for c in self.cards)
        return (self.total - hard_total) == 10

    @property
    def is_blackjack(self) -> bool:
        return (
            len(self.cards) == 2
            and self.total == 21
            and not self.from_split
        )

    @property
    def is_busted(self) -> bool:
        return self.total > 21

    @property
    def can_split(self) -> bool:
        return (
            len(self.cards) == 2
            and self.cards[0].rank == self.cards[1].rank
            and not self.split_from_aces
        )

    @property
    def can_double(self) -> bool:
        return len(self.cards) == 2 and not self.split_from_aces

    def __repr__(self) -> str:
        return f"Hand({self.cards}, total={self.total})"


class Shoe:
    def __init__(self, num_decks: int = NUM_DECKS):
        self.num_decks = num_decks
        self.cards: List[Card] = []
        self.cut_card_pos: int = 0
        self._build_and_shuffle()

    def _build_and_shuffle(self) -> None:
        self.cards = [
            Card(rank, suit)
            for _ in range(self.num_decks)
            for suit in SUITS
            for rank in RANKS
        ]
        random.shuffle(self.cards)
        total = len(self.cards)
        # cut card placed near the end of the penetration point
        self.cut_card_pos = int(total * PENETRATION)
        self._dealt = 0

    def deal_one(self) -> Card:
        if not self.cards:
            self._build_and_shuffle()
        card = self.cards.pop(0)
        self._dealt += 1
        return card

    @property
    def needs_reshuffle(self) -> bool:
        return self._dealt >= self.cut_card_pos

    @property
    def decks_remaining(self) -> float:
        cards_remaining = len(self.cards)
        return max(cards_remaining / 52, 0.5)  # floor at 0.5 to avoid div-by-zero

    def reshuffle(self) -> None:
        self._build_and_shuffle()
