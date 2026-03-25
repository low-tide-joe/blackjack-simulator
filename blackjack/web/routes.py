from flask import Blueprint, jsonify, render_template, request

from blackjack.engine import Action, RoundPhase
from blackjack.web import session_store
from blackjack.web.serializers import (
    serialize_game_state,
    serialize_round_result,
    serialize_strategy_result,
)

bp = Blueprint("blackjack", __name__)


def _get_engine_or_404(game_id: str):
    engine = session_store.get_engine(game_id)
    if engine is None:
        return None, (jsonify({"error": "Game not found. Please start a new game."}), 404)
    return engine, None


@bp.get("/")
def index():
    return render_template("index.html")


@bp.post("/api/new-game")
def new_game():
    data = request.get_json(force=True)
    game_id = data.get("game_id")
    mode = data.get("mode", "practice")
    num_seats = int(data.get("num_seats", 1))

    if not game_id:
        return jsonify({"error": "game_id required"}), 400
    if mode not in ("practice", "bankroll"):
        return jsonify({"error": "mode must be practice or bankroll"}), 400
    if not 1 <= num_seats <= 3:
        return jsonify({"error": "num_seats must be 1-3"}), 400

    engine = session_store.create_engine(game_id, num_seats=num_seats, mode=mode)
    return jsonify({"state": serialize_game_state(engine)})


@bp.post("/api/bet")
def bet():
    data = request.get_json(force=True)
    game_id = data.get("game_id")
    bets = data.get("bets", [])

    engine, err = _get_engine_or_404(game_id)
    if err:
        return err

    if engine.phase != RoundPhase.BETTING:
        return jsonify({"error": "Not in betting phase"}), 400

    try:
        for i, amount in enumerate(bets):
            engine.set_bet(i, int(amount))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"state": serialize_game_state(engine)})


@bp.post("/api/deal")
def deal():
    data = request.get_json(force=True)
    game_id = data.get("game_id")

    engine, err = _get_engine_or_404(game_id)
    if err:
        return err

    if engine.phase != RoundPhase.BETTING:
        return jsonify({"error": "Not in betting phase"}), 400

    reshuffled = False
    if engine.shoe.needs_reshuffle:
        reshuffled = True

    engine.deal_round()
    state = serialize_game_state(engine)
    # If all blackjacks, phase jumped straight to DEALER_TURN — flag it
    state["reshuffled"] = reshuffled or engine._reshuffled_this_round
    return jsonify({"state": state})


@bp.post("/api/action")
def action():
    data = request.get_json(force=True)
    game_id = data.get("game_id")
    action_str = data.get("action", "").lower()

    engine, err = _get_engine_or_404(game_id)
    if err:
        return err

    if engine.phase != RoundPhase.PLAYER_TURN:
        return jsonify({"error": "Not in player turn phase"}), 400

    try:
        act = Action(action_str)
    except ValueError:
        return jsonify({"error": f"Invalid action: {action_str}"}), 400

    try:
        strategy_result = engine.player_action(act)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    response = {"state": serialize_game_state(engine)}
    if strategy_result is not None:
        response["strategy_feedback"] = serialize_strategy_result(strategy_result)

    return jsonify(response)


@bp.post("/api/finish-round")
def finish_round():
    """Run dealer play + settle in one call. Frontend animates dealer cards client-side."""
    data = request.get_json(force=True)
    game_id = data.get("game_id")

    engine, err = _get_engine_or_404(game_id)
    if err:
        return err

    if engine.phase != RoundPhase.DEALER_TURN:
        return jsonify({"error": "Not in dealer turn phase"}), 400

    dealer_cards_before = len(engine.dealer_hand.cards)
    engine.dealer_play()
    dealer_cards_after = len(engine.dealer_hand.cards)

    result = engine.settle()

    return jsonify({
        "state": serialize_game_state(engine),
        "result": serialize_round_result(result),
        "dealer_cards_drawn": dealer_cards_after - dealer_cards_before,
    })


@bp.post("/api/next-round")
def next_round():
    data = request.get_json(force=True)
    game_id = data.get("game_id")

    engine, err = _get_engine_or_404(game_id)
    if err:
        return err

    if engine.phase != RoundPhase.DONE:
        return jsonify({"error": "Round is not done yet"}), 400

    engine.reset_for_next_round()
    return jsonify({"state": serialize_game_state(engine)})


@bp.get("/api/count")
def count():
    game_id = request.args.get("game_id")

    engine, err = _get_engine_or_404(game_id)
    if err:
        return err

    return jsonify({
        "running_count": engine.running_count,
        "true_count": round(engine.true_count, 2),
        "decks_remaining": round(engine.shoe.decks_remaining, 1),
    })
