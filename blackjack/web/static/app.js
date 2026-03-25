'use strict';

// ═══════════════════════════════════════════════════════════
// Game state
// ═══════════════════════════════════════════════════════════
const Game = {
  id: null,       // UUID, generated per page load
  mode: 'practice',
  numSeats: 1,
  state: null,    // last serialized game state from server
  lastResult: null,
};

// ═══════════════════════════════════════════════════════════
// API wrapper
// ═══════════════════════════════════════════════════════════
async function api(endpoint, body = null) {
  const opts = {
    method: body !== null ? 'POST' : 'GET',
    headers: { 'Content-Type': 'application/json' },
  };
  if (body !== null) opts.body = JSON.stringify(body);

  const res = await fetch(endpoint, opts);
  const data = await res.json();

  if (!res.ok) {
    showError(data.error || 'Server error');
    throw new Error(data.error || 'Server error');
  }
  return data;
}

function showError(msg) {
  // Simple inline error — could be expanded
  console.error('[API error]', msg);
  showToast(`⚠ ${msg}`, false, false);
}

// ═══════════════════════════════════════════════════════════
// Screen management
// ═══════════════════════════════════════════════════════════
function showScreen(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(`screen-${name}`).classList.add('active');
}

// ═══════════════════════════════════════════════════════════
// Card rendering
// ═══════════════════════════════════════════════════════════
function makeCard(cardData, animate = true) {
  if (cardData.hidden) {
    const back = document.createElement('div');
    back.className = 'card-back' + (animate ? ' card-deal' : '');
    back.innerHTML = '<div class="card-back-icon">🂠</div>';
    return back;
  }

  const card = document.createElement('div');
  card.className = `card ${cardData.is_red ? 'red' : 'black'}${animate ? ' card-deal' : ''}`;
  card.innerHTML = `
    <span class="card-rank">${cardData.rank}</span>
    <span class="card-suit">${cardData.symbol}</span>
  `;
  return card;
}

function makeCardFlipContainer(backEl) {
  const container = document.createElement('div');
  container.className = 'card-flip-container';
  const inner = document.createElement('div');
  inner.className = 'card-flip-inner';
  const backFace = document.createElement('div');
  backFace.className = 'card-face';
  backFace.appendChild(backEl);
  const frontFace = document.createElement('div');
  frontFace.className = 'card-back-face';
  // content filled in by flipHoleCard when revealed
  inner.appendChild(backFace);
  inner.appendChild(frontFace);
  container.appendChild(inner);
  return container;
}

function flipHoleCard(container, cardData) {
  // Replace back face content with the real card, then flip
  const frontFace = container.querySelector('.card-back-face');
  frontFace.innerHTML = '';
  frontFace.appendChild(makeCard(cardData, false));
  container.classList.add('flipped');
}

// ═══════════════════════════════════════════════════════════
// Table rendering
// ═══════════════════════════════════════════════════════════
function renderDealer(state, animate = true) {
  const row = document.getElementById('dealer-cards');
  row.innerHTML = '';

  if (!state.dealer) return;

  const dealer = state.dealer;
  dealer.cards.forEach((cardData, i) => {
    if (cardData.hidden) {
      // Create flip container so we can flip it later
      const backEl = document.createElement('div');
      backEl.className = 'card-back';
      backEl.innerHTML = '<div class="card-back-icon">🂠</div>';
      const flipContainer = makeCardFlipContainer(backEl);
      flipContainer.id = 'hole-card-flip';
      row.appendChild(flipContainer);
    } else {
      const el = makeCard(cardData, animate);
      if (animate) el.style.animationDelay = `${i * 80}ms`;
      row.appendChild(el);
    }
  });

  const totalEl = document.getElementById('dealer-total');
  if (state.phase === 'PLAYER_TURN') {
    const upcard = dealer.cards[0];
    totalEl.textContent = upcard ? `Showing ${upcard.rank}` : '';
  } else if (dealer.total !== undefined) {
    totalEl.textContent = dealer.is_soft ? `${dealer.total} (soft)` : `${dealer.total}`;
  } else {
    totalEl.textContent = '';
  }
}

function renderSeats(state, animate = true) {
  const area = document.getElementById('seats-area');
  area.innerHTML = '';

  state.seats.forEach((hands, seatIdx) => {
    const seat = document.createElement('div');
    seat.className = 'seat';

    if (state.num_seats > 1) {
      const label = document.createElement('div');
      label.className = 'seat-label';
      label.textContent = `Hand ${seatIdx + 1}`;
      seat.appendChild(label);
    }

    const handGroup = document.createElement('div');
    handGroup.className = 'hand-group';

    hands.forEach((hand, handIdx) => {
      const handEl = document.createElement('div');
      handEl.className = 'player-hand';

      const isActive = (
        state.phase === 'PLAYER_TURN' &&
        seatIdx === state.active_seat &&
        handIdx === state.active_hand_idx
      );
      if (isActive) handEl.classList.add('active');

      // Cards
      const cardsRow = document.createElement('div');
      cardsRow.className = 'cards-row';
      hand.cards.forEach((cardData, i) => {
        const el = makeCard(cardData, animate);
        if (animate) el.style.animationDelay = `${(seatIdx * 2 + handIdx + i) * 70}ms`;
        cardsRow.appendChild(el);
      });
      handEl.appendChild(cardsRow);

      // Total / status
      const info = document.createElement('div');
      info.className = 'hand-total';
      if (hand.is_blackjack) {
        info.innerHTML = '<span style="color:var(--gold-light);font-weight:700">BLACKJACK</span>';
      } else if (hand.is_busted) {
        info.innerHTML = '<span style="color:#ff6b6b;font-weight:700">BUST</span>';
      } else if (hand.total !== undefined) {
        info.textContent = hand.is_soft ? `${hand.total} (soft)` : `${hand.total}`;
      }
      handEl.appendChild(info);

      // Bet badge (bankroll mode)
      if (state.mode === 'bankroll' && hand.bet) {
        const badge = document.createElement('div');
        badge.className = 'bet-badge';
        badge.textContent = `$${hand.bet}${hand.doubled ? ' (doubled)' : ''}`;
        handEl.appendChild(badge);
      }

      if (hands.length > 1) {
        const splitLabel = document.createElement('div');
        splitLabel.className = 'seat-label';
        splitLabel.textContent = `Split ${handIdx + 1}`;
        handGroup.appendChild(splitLabel);
      }

      handGroup.appendChild(handEl);
    });

    seat.appendChild(handGroup);
    area.appendChild(seat);
  });
}

function renderStats(state) {
  const bankrollEl = document.getElementById('stat-bankroll');
  if (state.mode === 'bankroll' && state.bankroll !== null) {
    bankrollEl.style.display = '';
    bankrollEl.textContent = `Bankroll: $${state.bankroll}`;
  } else {
    bankrollEl.style.display = 'none';
  }

  const acc = state.strategy_accuracy;
  const accEl = document.getElementById('stat-accuracy');
  if (acc !== null && state.total_decisions > 0) {
    accEl.textContent = `Accuracy: ${acc}%`;
  } else {
    accEl.textContent = 'Accuracy: —';
  }

  document.getElementById('stat-mode').textContent =
    state.mode === 'bankroll' ? '💰 Bankroll' : '🎓 Practice';
}

function renderActionButtons(state) {
  const bar = document.getElementById('action-bar');
  const btns = document.getElementById('action-buttons');
  const roundOverBtns = document.getElementById('round-over-buttons');
  const roundSummary = document.getElementById('round-summary');

  if (state.phase === 'DONE') {
    bar.style.visibility = 'visible';
    btns.style.display = 'none';
    roundOverBtns.style.display = '';
    return;
  }

  roundOverBtns.style.display = 'none';
  roundSummary.style.display = 'none';
  btns.style.display = '';

  const inPlayerTurn = state.phase === 'PLAYER_TURN';
  bar.style.visibility = inPlayerTurn ? 'visible' : 'hidden';

  if (!inPlayerTurn) return;

  // Find active hand
  const hand = state.seats?.[state.active_seat]?.[state.active_hand_idx];
  if (!hand) return;

  document.getElementById('btn-hit').disabled = false;
  document.getElementById('btn-stand').disabled = false;
  document.getElementById('btn-double').disabled = !hand.can_double;
  document.getElementById('btn-split').disabled = !hand.can_split;

  // Count how many hands this seat has (for re-split limit check, server enforces)
  const seatHandCount = state.seats[state.active_seat].length;
  if (seatHandCount >= 4) {
    document.getElementById('btn-split').disabled = true;
  }
}

function renderTable(state, animate = true) {
  Game.state = state;
  renderDealer(state, animate);
  renderSeats(state, animate);
  renderStats(state);
  renderActionButtons(state);
}

// ═══════════════════════════════════════════════════════════
// Strategy toast
// ═══════════════════════════════════════════════════════════
let toastTimer = null;

function showToast(mainText, isCorrect, autoHide = true) {
  const toast = document.getElementById('strategy-toast');
  toast.innerHTML = mainText;
  toast.classList.add('visible');

  if (toastTimer) clearTimeout(toastTimer);
  if (autoHide) {
    toastTimer = setTimeout(() => toast.classList.remove('visible'), 3000);
  }
}

function showStrategyToast(feedback) {
  if (!feedback) return;
  if (feedback.was_correct) {
    showToast(
      `<div class="toast-correct">✓ Correct — ${feedback.player_action_name}</div>` +
      `<div class="toast-reason">${feedback.reason}</div>`,
      true
    );
  } else {
    showToast(
      `<div class="toast-wrong">✗ Strategy says: <strong>${feedback.correct_action_name}</strong> (you chose ${feedback.player_action_name})</div>` +
      `<div class="toast-reason">${feedback.reason}</div>`,
      false
    );
  }
}

// ═══════════════════════════════════════════════════════════
// Inline round results
// ═══════════════════════════════════════════════════════════
function showRoundResults(state, result) {
  // Append outcome badges to each rendered player-hand
  const seatEls = document.querySelectorAll('#seats-area .seat');
  result.seat_results.forEach((hands, seatIdx) => {
    const handEls = seatEls[seatIdx]?.querySelectorAll('.player-hand') || [];
    hands.forEach((hr, handIdx) => {
      const handEl = handEls[handIdx];
      if (!handEl) return;

      const badge = document.createElement('div');
      badge.className = `outcome-badge outcome-${hr.outcome}`;
      badge.textContent = hr.outcome.toUpperCase();
      handEl.appendChild(badge);

      if (state.mode === 'bankroll') {
        const payoutEl = document.createElement('div');
        payoutEl.className = `result-payout ${hr.payout > 0 ? 'positive' : hr.payout < 0 ? 'negative' : 'zero'}`;
        payoutEl.textContent = hr.payout >= 0 ? `+$${hr.payout}` : `-$${Math.abs(hr.payout)}`;
        handEl.appendChild(payoutEl);
      }
    });
  });

  // Round summary line
  const summaryEl = document.getElementById('round-summary');
  const parts = [];
  const acc = state.strategy_accuracy;
  if (acc !== null && state.total_decisions > 0) {
    parts.push(`Accuracy: ${acc}% (${state.correct_decisions}/${state.total_decisions})`);
  }
  if (state.mode === 'bankroll' && state.bankroll !== null) {
    parts.push(`Bankroll: $${state.bankroll}`);
  }
  if (parts.length > 0) {
    summaryEl.textContent = parts.join('  ·  ');
    summaryEl.style.display = '';
  }
}

// ═══════════════════════════════════════════════════════════
// Dealer animation then finish
// ═══════════════════════════════════════════════════════════
async function runDealerAndFinish() {
  renderActionButtons({ phase: 'DEALER_TURN' });

  let data;
  try {
    data = await api('/api/finish-round', { game_id: Game.id });
  } catch (e) {
    console.error('finish-round failed:', e);
    return;
  }

  // Flip hole card if it's still in the DOM (only present when dealer was hidden during player turn)
  try {
    const flipContainer = document.getElementById('hole-card-flip');
    if (flipContainer) {
      const realCard = data.result.dealer_hand.cards[1];
      if (realCard) flipHoleCard(flipContainer, realCard);
      await sleep(400);
    }
  } catch (e) {
    console.warn('hole card flip error (non-fatal):', e);
  }

  // Animate any extra dealer cards one by one
  try {
    const drawn = data.dealer_cards_drawn || 0;
    if (drawn > 0 && data.result.dealer_hand.cards.length > 2) {
      const row = document.getElementById('dealer-cards');
      const allDealerCards = data.result.dealer_hand.cards;
      const existingCount = allDealerCards.length - drawn;
      for (let i = existingCount; i < allDealerCards.length; i++) {
        await sleep(420);
        const el = makeCard(allDealerCards[i], true);
        row.appendChild(el);
        const isLast = allDealerCards[i + 1] === undefined;
        document.getElementById('dealer-total').textContent = isLast
          ? `${data.result.dealer_hand.total}${data.result.dealer_hand.is_soft ? ' (soft)' : ''}${data.result.dealer_hand.is_busted ? ' — BUST' : ''}`
          : '...';
      }
    }
  } catch (e) {
    console.warn('dealer animation error (non-fatal):', e);
  }

  await sleep(400);
  renderTable(data.state, false);
  showRoundResults(data.state, data.result);
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ═══════════════════════════════════════════════════════════
// Flow controllers
// ═══════════════════════════════════════════════════════════
async function startGame() {
  Game.id = crypto.randomUUID();
  Game.mode = document.querySelector('#mode-toggle .toggle-btn.active').dataset.value;
  Game.numSeats = parseInt(document.querySelector('#seats-toggle .toggle-btn.active').dataset.value);

  const data = await api('/api/new-game', {
    game_id: Game.id,
    mode: Game.mode,
    num_seats: Game.numSeats,
  });

  Game.state = data.state;

  if (Game.mode === 'bankroll') {
    setupBettingScreen(data.state);
    showScreen('betting');
  } else {
    // Practice mode — skip betting, go straight to deal
    await dealRound();
  }
}

function setupBettingScreen(state) {
  document.getElementById('bankroll-display').textContent =
    `Bankroll: $${state.bankroll}`;

  const grid = document.getElementById('bet-inputs');
  grid.innerHTML = '';
  for (let i = 0; i < Game.numSeats; i++) {
    const row = document.createElement('div');
    row.className = 'bet-row';
    row.innerHTML = `
      <label>Seat ${i + 1}</label>
      <input class="bet-input" type="number" id="bet-seat-${i}" value="25" min="1" max="${state.bankroll}" placeholder="Bet">
    `;
    grid.appendChild(row);
  }
}

async function placeBetsAndDeal() {
  const bets = [];
  for (let i = 0; i < Game.numSeats; i++) {
    bets.push(parseInt(document.getElementById(`bet-seat-${i}`).value) || 1);
  }
  await api('/api/bet', { game_id: Game.id, bets });
  await dealRound();
}

async function dealRound() {
  // Reset toast
  document.getElementById('strategy-toast').classList.remove('visible');
  document.getElementById('banner-reshuffle').style.display = 'none';

  showScreen('table');

  const data = await api('/api/deal', { game_id: Game.id });
  renderTable(data.state, true);

  if (data.state.reshuffled) {
    const banner = document.getElementById('banner-reshuffle');
    banner.style.display = '';
    setTimeout(() => banner.style.display = 'none', 3500);
  }

  // If no player turn (all blackjacks or immediate dealer turn), run dealer immediately
  if (data.state.phase === 'DEALER_TURN') {
    await sleep(800);
    await runDealerAndFinish();
  }
}

async function takeAction(action) {
  // Disable buttons while waiting to prevent double-clicks
  document.querySelectorAll('.action-btn').forEach(b => b.disabled = true);

  let data;
  try {
    data = await api('/api/action', { game_id: Game.id, action });
  } catch (e) {
    // Re-enable buttons so the player can try again
    renderActionButtons(Game.state);
    return;
  }

  renderTable(data.state, false);

  if (data.strategy_feedback) {
    showStrategyToast(data.strategy_feedback);
  }

  if (data.state.phase === 'DEALER_TURN') {
    await sleep(600);
    await runDealerAndFinish();
  }
}

async function nextHand() {
  document.getElementById('strategy-toast').classList.remove('visible');
  let data;
  try {
    data = await api('/api/next-round', { game_id: Game.id });
  } catch (e) {
    return;
  }
  Game.state = data.state;

  if (Game.mode === 'bankroll') {
    setupBettingScreen(data.state);
    showScreen('betting');
  } else {
    await dealRound();
  }
}

// ═══════════════════════════════════════════════════════════
// Count reveal
// ═══════════════════════════════════════════════════════════
async function revealCount() {
  const popover = document.getElementById('count-popover');
  if (popover.style.display !== 'none') {
    popover.style.display = 'none';
    return;
  }

  const data = await api(`/api/count?game_id=${Game.id}`);
  const rc = data.running_count;
  const tc = data.true_count;

  const rcEl = document.getElementById('count-running');
  const tcEl = document.getElementById('count-true');
  const decksEl = document.getElementById('count-decks');

  rcEl.textContent = rc >= 0 ? `+${rc}` : `${rc}`;
  rcEl.className = `count-value ${rc > 0 ? 'positive' : rc < 0 ? 'negative' : ''}`;

  tcEl.textContent = tc >= 0 ? `+${tc.toFixed(1)}` : `${tc.toFixed(1)}`;
  tcEl.className = `count-value ${tc > 0 ? 'positive' : tc < 0 ? 'negative' : ''}`;

  decksEl.textContent = data.decks_remaining.toFixed(1);
  decksEl.className = 'count-value';

  popover.style.display = '';
}

// ═══════════════════════════════════════════════════════════
// Event listeners
// ═══════════════════════════════════════════════════════════
function initToggleGroups() {
  document.querySelectorAll('.toggle-group').forEach(group => {
    group.querySelectorAll('.toggle-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        group.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initToggleGroups();

  document.getElementById('btn-start').addEventListener('click', startGame);
  document.getElementById('btn-deal').addEventListener('click', placeBetsAndDeal);

  document.querySelectorAll('.action-btn').forEach(btn => {
    btn.addEventListener('click', () => takeAction(btn.dataset.action));
  });

  document.getElementById('btn-count').addEventListener('click', revealCount);
  document.getElementById('count-close').addEventListener('click', () => {
    document.getElementById('count-popover').style.display = 'none';
  });

  document.getElementById('btn-next-hand').addEventListener('click', nextHand);
  document.getElementById('btn-new-game').addEventListener('click', () => showScreen('setup'));

  // Keyboard shortcuts on table screen
  document.addEventListener('keydown', e => {
    const state = Game.state;
    if (!state || state.phase !== 'PLAYER_TURN') return;
    if (document.getElementById('screen-table').classList.contains('active')) {
      const hand = state.seats?.[state.active_seat]?.[state.active_hand_idx];
      switch (e.key.toLowerCase()) {
        case 'h': takeAction('h'); break;
        case 's': takeAction('s'); break;
        case 'd': if (hand?.can_double) takeAction('d'); break;
        case 'p': if (hand?.can_split) takeAction('p'); break;
        case 'c': revealCount(); break;
      }
    }
  });
});
