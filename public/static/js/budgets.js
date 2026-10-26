/* Budget Management Logic */

document.addEventListener('DOMContentLoaded', () => {
  initBudgetsPage();
});

function initBudgetsPage() {
  loadBudgets();
  loadBudgetCategoryDropdown();

  const addBudgetForm = document.getElementById('addBudgetForm');
  if (addBudgetForm) {
    addBudgetForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const category = document.getElementById('budgetCategory').value;
      const amount = parseFloat(document.getElementById('budgetAmount').value);
      const now = new Date();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const year = String(now.getFullYear());

      if (!category || isNaN(amount) || amount <= 0) {
        showToast('Validation Error', 'Please select a category and valid amount.', 'warning');
        return;
      }

      try {
        const res = await fetch('/api/budgets', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category, amount, month, year })
        });
        const data = await res.json();
        if (data.success) {
          showToast('Success', data.message || 'Budget saved.', 'success');
          addBudgetForm.reset();
          const modal = document.getElementById('addBudgetModal');
          if (modal) modal.classList.remove('active');
          loadBudgets();
        } else {
          showToast('Error', data.message || 'Failed to save budget.', 'danger');
        }
      } catch (err) {
        console.error('Budget save error:', err);
        showToast('Error', 'Server connection error.', 'danger');
      }
    });
  }

  // Open modal button
  const openBtn = document.getElementById('openAddBudgetModalBtn');
  const modal = document.getElementById('addBudgetModal');
  if (openBtn && modal) {
    openBtn.addEventListener('click', () => modal.classList.add('active'));
  }
}

async function loadBudgetCategoryDropdown() {
  const catSelect = document.getElementById('budgetCategory');
  if (!catSelect) return;

  try {
    const res = await fetch('/api/categories');
    const data = await res.json();
    if (data.success && data.categories) {
      catSelect.innerHTML = `<option value="">Select Category</option>` +
        data.categories.map(c => `<option value="${escapeHtml(c.name)}">${escapeHtml(c.name)}</option>`).join('');
    }
  } catch (err) {
    console.error('Budget categories load error:', err);
  }
}

async function loadBudgets() {
  const container = document.getElementById('budgetsGridContainer');
  if (!container) return;

  try {
    const res = await fetch('/api/budgets');
    const data = await res.json();

    if (!data.success || !data.budgets || data.budgets.length === 0) {
      container.innerHTML = `
        <div class="card empty-state" style="grid-column: 1/-1;">
          <i class="fa-solid fa-calculator empty-state-icon"></i>
          <div class="empty-state-title">No Budgets Configured</div>
          <div class="empty-state-desc">Set spending limits for your categories to prevent overspending!</div>
          <button class="btn btn-primary btn-sm" onclick="document.getElementById('addBudgetModal').classList.add('active')">
            <i class="fa-solid fa-plus"></i> Set First Budget
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = data.budgets.map(b => {
      let alertClass = 'alert-ok';
      let statusText = 'On Track';
      let progressColor = 'var(--success)';

      if (b.status === 'danger') {
        alertClass = 'alert-danger';
        statusText = 'Exceeded!';
        progressColor = 'var(--danger)';
      } else if (b.status === 'warning') {
        alertClass = 'alert-warning';
        statusText = 'Near Limit (80%+)';
        progressColor = 'var(--warning)';
      }

      return `
        <div class="card card-hover budget-card">
          <div class="budget-card-header">
            <div class="budget-cat-name">
              <i class="fa-solid fa-chart-pie" style="color: var(--primary);"></i> ${escapeHtml(b.category)}
            </div>
            <div class="budget-alert-badge ${alertClass}">${statusText}</div>
          </div>

          <div class="budget-amounts">
            <span>Spent: <strong>${formatINR(b.spent_amount)}</strong></span>
            <span>Budget: <strong>${formatINR(b.budget_amount)}</strong></span>
          </div>

          <div class="progress-bar-bg" style="margin-bottom: 0.75rem;">
            <div class="progress-bar-fill" style="width: ${Math.min(b.percentage_used, 100)}%; background-color: ${progressColor};"></div>
          </div>

          <div style="display: flex; justify-content: space-between; font-size: 0.82rem; color: var(--text-muted);">
            <span>${b.percentage_used}% used</span>
            <span>Remaining: <strong>${formatINR(b.remaining_amount)}</strong></span>
          </div>

          <div style="margin-top: 1rem; text-align: right;">
            <button class="btn btn-danger btn-sm" onclick="deleteBudget('${b.id}', '${escapeHtml(b.category)}')">
              <i class="fa-solid fa-trash"></i> Delete
            </button>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Load budgets error:', err);
  }
}

async function deleteBudget(id, category) {
  if (confirm(`Remove budget for ${category}?`)) {
    try {
      const res = await fetch(`/api/budgets/${id}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.success) {
        showToast('Deleted', data.message || 'Budget removed.', 'info');
        loadBudgets();
      }
    } catch (err) {
      console.error('Delete budget error:', err);
    }
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
