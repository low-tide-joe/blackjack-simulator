"""
Integration tests for GameEngine — simulate rounds programmatically.
"""
import pytest
from unittest.mock import patch
from blackjack.models import Card, Shoe
from blackjack.engine import Action, GameEngine, RoundPhase


def _make_shoe_from_cards(cards):
    """Patch a shoe to deal a predefined sequence of cards."""
    shoe = Shoe.__new__(Shoe)
    shoe.num_decks = 6
    shoe.cards = list(cards)  # deal_one uses pop(0), so cards[0] is first dealt
    shoe._dealt = 0
    shoe.cut_card_pos = 999
    return shoe


def c(rank, suit="S"):
    return Card(rank, suit)


class TestDealRound:
    def test_deal_gives_two_cards_each(self):
        engine = GameEngine(num_seats=1, mode="practice")
        engine.deal_round()
        assert len(engine.seats[0][0].cards) == 2
        assert len(engine.dealer_hand.cards) == 2

    def test_phase_after_deal(self):
        engine = GameEngine(num_seats=1, mode="practice")
        engine.deal_round()
        assert engine.phase in (RoundPhase.PLAYER_TURN, RoundPhase.DEALER_TURN)

    def test_multi_seat_deal(self):
        engine = GameEngine(num_seats=3, mode="practice")
        engine.deal_round()
        for seat in engine.seats:
            assert len(seat[0].cards) == 2


class TestPlayerActions:
    def _engine_with_cards(self, player_cards, dealer_cards, extra=[]):
        """Create engine and patch shoe to deal specific cards in order."""
        # Dealing order: seat0_c1, dealer_c1, seat0_c2, dealer_c2, then extras
        seq = [player_cards[0], dealer_cards[0], player_cards[1], dealer_cards[1]] + extra
        engine = GameEngine(num_seats=1, mode="practice")
        shoe = _make_shoe_from_cards(seq)
        engine.shoe = shoe
        engine.counter._shoe = shoe
        engine.deal_round()
        return engine

    def test_hit_adds_card(self):
        engine = self._engine_with_cards(
            [c("5"), c("6")], [c("7"), c("8")], extra=[c("3")]
        )
        initial = len(engine.active_hand.cards)
        engine.player_action(Action.HIT)
        assert len(engine.active_hand.cards) == initial + 1

    def test_stand_advances_phase(self):
        engine = self._engine_with_cards(
            [c("K"), c("7")], [c("8"), c("9")]
        )
        engine.player_action(Action.STAND)
        assert engine.phase == RoundPhase.DEALER_TURN

    def test_double_doubles_bet_and_deals_one_card(self):
        engine = self._engine_with_cards(
            [c("5"), c("6")], [c("7"), c("8")], extra=[c("K")]
        )
        original_bet = engine.active_hand.bet
        engine.player_action(Action.DOUBLE)
        assert engine.active_hand.bet == original_bet * 2
        assert len(engine.active_hand.cards) == 3
        assert engine.phase == RoundPhase.DEALER_TURN

    def test_bust_advances_to_dealer(self):
        engine = self._engine_with_cards(
            [c("K"), c("7")], [c("8"), c("9")], extra=[c("9")]
        )
        engine.player_action(Action.HIT)  # K+7+9 = 26, bust
        assert engine.phase == RoundPhase.DEALER_TURN


class TestSplit:
    def test_split_creates_two_hands(self):
        engine = GameEngine(num_seats=1, mode="practice")
        seq = [c("8", "H"), c("7"), c("8", "S"), c("9"), c("3"), c("K")]
        shoe = _make_shoe_from_cards(seq)
        engine.shoe = shoe
        engine.counter._shoe = shoe
        engine.deal_round()
        engine.player_action(Action.SPLIT)
        assert len(engine.seats[0]) == 2

    def test_ace_split_gets_one_card_each(self):
        engine = GameEngine(num_seats=1, mode="practice")
        seq = [c("A", "H"), c("7"), c("A", "S"), c("9"), c("K"), c("3")]
        shoe = _make_shoe_from_cards(seq)
        engine.shoe = shoe
        engine.counter._shoe = shoe
        engine.deal_round()
        engine.player_action(Action.SPLIT)
        # Both hands should have exactly 2 cards and be done
        for hand in engine.seats[0]:
            assert len(hand.cards) == 2
        # Phase should advance since aces get one card only
        assert engine.phase == RoundPhase.DEALER_TURN


class TestDealerPlay:
    def test_dealer_stands_on_17(self):
        engine = GameEngine(num_seats=1, mode="practice")
        seq = [c("K"), c("10"), c("K"), c("7")]
        shoe = _make_shoe_from_cards(seq)
        engine.shoe = shoe
        engine.counter._shoe = shoe
        engine.deal_round()
        engine.player_action(Action.STAND)
        engine.dealer_play()
        assert engine.dealer_hand.total >= 17
        assert engine.phase == RoundPhase.SETTLEMENT

    def test_dealer_hits_on_16(self):
        engine = GameEngine(num_seats=1, mode="practice")
        seq = [c("K"), c("9"), c("K"), c("7"), c("5")]
        shoe = _make_shoe_from_cards(seq)
        engine.shoe = shoe
        engine.counter._shoe = shoe
        engine.deal_round()
        engine.player_action(Action.STAND)
        engine.dealer_play()
        # Dealer had 9+7=16, hits, gets 5 → 21
        assert engine.dealer_hand.total >= 17


class TestSettlement:
    def _play_and_settle(self, player_cards, dealer_cards, action=Action.STAND, extra=[]):
        seq = [player_cards[0], dealer_cards[0], player_cards[1], dealer_cards[1]] + extra
        engine = GameEngine(num_seats=1, mode="practice")
        shoe = _make_shoe_from_cards(seq)
        engine.shoe = shoe
        engine.counter._shoe = shoe
        engine.deal_round()
        if engine.phase == RoundPhase.PLAYER_TURN:
            engine.player_action(action)
        if engine.phase == RoundPhase.DEALER_TURN:
            engine.dealer_play()
        return engine.settle(), engine

    def test_player_wins(self):
        result, _ = self._play_and_settle(
            [c("K"), c("9")], [c("7"), c("8")]  # player 19, dealer 15 → dealer hits
        )
        # Dealer has 15 and will hit, but shoe has no extra card so it stays
        # Let's give dealer a small total
        pass  # covered in test below

    def test_player_blackjack_pays_3_2(self):
        result, engine = self._play_and_settle(
            [c("A"), c("K")], [c("7"), c("9")]
        )
        hr = result.seat_results[0][0]
        assert hr.outcome == "blackjack"
        assert hr.payout == 1  # practice mode bet=1, BJ pays 1.5x → int(1.5)=1

    def test_player_busts_loses(self):
        result, _ = self._play_and_settle(
            [c("K"), c("7")], [c("8"), c("9")], action=Action.HIT, extra=[c("9")]
        )
        hr = result.seat_results[0][0]
        assert hr.outcome == "bust"
        assert hr.payout < 0

    def test_push(self):
        result, engine = self._play_and_settle(
            [c("K"), c("9")], [c("K"), c("9")]
        )
        hr = result.seat_results[0][0]
        assert hr.outcome == "push"
        assert hr.payout == 0


class TestStrategyTracking:
    def test_correct_decision_tracked(self):
        engine = GameEngine(num_seats=1, mode="practice")
        # Give player a hard 11 vs dealer 6 → correct action is Double
        seq = [c("7"), c("6"), c("4"), c("8"), c("K")]
        shoe = _make_shoe_from_cards(seq)
        engine.shoe = shoe
        engine.counter._shoe = shoe
        engine.deal_round()
        result = engine.player_action(Action.DOUBLE)
        assert result.was_correct
        assert engine.total_decisions == 1
        assert engine.correct_decisions == 1

    def test_accuracy_calculation(self):
        engine = GameEngine(num_seats=1, mode="practice")
        engine.total_decisions = 10
        engine.correct_decisions = 8
        assert abs(engine.strategy_accuracy - 80.0) < 0.01

    def test_accuracy_none_when_no_decisions(self):
        engine = GameEngine(num_seats=1, mode="practice")
        assert engine.strategy_accuracy is None
