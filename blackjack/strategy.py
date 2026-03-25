"""
Basic strategy tables for 6-deck, dealer stands on soft 17, double after split allowed.
Actions: H=Hit, S=Stand, D=Double (else hit), P=Split, DS=Double (else stand)

Dealer upcard columns: 2, 3, 4, 5, 6, 7, 8, 9, 10, A
"""
from blackjack.models import Hand

# Dealer upcard index (column order)
_DEALER_COLS = [2, 3, 4, 5, 6, 7, 8, 9, 10, 1]  # 1 = Ace

# ---------------------------------------------------------------------------
# Hard totals: player hard total (5-17+) vs dealer upcard
# Row: hard total, Columns: dealer 2-9, 10, A
# ---------------------------------------------------------------------------
_HARD = {
    #       2    3    4    5    6    7    8    9   10    A
    5:  [ "H", "H", "H", "H", "H", "H", "H", "H", "H", "H"],
    6:  [ "H", "H", "H", "H", "H", "H", "H", "H", "H", "H"],
    7:  [ "H", "H", "H", "H", "H", "H", "H", "H", "H", "H"],
    8:  [ "H", "H", "H", "H", "H", "H", "H", "H", "H", "H"],
    9:  [ "H", "D", "D", "D", "D", "H", "H", "H", "H", "H"],
    10: [ "D", "D", "D", "D", "D", "D", "D", "D", "H", "H"],
    11: [ "D", "D", "D", "D", "D", "D", "D", "D", "D", "H"],
    12: [ "H", "H", "S", "S", "S", "H", "H", "H", "H", "H"],
    13: [ "S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
    14: [ "S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
    15: [ "S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
    16: [ "S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
    17: [ "S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
}

# ---------------------------------------------------------------------------
# Soft totals: player soft total (A+2=13 through A+9=20) vs dealer upcard
# ---------------------------------------------------------------------------
_SOFT = {
    #       2    3    4    5    6    7    8    9   10    A
    13: [ "H", "H", "H", "D", "D", "H", "H", "H", "H", "H"],
    14: [ "H", "H", "H", "D", "D", "H", "H", "H", "H", "H"],
    15: [ "H", "H", "D", "D", "D", "H", "H", "H", "H", "H"],
    16: [ "H", "H", "D", "D", "D", "H", "H", "H", "H", "H"],
    17: [ "H", "D", "D", "D", "D", "H", "H", "H", "H", "H"],
    18: ["DS","DS", "D", "D", "D", "S", "S", "H", "H", "H"],
    19: [ "S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
    20: [ "S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
}

# ---------------------------------------------------------------------------
# Pairs: player pair rank vs dealer upcard
# ---------------------------------------------------------------------------
_PAIRS = {
    #        2    3    4    5    6    7    8    9   10    A
    "2":  [ "P", "P", "P", "P", "P", "P", "H", "H", "H", "H"],
    "3":  [ "P", "P", "P", "P", "P", "P", "H", "H", "H", "H"],
    "4":  [ "H", "H", "H", "P", "P", "H", "H", "H", "H", "H"],
    "5":  [ "D", "D", "D", "D", "D", "D", "D", "D", "H", "H"],
    "6":  [ "P", "P", "P", "P", "P", "H", "H", "H", "H", "H"],
    "7":  [ "P", "P", "P", "P", "P", "P", "H", "H", "H", "H"],
    "8":  [ "P", "P", "P", "P", "P", "P", "P", "P", "P", "P"],
    "9":  [ "P", "P", "P", "P", "P", "S", "P", "P", "S", "S"],
    "10": [ "S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
    "J":  [ "S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
    "Q":  [ "S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
    "K":  [ "S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
    "A":  [ "P", "P", "P", "P", "P", "P", "P", "P", "P", "P"],
}

_DEALER_COL_INDEX = {2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7, 10: 8, 1: 9}

_ACTION_REASONS = {
    "H":  "Hit",
    "S":  "Stand",
    "D":  "Double down",
    "DS": "Double down (stand if double not allowed)",
    "P":  "Split",
}

_DETAIL_REASONS = {
    # hard
    ("hard", 9,  "D"):  "Double hard 9 vs dealer {d} — good doubling spot",
    ("hard", 10, "D"):  "Double hard 10 vs dealer {d} — strong double",
    ("hard", 11, "D"):  "Double hard 11 vs dealer {d} — best double in the game",
    ("hard", 12, "S"):  "Stand hard 12 vs dealer {d} — let dealer bust",
    ("hard", 12, "H"):  "Hit hard 12 vs dealer {d} — dealer too strong to stand",
    ("hard", 13, "H"):  "Hit hard 13 vs dealer {d} — dealer won't bust enough",
    ("hard", 14, "H"):  "Hit hard 14 vs dealer {d} — dealer won't bust enough",
    ("hard", 15, "H"):  "Hit hard 15 vs dealer {d} — dealer too strong",
    ("hard", 16, "H"):  "Hit hard 16 vs dealer {d} — dealer too strong",
    # soft
    ("soft", 18, "DS"): "Double soft 18 vs dealer {d} — strong soft double",
    ("soft", 18, "H"):  "Hit soft 18 vs dealer {d} — dealer too strong to stand",
    ("soft", 17, "H"):  "Hit soft 17 — always hit, you can't bust",
    # pairs
    ("pair", "A",  "P"): "Always split aces",
    ("pair", "8",  "P"): "Always split 8s — 16 is the worst hand",
    ("pair", "10", "S"): "Never split 10s — 20 is a great hand",
    ("pair", "5",  "D"): "Never split 5s — double instead (treat as hard 10)",
    ("pair", "4",  "P"): "Split 4s vs dealer {d} — DAS rules make this correct",
    ("pair", "4",  "H"): "Don't split 4s vs dealer {d} — hit instead",
}


def _dealer_col(dealer_upcard_value: int) -> int:
    v = dealer_upcard_value
    # Ace comes in as value 11, map to 1
    if v == 11:
        v = 1
    return _DEALER_COL_INDEX[v]


def get_correct_action(hand: Hand, dealer_upcard_value: int) -> tuple[str, str]:
    """
    Returns (action, reason) where action is one of H/S/D/P/DS.
    dealer_upcard_value is the numeric value of the dealer's visible card (11 for Ace).
    """
    col = _dealer_col(dealer_upcard_value)
    dealer_display = "A" if dealer_upcard_value in (1, 11) else str(dealer_upcard_value)

    # Check pairs first (only if hand can actually split)
    if hand.can_split:
        rank = hand.cards[0].rank
        action = _PAIRS[rank][col]
        reason = _get_reason("pair", rank, action, dealer_display)
        return action, reason

    # Soft hand
    if hand.is_soft and hand.total in _SOFT:
        total = hand.total
        action = _SOFT[total][col]
        reason = _get_reason("soft", total, action, dealer_display)
        return action, reason

    # Hard hand (cap at 17 for lookup; 17+ always stand)
    total = min(hand.total, 17)
    total = max(total, 5)
    action = _HARD[total][col]
    reason = _get_reason("hard", hand.total, action, dealer_display)
    return action, reason


def _get_reason(category: str, key, action: str, dealer_display: str) -> str:
    template = _DETAIL_REASONS.get((category, key, action))
    if template:
        return template.format(d=dealer_display)
    base = _ACTION_REASONS.get(action, action)
    if category == "pair":
        return f"{base} {key}s vs dealer {dealer_display}"
    qualifier = "soft" if category == "soft" else "hard"
    return f"{base} {qualifier} {key} vs dealer {dealer_display}"


def action_label(action: str) -> str:
    return _ACTION_REASONS.get(action, action)
