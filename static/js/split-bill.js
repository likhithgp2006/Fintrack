/* Split Bill Calculator Logic */

document.addEventListener('DOMContentLoaded', () => {
  initSplitBill();
});

let currentTipPct = 0;
let isCustomMode = false;
let participants = [
  { name: 'You (Me)', shareRatio: 1 },
  { name: 'Friend 1', shareRatio: 1 },
  { name: 'Friend 2', shareRatio: 1 },
  { name: 'Friend 3', shareRatio: 1 }
];

function initSplitBill() {
  const billAmountInput = document.getElementById('billAmount');
  const taxInput = document.getElementById('taxPercent');
  const roundSelect = document.getElementById('roundOption');
  const peopleInput = document.getElementById('peopleCount');
  const decBtn = document.getElementById('decrementPeopleBtn');
  const incBtn = document.getElementById('incrementPeopleBtn');
  const modeEqualBtn = document.getElementById('modeEqualBtn');
  const modeCustomBtn = document.getElementById('modeCustomBtn');
  const copyBtn = document.getElementById('copySummaryBtn');
  const recordBtn = document.getElementById('recordMyShareBtn');

  // Update currency symbol
  const symEl = document.getElementById('billCurrencySymbol');
  if (symEl) symEl.textContent = getCurrencySymbol();

  // Tip Buttons
  document.querySelectorAll('.tip-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tip-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const tipVal = btn.dataset.tip;
      const customGroup = document.getElementById('customTipGroup');

      if (tipVal === 'custom') {
        customGroup.style.display = 'block';
        currentTipPct = parseFloat(document.getElementById('customTipInput').value) || 0;
      } else {
        customGroup.style.display = 'none';
        currentTipPct = parseFloat(tipVal) || 0;
      }
      calculateSplit();
    });
  });

  const customTipInput = document.getElementById('customTipInput');
  if (customTipInput) {
    customTipInput.addEventListener('input', () => {
      currentTipPct = parseFloat(customTipInput.value) || 0;
      calculateSplit();
    });
  }

  // People +/-
  if (decBtn && peopleInput) {
    decBtn.addEventListener('click', () => {
      let val = parseInt(peopleInput.value) || 1;
      if (val > 1) {
        peopleInput.value = val - 1;
        syncParticipantsCount(val - 1);
        calculateSplit();
      }
    });
  }

  if (incBtn && peopleInput) {
    incBtn.addEventListener('click', () => {
      let val = parseInt(peopleInput.value) || 1;
      if (val < 50) {
        peopleInput.value = val + 1;
        syncParticipantsCount(val + 1);
        calculateSplit();
      }
    });
  }

  if (peopleInput) {
    peopleInput.addEventListener('input', () => {
      let val = parseInt(peopleInput.value) || 1;
      if (val < 1) val = 1;
      syncParticipantsCount(val);
      calculateSplit();
    });
  }

  // Split Mode toggle
  if (modeEqualBtn && modeCustomBtn) {
    modeEqualBtn.addEventListener('click', () => {
      isCustomMode = false;
      modeEqualBtn.classList.add('active');
      modeCustomBtn.classList.remove('active');
      document.getElementById('customFriendsList').style.display = 'none';
      calculateSplit();
    });

    modeCustomBtn.addEventListener('click', () => {
      isCustomMode = true;
      modeCustomBtn.classList.add('active');
      modeEqualBtn.classList.remove('active');
      document.getElementById('customFriendsList').style.display = 'block';
      renderFriendsInputs();
      calculateSplit();
    });
  }

  // Inputs change
  [billAmountInput, taxInput, roundSelect].forEach(input => {
    if (input) input.addEventListener('input', calculateSplit);
  });

  // Action: Copy Summary
  if (copyBtn) copyBtn.addEventListener('click', copySplitSummary);

  // Action: Record My Share as Expense
  if (recordBtn) recordBtn.addEventListener('click', recordMyShareExpense);

  syncParticipantsCount(parseInt(peopleInput?.value) || 4);
  calculateSplit();
}

function syncParticipantsCount(count) {
  while (participants.length < count) {
    participants.push({ name: `Friend ${participants.length}`, shareRatio: 1 });
  }
  while (participants.length > count) {
    participants.pop();
  }
  if (isCustomMode) {
    renderFriendsInputs();
  }
}

function renderFriendsInputs() {
  const container = document.getElementById('friendsInputsContainer');
  if (!container) return;

  container.innerHTML = participants.map((p, idx) => `
    <div style="display: flex; gap: 0.5rem; align-items: center;">
      <input type="text" class="form-control form-control-sm friend-name-input" data-idx="${idx}" value="${escapeHtml(p.name)}" placeholder="Participant name" style="flex: 2;">
      <div style="display: flex; align-items: center; gap: 0.35rem; flex: 1;">
        <span class="text-muted" style="font-size: 0.8rem;">Weight:</span>
        <input type="number" step="0.5" min="0.5" max="10" class="form-control form-control-sm friend-weight-input" data-idx="${idx}" value="${p.shareRatio || 1}" style="width: 65px;">
      </div>
    </div>
  `).join('');

  container.querySelectorAll('.friend-name-input').forEach(input => {
    input.addEventListener('input', (e) => {
      const idx = parseInt(e.target.dataset.idx);
      participants[idx].name = e.target.value || `Person ${idx + 1}`;
      calculateSplit();
    });
  });

  container.querySelectorAll('.friend-weight-input').forEach(input => {
    input.addEventListener('input', (e) => {
      const idx = parseInt(e.target.dataset.idx);
      participants[idx].shareRatio = parseFloat(e.target.value) || 1;
      calculateSplit();
    });
  });
}

let lastCalculated = null;

function calculateSplit() {
  const billAmount = parseFloat(document.getElementById('billAmount')?.value) || 0;
  const taxPct = parseFloat(document.getElementById('taxPercent')?.value) || 0;
  const roundOption = document.getElementById('roundOption')?.value || 'none';
  const peopleCount = Math.max(1, parseInt(document.getElementById('peopleCount')?.value) || 1);

  const tipAmount = billAmount * (currentTipPct / 100);
  const taxAmount = billAmount * (taxPct / 100);
  const totalPayable = billAmount + tipAmount + taxAmount;

  // Calculate per person
  let perPersonBase = totalPayable / peopleCount;
  let finalPerPerson = perPersonBase;

  // Rounding logic
  if (roundOption === '5') {
    finalPerPerson = Math.ceil(perPersonBase / 5) * 5;
  } else if (roundOption === '10') {
    finalPerPerson = Math.ceil(perPersonBase / 10) * 10;
  } else if (roundOption === '1') {
    finalPerPerson = Math.ceil(perPersonBase);
  }

  // Update DOM Summary
  document.getElementById('breakdownBaseBill').textContent = formatCurrency(billAmount);
  document.getElementById('breakdownTipPct').textContent = `${currentTipPct}%`;
  document.getElementById('breakdownTipAmount').textContent = formatCurrency(tipAmount);
  document.getElementById('breakdownTaxPct').textContent = `${taxPct}%`;
  document.getElementById('breakdownTaxAmount').textContent = formatCurrency(taxAmount);
  document.getElementById('breakdownTotalBill').textContent = formatCurrency(totalPayable);

  const heroAmountEl = document.getElementById('summaryPerPerson');
  const heroSubEl = document.getElementById('summaryHeroSubtitle');

  heroAmountEl.textContent = formatCurrency(finalPerPerson);
  heroSubEl.textContent = isCustomMode 
    ? `Divided among ${peopleCount} participants`
    : `Divided equally among ${peopleCount} friends`;

  // Render individual shares
  const indContainer = document.getElementById('individualShareContainer');
  let totalWeights = participants.reduce((sum, p) => sum + (p.shareRatio || 1), 0);

  const calculatedShares = participants.map((p, i) => {
    let share = 0;
    if (isCustomMode && totalWeights > 0) {
      share = (totalPayable * (p.shareRatio || 1)) / totalWeights;
    } else {
      share = finalPerPerson;
    }

    if (roundOption === '5' && isCustomMode) share = Math.ceil(share / 5) * 5;
    else if (roundOption === '10' && isCustomMode) share = Math.ceil(share / 10) * 10;
    else if (roundOption === '1' && isCustomMode) share = Math.ceil(share);

    return { name: p.name, amount: share };
  });

  if (indContainer) {
    indContainer.innerHTML = calculatedShares.map(s => `
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.35rem 0.5rem; background: var(--bg-body); border-radius: 6px; font-size: 0.88rem;">
        <span style="font-weight: 500;"><i class="fa-solid fa-user" style="color: var(--primary); font-size: 0.8rem; margin-right: 0.4rem;"></i>${escapeHtml(s.name)}</span>
        <strong class="amount-expense">${formatCurrency(s.amount)}</strong>
      </div>
    `).join('');
  }

  lastCalculated = {
    occasion: document.getElementById('billDescription')?.value.trim() || 'Shared Bill',
    baseBill: billAmount,
    tipPct: currentTipPct,
    tipAmount,
    taxPct,
    taxAmount,
    totalPayable,
    perPerson: finalPerPerson,
    myShare: calculatedShares[0]?.amount || finalPerPerson,
    shares: calculatedShares
  };
}

async function copySplitSummary() {
  if (!lastCalculated || lastCalculated.baseBill <= 0) {
    showToast('Notice', 'Enter a bill amount first.', 'warning');
    return;
  }

  const c = lastCalculated;
  const occasion = c.occasion ? `🧾 *${c.occasion}*` : '🧾 *Expense Split*';
  let lines = [
    occasion,
    `━━━━━━━━━━━━━━━━`,
    `💰 *Total Bill:* ${formatCurrency(c.totalPayable)} (Base: ${formatCurrency(c.baseBill)}${c.tipAmount > 0 ? ` + Tip ${formatCurrency(c.tipAmount)}` : ''})`,
    `👥 *Total People:* ${c.shares.length}`,
    `━━━━━━━━━━━━━━━━`,
    `*Individual Shares:*`
  ];

  c.shares.forEach(s => {
    lines.push(`• ${s.name}: *${formatCurrency(s.amount)}*`);
  });

  lines.push(`━━━━━━━━━━━━━━━━`);
  lines.push(`⚡ Please settle up via UPI / Net Banking!`);

  const fullText = lines.join('\n');

  try {
    await navigator.clipboard.writeText(fullText);
    showToast('Copied to Clipboard!', 'Share summary is ready to paste into WhatsApp / Telegram.', 'success');
  } catch (err) {
    // Fallback prompt
    const ta = document.createElement('textarea');
    ta.value = fullText;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showToast('Copied to Clipboard!', 'Share summary copied!', 'success');
  }
}

async function recordMyShareExpense() {
  if (!lastCalculated || lastCalculated.myShare <= 0) {
    showToast('Notice', 'Calculate bill amount first.', 'warning');
    return;
  }

  const c = lastCalculated;
  const desc = c.occasion ? `Split Bill: ${c.occasion}` : 'Split Bill (My Share)';
  const amount = c.myShare;
  const todayStr = new Date().toISOString().split('T')[0];

  if (!confirm(`Record ${formatCurrency(amount)} as an Expense in your tracker for "${desc}"?`)) return;

  try {
    const res = await fetch('/api/expenses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: todayStr,
        description: desc,
        category: 'Food',
        amount: amount,
        payment_method: 'UPI',
        type: 'Expense',
        notes: `Calculated using Split Bill Calculator. Total bill was ${formatCurrency(c.totalPayable)} split across ${c.shares.length} people.`
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Recorded to Tracker!', `${formatCurrency(amount)} logged as Food expense.`, 'success');
    } else {
      showToast('Error', data.message || 'Failed to record expense.', 'danger');
    }
  } catch (err) {
    showToast('Error', 'Network error recording expense.', 'danger');
  }
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
