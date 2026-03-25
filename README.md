# Blackjack Simulator

A terminal-based blackjack simulator written in Python. Play single or multi-hand blackjack, get instant basic strategy feedback on every decision, and practice Hi-Lo card counting with a hidden count you reveal on demand.

---

## Features

- **Single or multi-hand play** — 1 to 3 simultaneous hands
- **Practice or bankroll mode** — play for fun or track chips against a starting bankroll
- **Instant basic strategy checking** — after every action, see whether you played correctly and why
- **Running strategy accuracy** — tracks your decision accuracy across the entire session
- **Hidden Hi-Lo card counting** — the count is maintained silently; type `count` at any point to check your running and true count against the game's tally
- **Realistic shoe mechanics** — 6-deck shoe with ~75% penetration cut card; reshuffles are announced
- **Full split support** — split pairs up to 4 hands, double after split (DAS), aces split once with one card each
- **Color terminal output** — red/black suits, highlighted outcomes, accuracy progress bar

---

## Rules

| Rule | Value |
|------|-------|
| Decks | 6 |
| Dealer soft 17 | Stand (S17) |
| Blackjack payout | 3:2 |
| Double down | Any two cards |
| Double after split | Yes |
| Re-splits | Up to 4 hands |
| Split aces | Once only, one card each |
| Surrender | No |
| Insurance | No |
| Shoe penetration | ~75% |

---

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or standard pip

---

## Installation

```bash
git clone https://github.com/your-username/blackjack-simulator
cd blackjack-simulator
uv sync
```

Or with pip (no dependencies beyond the standard library — `pytest` only needed for tests):

```bash
pip install pytest
```

---

## Running the game

```bash
uv run python main.py
```

Or without uv:

```bash
python main.py
```

On startup you will be asked to choose a mode and how many hands to play per round.

---

## Modes

### Practice mode
No bankroll tracking. Focus entirely on learning correct strategy and card counting. Just play hand after hand with no financial pressure.

### Bankroll mode
Start with $1,000 in chips. Place a bet before each hand. Winnings and losses are tracked and displayed after each round. The session summary shows your final bankroll and net result.

---

## Player commands

During your turn, type one of the following:

| Command | Action |
|---------|--------|
| `h` | Hit — take another card |
| `s` | Stand — end your turn |
| `d` | Double down — double your bet, take exactly one more card |
| `p` | Split — split a pair into two separate hands |
| `count` | Reveal the current Hi-Lo running count and true count |
| `help` | Show available commands |
| `quit` | End the session and display summary |

Only valid commands for the current hand are shown in the prompt — for example, `d` and `p` disappear once you have more than two cards, and `p` only appears when you hold a pair.

---

## Basic strategy feedback

After **every** action, the game checks your decision against mathematically correct basic strategy for 6-deck S17 DAS and gives immediate feedback:

```
✓ Correct!  Double hard 11 vs dealer 6 — high EV double opportunity
```

```
✗ Strategy says: Stand  (you chose Hit)
    Stand hard 16 vs dealer 6 — let dealer bust
```

At the end of each round your running accuracy is shown:

```
Strategy accuracy: 87.5%  ████████░░  (7/8)
```

### How the strategy tables work

The correct action for every situation is stored in three lookup tables in `blackjack/strategy.py`:

- **Hard totals** — player hard 5–17 vs dealer 2–A
- **Soft totals** — player soft 13–20 (A+2 through A+9) vs dealer 2–A
- **Pairs** — each pair rank vs dealer 2–A

The tables follow the standard 6-deck, S17, DAS basic strategy chart. Key rules to know:

| Situation | Correct play |
|-----------|-------------|
| Hard 8 or less | Always hit |
| Hard 9 | Double vs dealer 3–6, otherwise hit |
| Hard 10 | Double vs dealer 2–9, otherwise hit |
| Hard 11 | Double vs dealer 2–10, hit vs ace |
| Hard 12 | Stand vs dealer 4–6, otherwise hit |
| Hard 13–16 | Stand vs dealer 2–6, otherwise hit |
| Hard 17+ | Always stand |
| Soft 17 (A+6) | Always hit |
| Soft 18 (A+7) | Double vs 3–6, stand vs 7–8, hit vs 9/10/A |
| Soft 19–20 | Always stand |
| Pair of aces | Always split |
| Pair of 8s | Always split |
| Pair of 10s | Never split — 20 is a great hand |
| Pair of 5s | Never split — double as hard 10 instead |

---

## Card counting (Hi-Lo)

The game silently maintains a Hi-Lo count from the moment the shoe is dealt. The point is for **you** to count in your head while playing, then type `count` to verify whether you're right.

### Hi-Lo card values

| Cards | Count value |
|-------|-------------|
| 2, 3, 4, 5, 6 | +1 (low cards favor the dealer — count goes up when they leave) |
| 7, 8, 9 | 0 (neutral) |
| 10, J, Q, K, A | −1 (high cards favor the player — count goes down when they leave) |

A positive count means more high cards remain in the shoe, which favors the player. A negative count favors the dealer.

### Running count vs true count

- **Running count** — the raw cumulative total since the last shuffle
- **True count** — running count ÷ decks remaining. This normalises for shoe depth and is the number that actually drives betting and strategy deviation decisions in real play

```
Count:  Running: +8   True: +2.1
```

The count resets automatically when the shoe reshuffles, which is announced mid-game.

---

## Multi-hand play

When playing 2 or 3 hands, each seat is played left to right. The active hand is marked with `>`. Each hand is bet and played independently. In bankroll mode, each hand requires its own bet before the round starts.

Example with 2 hands:

```
  Dealer: K♠  [??]  (showing K♠)

  > Hand 1  bet: $25: 7♥  9♣  [16]
    Hand 2  bet: $10: A♦  6♠  [17 (soft)]
```

---

## Project structure

```
blackjack-simulator/
├── main.py                  # Entry point, mode selection, game loop
├── blackjack/
│   ├── models.py            # Card, Hand, Shoe
│   ├── engine.py            # GameEngine — pure game logic, zero I/O
│   ├── strategy.py          # Basic strategy lookup tables + reason strings
│   ├── counting.py          # HiLoCounter (running count, true count)
│   └── terminal_ui.py       # All display and input logic
└── tests/
    ├── test_models.py       # Card values, hand totals, shoe mechanics
    ├── test_counting.py     # Hi-Lo weights, true count math
    ├── test_strategy.py     # Strategy table spot-checks
    └── test_engine.py       # Full round integration tests
```

### Architecture note

`engine.py` contains zero `print` or `input` calls — it only returns state objects. `terminal_ui.py` is the sole layer that touches the terminal. This separation means that a graphical frontend (e.g. a `rich`/`textual` TUI or a Pygame window) can be added later by writing a new display layer without modifying any game logic.

---

## Running tests

```bash
uv run pytest tests/ -v
```

The test suite (80 tests) covers:

- Card Hi-Lo values and suit colors
- Hand total calculation including multi-ace soft/hard transitions
- Blackjack detection, bust detection, split and double eligibility
- Shoe size, deal order, penetration and reshuffle trigger
- Every representative cell of the hard, soft, and pair strategy tables
- Hi-Lo running count and true count arithmetic
- Full round simulation: deal → player actions → dealer play → settlement
- Split mechanics: up to 4 hands, ace split one-card rule
- Strategy accuracy tracking across decisions
