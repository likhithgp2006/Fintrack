/* Savings Goals Logic */

document.addEventListener('DOMContentLoaded', () => {
  loadGoals();
  initGoalModals();
});

let cachedGoals = [];

async function loadGoals() {
  const container = document.getElementById('goalsGridContainer');
  try {
    const res = await fetch('/api/goals');
    if (res.status === 401) {
      window.location.href = '/login';
      return;
    }
    const data = await res.json();
    if (!data.success) {
      showToast('Error', data.message || 'Could not fetch goals.', 'danger');
      return;
    }

    cachedGoals = data.goals || [];
    updateGoalsSummary(data.summary);
    renderGoalsGrid(cachedGoals);

  } catch (err) {
    console.error('Failed to load goals:', err);
    if (container) {
      container.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
          <i class="fa-solid fa-triangle-exclamation empty-state-icon text-danger"></i>
          <div class="empty-state-title">Failed to load goals</div>
          <div class="empty-state-desc">Please refresh the page to try again.</div>
        </div>
      `;
    }
  }
}

function updateGoalsSummary(summary) {
  if (!summary) return;
  const savedEl = document.getElementById('summaryTotalSaved');
  const targetEl = document.getElementById('summaryTotalTarget');
  const pctEl = document.getElementById('summaryOverallPct');
  const compEl = document.getElementById('summaryCompletedCount');

  if (savedEl) savedEl.textContent = formatCurrency(summary.total_saved);
  if (targetEl) targetEl.textContent = formatCurrency(summary.total_target);
  if (pctEl) pctEl.textContent = `${summary.overall_percentage}%`;
  if (compEl) compEl.textContent = summary.completed_count;
}

function getCategoryIcon(cat) {
  const map = {
    'Savings': 'fa-piggy-bank',
    'Emergency': 'fa-shield-halved',
    'Gadgets': 'fa-laptop',
    'Travel': 'fa-plane-departure',
    'Vehicle': 'fa-car',
    'Education': 'fa-graduation-cap',
    'Home': 'fa-house-chimney',
    'Other': 'fa-star'
  };
  return map[cat] || 'fa-bullseye';
}

function renderGoalsGrid(goals) {
  const container = document.getElementById('goalsGridContainer');
  if (!container) return;

  if (goals.length === 0) {
    container.innerHTML = `
      <div class="card empty-state" style="grid-column: 1 / -1; padding: 3rem 1.5rem; text-align: center;">
        <i class="fa-solid fa-bullseye empty-state-icon" style="font-size: 3rem; color: var(--primary); margin-bottom: 1rem;"></i>
        <h3 class="empty-state-title" style="margin-bottom: 0.5rem;">No savings goals yet</h3>
        <p class="empty-state-desc" style="max-width: 450px; margin: 0 auto 1.5rem;">
          Dreaming of a new gadget, vacation, or emergency safety net? Set your first goal and track your deposits!
        </p>
        <button class="btn btn-primary" onclick="document.getElementById('openNewGoalModalBtn').click()">
          <i class="fa-solid fa-plus"></i> Create Your First Goal
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = goals.map(g => {
    const isCompleted = g.percentage >= 100;
    const isOverdue = g.status === 'Overdue';
    const catIcon = getCategoryIcon(g.category);

    let progressColor = 'var(--primary)';
    if (g.percentage >= 100) progressColor = 'var(--success)';
    else if (g.percentage >= 75) progressColor = '#3b82f6';
    else if (g.percentage >= 50) progressColor = '#f59e0b';

    let deadlineBadge = '';
    if (isCompleted) {
      deadlineBadge = `<span class="badge badge-income"><i class="fa-solid fa-trophy"></i> Reached!</span>`;
    } else if (isOverdue) {
      deadlineBadge = `<span class="badge badge-expense"><i class="fa-solid fa-clock"></i> Overdue</span>`;
    } else if (g.days_remaining !== null) {
      deadlineBadge = `<span class="badge badge-category"><i class="fa-regular fa-clock"></i> ${g.days_remaining} days left</span>`;
    }

    return `
      <div class="card goal-card ${isCompleted ? 'goal-completed' : ''}">
        <div class="goal-card-header">
          <div class="goal-icon-badge">
            <i class="fa-solid ${catIcon}"></i>
          </div>
          <div class="goal-title-wrap">
            <h3 class="goal-title">${escapeHtml(g.title)}</h3>
            <span class="goal-category-label">${escapeHtml(g.category)}</span>
          </div>
          <div class="goal-status-badge">
            ${deadlineBadge}
          </div>
        </div>

        <div class="goal-amounts-row">
          <div>
            <div class="goal-amount-label">Saved</div>
            <div class="goal-amount-val amount-income">${formatCurrency(g.current_amount)}</div>
          </div>
          <div style="text-align: right;">
            <div class="goal-amount-label">Target</div>
            <div class="goal-amount-target">${formatCurrency(g.target_amount)}</div>
          </div>
        </div>

        <div class="goal-progress-wrap">
          <div class="goal-progress-bar-bg">
            <div class="goal-progress-bar-fill" style="width: ${g.percentage_display}%; background: ${progressColor};"></div>
          </div>
          <div class="goal-progress-meta">
            <span class="goal-milestone-text">${g.milestone ? g.milestone.badge : ''}</span>
            <span class="goal-pct-text">${g.percentage}%</span>
          </div>
        </div>

        ${g.notes ? `<p class="goal-notes-snippet"><i class="fa-regular fa-note-sticky"></i> ${escapeHtml(g.notes)}</p>` : ''}

        <div class="goal-card-footer">
          <button class="btn btn-sm btn-primary" onclick="openDepositModal(${g.id})" title="Deposit savings">
            <i class="fa-solid fa-piggy-bank"></i> + Deposit
          </button>
          <div class="goal-actions-group">
            <button class="btn btn-sm btn-secondary btn-icon" onclick="openEditGoalModal(${g.id})" title="Edit Goal">
              <i class="fa-solid fa-pen-to-square"></i>
            </button>
            <button class="btn btn-sm btn-danger btn-icon" onclick="deleteGoal(${g.id})" title="Delete Goal">
              <i class="fa-solid fa-trash-can"></i>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function initGoalModals() {
  const newGoalModal = document.getElementById('newGoalModal');
  const openNewBtn = document.getElementById('openNewGoalModalBtn');
  const closeBtns = document.querySelectorAll('.close-modal-btn');
  const newForm = document.getElementById('newGoalForm');
  const editForm = document.getElementById('editGoalForm');
  const contributeForm = document.getElementById('contributeForm');

  // Open New Goal Modal
  if (openNewBtn && newGoalModal) {
    openNewBtn.addEventListener('click', () => {
      newForm.reset();
      // default deadline 3 months ahead
      const d = new Date();
      d.setMonth(d.getMonth() + 3);
      document.getElementById('goalTargetDate').value = d.toISOString().split('T')[0];
      newGoalModal.classList.add('active');
    });
  }

  // Close modals
  closeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
    });
  });

  // Modal backdrop click
  document.querySelectorAll('.modal-overlay').forEach(m => {
    m.addEventListener('click', (e) => {
      if (e.target === m) m.classList.remove('active');
    });
  });

  // Submit New Goal
  if (newForm) {
    newForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const title = document.getElementById('goalTitle').value.trim();
      const target_amount = parseFloat(document.getElementById('goalTargetAmount').value) || 0;
      const current_amount = parseFloat(document.getElementById('goalCurrentAmount').value) || 0;
      const target_date = document.getElementById('goalTargetDate').value;
      const category = document.getElementById('goalCategory').value;
      const notes = document.getElementById('goalNotes').value.trim();

      try {
        const res = await fetch('/api/goals', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, target_amount, current_amount, target_date, category, notes })
        });
        const data = await res.json();
        if (data.success) {
          showToast('Goal Created', data.message, 'success');
          newGoalModal.classList.remove('active');
          loadGoals();
        } else {
          showToast('Error', data.message || 'Failed to create goal.', 'danger');
        }
      } catch (err) {
        showToast('Error', 'Network error creating goal.', 'danger');
      }
    });
  }

  // Quick Amount Pills in Deposit Modal
  document.querySelectorAll('.quick-amt-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const amtInput = document.getElementById('contributeAmount');
      const addVal = parseFloat(btn.dataset.amt) || 0;
      const currentVal = parseFloat(amtInput.value) || 0;
      amtInput.value = (currentVal + addVal);
    });
  });

  // Submit Deposit
  if (contributeForm) {
    contributeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const goalId = document.getElementById('contributeGoalId').value;
      const amount = parseFloat(document.getElementById('contributeAmount').value) || 0;
      const payment_method = document.getElementById('contributePaymentMethod').value;
      const record_expense = document.getElementById('contributeRecordExpense').checked;

      if (amount <= 0) {
        showToast('Error', 'Please enter a valid deposit amount.', 'danger');
        return;
      }

      try {
        const res = await fetch(`/api/goals/${goalId}/contribute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ amount, payment_method, record_expense })
        });
        const data = await res.json();
        if (data.success) {
          showToast('Savings Deposited!', data.message, 'success');
          document.getElementById('contributeModal').classList.remove('active');
          loadGoals();
        } else {
          showToast('Error', data.message, 'danger');
        }
      } catch (err) {
        showToast('Error', 'Failed to deposit savings.', 'danger');
      }
    });
  }

  // Submit Edit Goal
  if (editForm) {
    editForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const goalId = document.getElementById('editGoalId').value;
      const title = document.getElementById('editGoalTitle').value.trim();
      const target_amount = parseFloat(document.getElementById('editGoalTargetAmount').value) || 0;
      const current_amount = parseFloat(document.getElementById('editGoalCurrentAmount').value) || 0;
      const target_date = document.getElementById('editGoalTargetDate').value;
      const category = document.getElementById('editGoalCategory').value;
      const notes = document.getElementById('editGoalNotes').value.trim();

      try {
        const res = await fetch(`/api/goals/${goalId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, target_amount, current_amount, target_date, category, notes })
        });
        const data = await res.json();
        if (data.success) {
          showToast('Goal Updated', data.message, 'success');
          document.getElementById('editGoalModal').classList.remove('active');
          loadGoals();
        } else {
          showToast('Error', data.message, 'danger');
        }
      } catch (err) {
        showToast('Error', 'Network error updating goal.', 'danger');
      }
    });
  }
}

// Global modal triggers from rendered cards
window.openDepositModal = function(id) {
  const goal = cachedGoals.find(g => String(g.id) === String(id));
  if (!goal) return;

  document.getElementById('contributeGoalId').value = goal.id;
  document.getElementById('contributeGoalTitle').textContent = goal.title;
  document.getElementById('contributeGoalSubtext').textContent = 
    `Saved: ${formatCurrency(goal.current_amount)} of ${formatCurrency(goal.target_amount)} (${goal.percentage}%)`;
  document.getElementById('contributeAmount').value = '';

  document.getElementById('contributeModal').classList.add('active');
};

window.openEditGoalModal = function(id) {
  const goal = cachedGoals.find(g => String(g.id) === String(id));
  if (!goal) return;

  document.getElementById('editGoalId').value = goal.id;
  document.getElementById('editGoalTitle').value = goal.title;
  document.getElementById('editGoalTargetAmount').value = goal.target_amount;
  document.getElementById('editGoalCurrentAmount').value = goal.current_amount;
  document.getElementById('editGoalTargetDate').value = goal.target_date;
  document.getElementById('editGoalCategory').value = goal.category;
  document.getElementById('editGoalNotes').value = goal.notes || '';

  document.getElementById('editGoalModal').classList.add('active');
};

window.deleteGoal = async function(id) {
  const goal = cachedGoals.find(g => String(g.id) === String(id));
  const title = goal ? goal.title : 'this goal';
  if (!confirm(`Are you sure you want to delete "${title}"?`)) return;

  try {
    const res = await fetch(`/api/goals/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Deleted', data.message, 'info');
      loadGoals();
    } else {
      showToast('Error', data.message, 'danger');
    }
  } catch (err) {
    showToast('Error', 'Failed to delete goal.', 'danger');
  }
};

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
