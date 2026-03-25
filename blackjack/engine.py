"""
GameEngine — pure game logic, zero I/O.
All state changes return data; the UI layer is responsible for display.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Tuple

from blackjack.models import Card, Hand, Shoe
from blackjack.counting import HiLoCounter
from blackjack.strategy import get_correct_action

BLACKJACK_PAYOUT = 1.5   # 3:2
MAX_SPLITS = 4            # max hands a seat can have after splitting
MAX_SEATS = 3


class Action(str, Enum):
    HIT = "h"
    STAND = "s"
    DOUBLE = "d"
    SPLIT = "p"


class RoundPhase(Enum):
    BETTING = auto()
    PLAYER_TURN = auto()
    DEALER_TURN = auto()
    SETTLEMENT = auto()
    DONE = auto()


@dataclass
class StrategyResult:
    player_action: str          # what the player did
    correct_action: str         # what basic strategy says
    reason: str                 # explanation
    was_correct: bool


@dataclass
class HandResult:
    hand: Hand
    outcome: str        # "win", "lose", "push", "blackjack", "bust"
    payout: int         # net chips (positive = gain, negative = loss)
    strategy_checks: List[StrategyResult] = field(default_factory=list)


@dataclass
class RoundResult:
    seat_results: List[List[HandResult]]  # [seat_index][hand_index]
    dealer_hand: Hand
    reshuffled: bool = False


class GameEngine:
    def __init__(self, num_seats: int = 1, mode: str = "practice", starting_bankroll: int = 1000):
        assert 1 <= num_seats <= MAX_SEATS
        assert mode in ("practice", "bankroll")
        self.num_seats = num_seats
        self.mode = mode
        self.bankroll = starting_bankroll if mode == "bankroll" else None

        self.shoe = Shoe()
        self.counter = HiLoCounter(self.shoe)

        # Per-session stats
        self.hands_played: int = 0
        self.correct_decisions: int = 0
        self.total_decisions: int = 0

        # Round state
        self._bets: List[int] = [0] * num_seats
        self._dealer_hand: Optional[Hand] = None
        self._seats: List[List[Hand]] = [[] for _ in range(num_seats)]
        self._phase: RoundPhase = RoundPhase.BETTING
        self._active_seat: int = 0
        self._active_hand_idx: int = 0
        self._reshuffled_this_round: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def phase(self) -> RoundPhase:
        return self._phase

    @property
    def dealer_hand(self) -> Optional[Hand]:
        return self._dealer_hand

    @property
    def seats(self) -> List[List[Hand]]:
        return self._seats

    @property
    def active_seat(self) -> int:
        return self._active_seat

    @property
    def active_hand_idx(self) -> int:
        return self._active_hand_idx

    @property
    def active_hand(self) -> Optional[Hand]:
        if self._seats and self._seats[self._active_seat]:
            return self._seats[self._active_seat][self._active_hand_idx]
        return None

    def set_bet(self, seat: int, amount: int) -> None:
        assert self._phase == RoundPhase.BETTING
        if self.mode == "bankroll":
            if amount <= 0:
                raise ValueError("Bet must be positive")
            if amount > self.bankroll:
                raise ValueError(f"Insufficient bankroll (have {self.bankroll})")
        self._bets[seat] = amount

    def deal_round(self) -> None:
        """Deal initial two cards to all seats and dealer."""
        assert self._phase == RoundPhase.BETTING
        if self.mode == "bankroll":
            for i in range(self.num_seats):
                if self._bets[i] <= 0:
                    raise ValueError(f"Seat {i+1} has no bet")
        else:
            # Practice mode — use dummy bets of 1
            self._bets = [1] * self.num_seats

        self._reshuffled_this_round = False
        if self.shoe.needs_reshuffle:
            self.shoe.reshuffle()
            self.counter.reset()
            self._reshuffled_this_round = True

        # Reset seats
        self._seats = [[Hand(bet=self._bets[i])] for i in range(self.num_seats)]
        self._dealer_hand = Hand()

        # Deal: seat0 card, dealer card, seat0 card2, dealer card2 (seat1/2 same)
        for _ in range(2):
            for seat in range(self.num_seats):
                self._deal_to(self._seats[seat][0])
            self._deal_to(self._dealer_hand)

        self._active_seat = 0
        self._active_hand_idx = 0
        self._phase = RoundPhase.PLAYER_TURN
        self._strategy_checks: List[List[List[StrategyResult]]] = [
            [[]] for _ in range(self.num_seats)
        ]

        # If all seats have blackjack immediately, skip to dealer
        self._advance_if_needed()

    def player_action(self, action: Action) -> Optional[StrategyResult]:
        """
        Execute a player action on the current active hand.
        Returns a StrategyResult (for immediate feedback) or None if the
        action phase ended.
        """
        assert self._phase == RoundPhase.PLAYER_TURN
        hand = self.active_hand
        dealer_upcard = self._dealer_hand.cards[0].value

        # Validate action is legal
        if action == Action.DOUBLE and not hand.can_double:
            raise ValueError("Cannot double on this hand")
        if action == Action.SPLIT and not hand.can_split:
            raise ValueError("Cannot split this hand")
        if action == Action.SPLIT and len(self._seats[self._active_seat]) >= MAX_SPLITS:
            raise ValueError("Maximum splits reached")

        # Check against basic strategy
        correct_action, reason = get_correct_action(hand, dealer_upcard)
        # Map DS to D/S depending on available action
        resolved_correct = correct_action
        if correct_action == "DS":
            resolved_correct = "D" if hand.can_double else "S"

        player_action_str = action.value.upper()
        # Map action enum back to strategy letter
        action_map = {Action.HIT: "H", Action.STAND: "S", Action.DOUBLE: "D", Action.SPLIT: "P"}
        player_strategy_letter = action_map[action]

        was_correct = player_strategy_letter == resolved_correct
        result = StrategyResult(
            player_action=player_strategy_letter,
            correct_action=resolved_correct,
            reason=reason,
            was_correct=was_correct,
        )

        # Track stats
        self.total_decisions += 1
        if was_correct:
            self.correct_decisions += 1

        # Store check
        self._strategy_checks[self._active_seat][self._active_hand_idx].append(result)

        # Execute action
        if action == Action.HIT:
            self._deal_to(hand)
            if hand.is_busted or hand.split_from_aces:
                self._advance_hand()
        elif action == Action.STAND:
            self._advance_hand()
        elif action == Action.DOUBLE:
            hand.doubled = True
            hand.bet *= 2
            if self.mode == "bankroll":
                self.bankroll -= hand.bet // 2  # extra bet placed
            self._deal_to(hand)
            self._advance_hand()
        elif action == Action.SPLIT:
            self._execute_split()

        return result

    def dealer_play(self) -> None:
        """Run dealer's turn: hit until 17+ (stands on soft 17)."""
        assert self._phase == RoundPhase.DEALER_TURN
        # Reveal hole card (already in hand, just marking phase)
        while True:
            total = self._dealer_hand.total
            is_soft = self._dealer_hand.is_soft
            # Dealer stands on soft 17 (S17 rule)
            if total > 17 or (total == 17):
                break
            self._deal_to(self._dealer_hand)
        self._phase = RoundPhase.SETTLEMENT

    def settle(self) -> RoundResult:
        """Resolve all hands, update bankroll, return results."""
        assert self._phase == RoundPhase.SETTLEMENT
        dealer_total = self._dealer_hand.total
        dealer_bj = self._dealer_hand.is_blackjack

        seat_results: List[List[HandResult]] = []

        for seat_idx, hands in enumerate(self._seats):
            hand_results = []
            for hand_idx, hand in enumerate(hands):
                checks = self._strategy_checks[seat_idx][hand_idx] if seat_idx < len(self._strategy_checks) and hand_idx < len(self._strategy_checks[seat_idx]) else []

                if hand.is_blackjack and dealer_bj:
                    outcome = "push"
                    payout = 0
                elif hand.is_blackjack:
                    outcome = "blackjack"
                    payout = int(hand.bet * BLACKJACK_PAYOUT)
                elif dealer_bj:
                    outcome = "lose"
                    payout = -hand.bet
                elif hand.is_busted:
                    outcome = "bust"
                    payout = -hand.bet
                elif self._dealer_hand.is_busted:
                    outcome = "win"
                    payout = hand.bet
                elif hand.total > dealer_total:
                    outcome = "win"
                    payout = hand.bet
                elif hand.total < dealer_total:
                    outcome = "lose"
                    payout = -hand.bet
                else:
                    outcome = "push"
                    payout = 0

                if self.mode == "bankroll":
                    self.bankroll += payout

                hand_results.append(HandResult(
                    hand=hand,
                    outcome=outcome,
                    payout=payout,
                    strategy_checks=checks,
                ))
            seat_results.append(hand_results)

        self.hands_played += self.num_seats
        self._phase = RoundPhase.DONE
        return RoundResult(
            seat_results=seat_results,
            dealer_hand=self._dealer_hand,
            reshuffled=self._reshuffled_this_round,
        )

    def reset_for_next_round(self) -> None:
        self._bets = [0] * self.num_seats
        self._phase = RoundPhase.BETTING

    @property
    def strategy_accuracy(self) -> Optional[float]:
        if self.total_decisions == 0:
            return None
        return self.correct_decisions / self.total_decisions * 100

    @property
    def running_count(self) -> int:
        return self.counter.running_count

    @property
    def true_count(self) -> float:
        return self.counter.true_count

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _deal_to(self, hand: Hand) -> Card:
        card = self.shoe.deal_one()
        hand.add_card(card)
        self.counter.update(card)
        return card

    def _execute_split(self) -> None:
        seat = self._active_seat
        hand_idx = self._active_hand_idx
        hand = self._seats[seat][hand_idx]
        is_ace_split = hand.cards[0].rank == "A"

        # Create two new hands from the split
        card1, card2 = hand.cards[0], hand.cards[1]
        new_hand1 = Hand(bet=self._bets[seat])
        new_hand1.add_card(card1)
        new_hand1.from_split = True
        new_hand1.split_from_aces = is_ace_split

        new_hand2 = Hand(bet=self._bets[seat])
        new_hand2.add_card(card2)
        new_hand2.from_split = True
        new_hand2.split_from_aces = is_ace_split

        if self.mode == "bankroll":
            self.bankroll -= self._bets[seat]  # extra bet for the split hand

        # Deal one card to each new hand
        self._deal_to(new_hand1)
        self._deal_to(new_hand2)

        # Replace current hand with two new ones
        self._seats[seat].pop(hand_idx)
        self._seats[seat].insert(hand_idx, new_hand1)
        self._seats[seat].insert(hand_idx + 1, new_hand2)

        # Expand strategy checks list to match
        self._strategy_checks[seat].insert(hand_idx, [])
        self._strategy_checks[seat][hand_idx + 1] = []

        # If ace split, both hands are done (one card only)
        if is_ace_split:
            self._advance_hand()
        else:
            # Stay on new_hand1 (same index), reset to play it
            self._active_hand_idx = hand_idx

    def _advance_hand(self) -> None:
        """Move to the next hand that still needs to be played."""
        seat = self._active_seat
        hands = self._seats[seat]

        # Try next hand in this seat
        next_idx = self._active_hand_idx + 1
        while next_idx < len(hands):
            h = hands[next_idx]
            if not h.is_busted and not (h.split_from_aces and len(h.cards) >= 2):
                self._active_hand_idx = next_idx
                return
            next_idx += 1

        # Move to next seat
        next_seat = seat + 1
        while next_seat < self.num_seats:
            seat_hands = self._seats[next_seat]
            if seat_hands and not seat_hands[0].is_blackjack:
                self._active_seat = next_seat
                self._active_hand_idx = 0
                return
            next_seat += 1

        # All hands done — move to dealer
        self._phase = RoundPhase.DEALER_TURN

    def _advance_if_needed(self) -> None:
        """Skip to dealer if all player hands are already resolved (e.g. all blackjack)."""
        all_done = all(
            hand.is_blackjack or hand.is_busted
            for hands in self._seats
            for hand in hands
        )
        if all_done:
            self._phase = RoundPhase.DEALER_TURN
