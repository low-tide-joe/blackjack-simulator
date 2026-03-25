#!/usr/bin/env python3
"""
Blackjack Simulator — entry point.
"""
import sys

from blackjack.engine import Action, GameEngine, RoundPhase
from blackjack.terminal_ui import (
    display_count,
    display_help,
    display_round_results,
    display_session_summary,
    display_table,
    display_welcome,
    prompt_action,
    prompt_bet,
    prompt_mode,
    prompt_num_seats,
)


def play(engine: GameEngine, mode: str) -> None:
    while True:
        # --- Betting phase ---
        if mode == "bankroll":
            for seat in range(engine.num_seats):
                amount = prompt_bet(seat, engine.bankroll)
                engine.set_bet(seat, amount)

        # --- Deal ---
        engine.deal_round()
        display_table(engine, hide_dealer_hole=True)

        # Check if we jumped straight to dealer (all blackjacks)
        if engine.phase == RoundPhase.DEALER_TURN:
            pass  # fall through to dealer turn below
        else:
            # --- Player turns ---
            quit_requested = False
            while engine.phase == RoundPhase.PLAYER_TURN:
                hand = engine.active_hand
                action = prompt_action(hand, engine)

                if action == "quit":
                    quit_requested = True
                    break

                strategy_result = engine.player_action(action)
                if strategy_result:
                    print()
                    from blackjack.terminal_ui import display_strategy_feedback
                    display_strategy_feedback(strategy_result)
                    print()

                display_table(engine, hide_dealer_hole=True)

            if quit_requested:
                break

        # --- Dealer turn ---
        if engine.phase == RoundPhase.DEALER_TURN:
            engine.dealer_play()

        # --- Settlement ---
        result = engine.settle()
        display_table(engine, hide_dealer_hole=False)
        display_round_results(result, engine, mode)

        # --- Continue? ---
        if mode == "bankroll" and engine.bankroll <= 0:
            print("  You're out of chips! Game over.\n")
            break

        try:
            cont = input("  Play another hand? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if cont in ("n", "no", "q", "quit"):
            break

        engine.reset_for_next_round()


def main() -> None:
    display_welcome()

    try:
        mode = prompt_mode()
        print()
        num_seats = prompt_num_seats()
        print()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye!")
        sys.exit(0)

    engine = GameEngine(num_seats=num_seats, mode=mode, starting_bankroll=1000)

    display_help()

    try:
        play(engine, mode)
    except (EOFError, KeyboardInterrupt):
        print()

    if engine.total_decisions > 0:
        display_session_summary(engine, mode)
    else:
        print("\nThanks for playing!\n")


if __name__ == "__main__":
    main()
