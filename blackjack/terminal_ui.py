"""
Terminal UI layer — all print/input lives here.
Depends on GameEngine for state; contains zero game logic.
"""
import sys
from typing import List, Optional

from blackjack.models import Card, Hand, RED_SUITS
from blackjack.engine import (
    Action, GameEngine, HandResult, RoundPhase, RoundResult, StrategyResult
)

# ANSI color codes
_RED   = "\033[91m"
_WHITE = "\033[97m"
_GREEN = "\033[92m"
_YELLOW= "\033[93m"
_CYAN  = "\033[96m"
_BOLD  = "\033[1m"
_DIM   = "\033[2m"
_RESET = "\033[0m"

_HIDDEN_CARD = "[??]"


def _color_card(card: Card) -> str:
    color = _RED if card.is_red else _WHITE
    return f"{color}{card}{_RESET}"


def _render_hand(hand: Hand, hide_hole: bool = False) -> str:
    parts = []
    for i, card in enumerate(hand.cards):
        if hide_hole and i == 1:
            parts.append(_HIDDEN_CARD)
        else:
            parts.append(_color_card(card))
    cards_str = "  ".join(parts)
    if hide_hole:
        return cards_str
    total = hand.total
    soft_str = " (soft)" if hand.is_soft else ""
    return f"{cards_str}  [{total}{soft_str}]"


def _print_separator(char: str = "─", width: int = 60) -> None:
    print(_DIM + char * width + _RESET)


def display_table(engine: GameEngine, hide_dealer_hole: bool = True) -> None:
    """Print current table state."""
    print()
    _print_separator()

    # Dealer
    dealer_str = _render_hand(engine.dealer_hand, hide_hole=hide_dealer_hole)
    if hide_dealer_hole:
        upcard = engine.dealer_hand.cards[0]
        print(f"  {_BOLD}Dealer:{_RESET} {dealer_str}  (showing {_color_card(upcard)})")
    else:
        print(f"  {_BOLD}Dealer:{_RESET} {dealer_str}")

    print()

    # Player seats
    for seat_idx, hands in enumerate(engine.seats):
        seat_label = f"Hand {seat_idx + 1}" if engine.num_seats > 1 else "Your hand"
        for hand_idx, hand in enumerate(hands):
            active = (
                engine.phase == RoundPhase.PLAYER_TURN
                and seat_idx == engine.active_seat
                and hand_idx == engine.active_hand_idx
            )
            prefix = f"  {_CYAN}>{_RESET} " if active else "    "
            split_label = f" (split {hand_idx + 1})" if len(hands) > 1 else ""
            bet_label = f"  bet: ${hand.bet}" if hand.bet else ""
            hand_str = _render_hand(hand)
            bj_tag = f"  {_GREEN}{_BOLD}BLACKJACK!{_RESET}" if hand.is_blackjack else ""
            bust_tag = f"  {_RED}{_BOLD}BUST{_RESET}" if hand.is_busted else ""
            print(f"{prefix}{_BOLD}{seat_label}{split_label}{_RESET}{bet_label}: {hand_str}{bj_tag}{bust_tag}")

    _print_separator()
    print()


def display_strategy_feedback(result: StrategyResult) -> None:
    if result.was_correct:
        print(f"  {_GREEN}✓ Correct!{_RESET} {_DIM}{result.reason}{_RESET}")
    else:
        action_names = {"H": "Hit", "S": "Stand", "D": "Double", "P": "Split", "DS": "Double/Stand"}
        correct = action_names.get(result.correct_action, result.correct_action)
        player = action_names.get(result.player_action, result.player_action)
        print(f"  {_RED}✗ Strategy says: {_BOLD}{correct}{_RESET}{_RED} (you chose {player}){_RESET}")
        print(f"    {_DIM}{result.reason}{_RESET}")


def display_round_results(result: RoundResult, engine: GameEngine, mode: str) -> None:
    print()
    _print_separator("═")
    print(f"  {_BOLD}--- Round Over ---{_RESET}")
    print()

    dealer = result.dealer_hand
    dealer_str = _render_hand(dealer)
    bj_tag = f"  {_YELLOW}{_BOLD}BLACKJACK!{_RESET}" if dealer.is_blackjack else ""
    bust_tag = f"  {_RED}{_BOLD}BUST{_RESET}" if dealer.is_busted else ""
    print(f"  {_BOLD}Dealer:{_RESET} {dealer_str}{bj_tag}{bust_tag}")
    print()

    for seat_idx, hand_results in enumerate(result.seat_results):
        seat_label = f"Hand {seat_idx + 1}" if engine.num_seats > 1 else "Your hand"
        for hand_idx, hr in enumerate(hand_results):
            split_label = f" (split {hand_idx + 1})" if len(hand_results) > 1 else ""
            outcome_str, outcome_color = _outcome_display(hr.outcome)
            payout_str = ""
            if mode == "bankroll":
                sign = "+" if hr.payout >= 0 else ""
                payout_str = f"  {outcome_color}{sign}${hr.payout}{_RESET}"
            print(f"  {_BOLD}{seat_label}{split_label}:{_RESET} {outcome_color}{_BOLD}{outcome_str}{_RESET}{payout_str}")

    print()
    # Strategy accuracy
    acc = engine.strategy_accuracy
    if acc is not None:
        bar = _accuracy_bar(acc)
        print(f"  Strategy accuracy: {_BOLD}{acc:.1f}%{_RESET}  {bar}  ({engine.correct_decisions}/{engine.total_decisions})")

    # Bankroll
    if mode == "bankroll":
        print(f"  Bankroll: {_BOLD}${engine.bankroll}{_RESET}")

    if result.reshuffled:
        print(f"\n  {_YELLOW}--- Shoe reshuffled, count reset ---{_RESET}")

    _print_separator("═")
    print()


def _outcome_display(outcome: str):
    mapping = {
        "win":       ("WIN",       _GREEN),
        "blackjack": ("BLACKJACK", _YELLOW),
        "lose":      ("LOSE",      _RED),
        "bust":      ("BUST",      _RED),
        "push":      ("PUSH",      _WHITE),
    }
    return mapping.get(outcome, (outcome.upper(), _WHITE))


def _accuracy_bar(pct: float, width: int = 10) -> str:
    filled = int(pct / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    color = _GREEN if pct >= 90 else (_YELLOW if pct >= 70 else _RED)
    return f"{color}{bar}{_RESET}"


def display_count(engine: GameEngine) -> None:
    rc = engine.running_count
    tc = engine.true_count
    sign = "+" if rc > 0 else ""
    tc_sign = "+" if tc > 0 else ""
    print(f"\n  {_CYAN}{_BOLD}Count:{_RESET}  Running: {_BOLD}{sign}{rc}{_RESET}   True: {_BOLD}{tc_sign}{tc:.1f}{_RESET}\n")


def display_help() -> None:
    print(f"""
  {_BOLD}Commands:{_RESET}
    {_CYAN}h{_RESET} — Hit
    {_CYAN}s{_RESET} — Stand
    {_CYAN}d{_RESET} — Double down
    {_CYAN}p{_RESET} — Split
    {_CYAN}count{_RESET} — Reveal current Hi-Lo count
    {_CYAN}help{_RESET}  — Show this message
    {_CYAN}quit{_RESET}  — End session
""")


def display_welcome() -> None:
    print(f"""
{_BOLD}{'═' * 60}
  BLACKJACK SIMULATOR
  6-deck | S17 | DAS | 3:2 BJ
{'═' * 60}{_RESET}
""")


def display_session_summary(engine: GameEngine, mode: str) -> None:
    print(f"""
{_BOLD}{'═' * 60}
  SESSION SUMMARY
{'═' * 60}{_RESET}
  Hands played:  {engine.hands_played}
  Strategy accuracy: {engine.strategy_accuracy:.1f}% ({engine.correct_decisions}/{engine.total_decisions})""")
    if mode == "bankroll":
        print(f"  Final bankroll: ${engine.bankroll}")
    print(f"{_BOLD}{'═' * 60}{_RESET}\n")


def prompt_mode() -> str:
    print(f"  {_BOLD}Mode:{_RESET}")
    print(f"    {_CYAN}1{_RESET} — Practice (no bankroll)")
    print(f"    {_CYAN}2{_RESET} — Bankroll (start with $1000)")
    while True:
        choice = input("  Choose [1/2]: ").strip()
        if choice == "1":
            return "practice"
        if choice == "2":
            return "bankroll"
        print("  Please enter 1 or 2.")


def prompt_num_seats() -> int:
    print(f"\n  {_BOLD}How many hands?{_RESET} [1-3]")
    while True:
        choice = input("  Enter 1, 2, or 3: ").strip()
        if choice in ("1", "2", "3"):
            return int(choice)
        print("  Please enter 1, 2, or 3.")


def prompt_bet(seat: int, bankroll: int) -> int:
    while True:
        raw = input(f"  Seat {seat + 1} bet (bankroll: ${bankroll}): $").strip()
        try:
            amount = int(raw)
            if amount <= 0:
                print("  Bet must be positive.")
            elif amount > bankroll:
                print(f"  Not enough chips (have ${bankroll}).")
            else:
                return amount
        except ValueError:
            print("  Enter a whole number.")


def prompt_action(hand: Hand, engine: GameEngine) -> Optional[Action]:
    """
    Prompt for player action. Returns Action or None if a meta-command was entered.
    Meta-commands (count/quit/help) are handled here and return None.
    """
    options = ["h", "s"]
    hint_parts = ["(h)it", "(s)tand"]
    if hand.can_double:
        options.append("d")
        hint_parts.append("(d)ouble")
    if hand.can_split and len(engine.seats[engine.active_seat]) < 4:
        options.append("p")
        hint_parts.append("(p)plit")
    hint_parts.extend(["count", "quit"])

    hint = "  " + "  ".join(hint_parts) + ": "

    while True:
        raw = input(hint).strip().lower()
        if raw == "quit":
            return "quit"
        if raw == "count":
            display_count(engine)
            continue
        if raw == "help":
            display_help()
            continue
        if raw in options:
            return Action(raw)
        print(f"  Invalid input. Options: {', '.join(options + ['count', 'quit', 'help'])}")
