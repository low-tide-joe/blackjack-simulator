"""
JSON serializers: convert engine data classes into plain dicts for API responses.
"""
from typing import Optional

from blackjack.models import Card, Hand, SUITS
from blackjack.engine import GameEngine, HandResult, RoundResult, StrategyResult, RoundPhase


def serialize_card(card: Card, hidden: bool = False) -> dict:
    if hidden:
        return {"hidden": True}
    return {
        "rank": card.rank,
        "suit": card.suit,
        "symbol": SUITS[card.suit],
        "display": str(card),
        "is_red": card.is_red,
    }


def serialize_hand(hand: Hand, hide_hole: bool = False) -> dict:
    cards = []
    for i, card in enumerate(hand.cards):
        hide = hide_hole and i == 1
        cards.append(serialize_card(card, hidden=hide))

    result = {
        "cards": cards,
        "bet": hand.bet,
        "doubled": hand.doubled,
        "from_split": hand.from_split,
        "is_blackjack": hand.is_blackjack,
        "is_busted": hand.is_busted,
        "can_split": hand.can_split,
        "can_double": hand.can_double,
    }
    if not hide_hole:
        result["total"] = hand.total
        result["is_soft"] = hand.is_soft
    else:
        # Show partial total based on visible card only
        visible = hand.cards[0]
        result["visible_total"] = visible.value
        result["is_soft"] = False

    return result


def serialize_strategy_result(result: StrategyResult) -> dict:
    action_names = {"H": "Hit", "S": "Stand", "D": "Double", "P": "Split", "DS": "Double/Stand"}
    return {
        "player_action": result.player_action,
        "correct_action": result.correct_action,
        "player_action_name": action_names.get(result.player_action, result.player_action),
        "correct_action_name": action_names.get(result.correct_action, result.correct_action),
        "reason": result.reason,
        "was_correct": result.was_correct,
    }


def serialize_hand_result(hr: HandResult) -> dict:
    return {
        "hand": serialize_hand(hr.hand),
        "outcome": hr.outcome,
        "payout": hr.payout,
        "strategy_checks": [serialize_strategy_result(sc) for sc in hr.strategy_checks],
    }


def serialize_round_result(result: RoundResult) -> dict:
    return {
        "seat_results": [
            [serialize_hand_result(hr) for hr in seat]
            for seat in result.seat_results
        ],
        "dealer_hand": serialize_hand(result.dealer_hand),
        "reshuffled": result.reshuffled,
    }


def serialize_game_state(engine: GameEngine) -> dict:
    in_player_turn = engine.phase == RoundPhase.PLAYER_TURN

    dealer = None
    if engine.dealer_hand is not None:
        dealer = serialize_hand(engine.dealer_hand, hide_hole=in_player_turn)

    seats = [
        [serialize_hand(hand) for hand in seat_hands]
        for seat_hands in engine.seats
    ]

    accuracy = engine.strategy_accuracy

    return {
        "phase": engine.phase.name,
        "dealer": dealer,
        "seats": seats,
        "active_seat": engine.active_seat,
        "active_hand_idx": engine.active_hand_idx,
        "num_seats": engine.num_seats,
        "mode": engine.mode,
        "bankroll": engine.bankroll,
        "hands_played": engine.hands_played,
        "correct_decisions": engine.correct_decisions,
        "total_decisions": engine.total_decisions,
        "strategy_accuracy": round(accuracy, 1) if accuracy is not None else None,
    }
