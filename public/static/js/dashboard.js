/* Dashboard Logic */

document.addEventListener('DOMContentLoaded', () => {
  loadDashboardData();
  loadFinancialHealth();
  checkBudgetAlerts();
});

let cachedDashboardData = null;

async function loadDashboardData() {
  try {
    const res = await fetch('/api/dashboard');
    if (res.status === 401) {
      window.location.href = '/login';
      return;
    }
    const data = await res.json();
    if (!data.success) {
      showToast('Error', data.message || 'Failed to load dashboard data.', 'danger');
      return;
    }

    cachedDashboardData = data;
    updateStatCards(data.summary);
    renderRecentTransactions(data.recent_transactions);
    
    window.renderDashboardCharts = () => {
      if (cachedDashboardData && cachedDashboardData.charts) {
        renderCategoryChart('categoryChartCanvas', cachedDashboardData.charts.category);
        renderMonthlyChart('monthlyChartCanvas', cachedDashboardData.charts.monthly);
      }
    };

    window.renderDashboardCharts();

  } catch (err) {
    console.error('Dashboard load error:', err);
    showToast('Error', 'Network error loading dashboard data.', 'danger');
  }
}

function updateStatCards(summary) {
  if (!summary) return;

  const totalIncomeEl = document.getElementById('statTotalIncome');
  const totalExpensesEl = document.getElementById('statTotalExpenses');
  const balanceEl = document.getElementById('statBalance');
  const countEl = document.getElementById('statTransactionCount');
  const highestEl = document.getElementById('statHighestExpense');
  const monthSpendingEl = document.getElementById('statCurrentMonthSpending');

  if (totalIncomeEl) totalIncomeEl.textContent = formatINR(summary.total_income);
  if (totalExpensesEl) totalExpensesEl.textContent = formatINR(summary.total_expenses);
  if (balanceEl) balanceEl.textContent = formatINR(summary.balance);
  if (countEl) countEl.textContent = summary.total_transactions;
  if (highestEl) highestEl.textContent = formatINR(summary.highest_expense);
  if (monthSpendingEl) monthSpendingEl.textContent = formatINR(summary.current_month_spending);
}

function renderRecentTransactions(transactions) {
  const container = document.getElementById('recentTransactionsBody');
  if (!container) return;

  if (!transactions || transactions.length === 0) {
    container.innerHTML = `
      <tr>
        <td colspan="6" class="empty-state">
          <i class="fa-solid fa-receipt empty-state-icon"></i>
          <div class="empty-state-title">No transactions yet</div>
          <div class="empty-state-desc">Click below to record your first income or expense!</div>
          <a href="/add-expense" class="btn btn-primary btn-sm"><i class="fa-solid fa-plus"></i> Add Transaction</a>
        </td>
      </tr>
    `;
    return;
  }

  container.innerHTML = transactions.map(t => {
    const isExpense = t.type === 'Expense';
    const amountClass = isExpense ? 'amount-expense' : 'amount-income';
    const badgeClass = isExpense ? 'badge-expense' : 'badge-income';
    const amountPrefix = isExpense ? '-' : '+';

    return `
      <tr>
        <td><strong>${formatDate(t.date)}</strong></td>
        <td>
          <div style="font-weight: 600;">${escapeHtml(t.description)}</div>
          ${t.notes ? `<small class="text-muted" style="font-size:0.78rem;">${escapeHtml(t.notes)}</small>` : ''}
        </td>
        <td><span class="badge badge-category">${escapeHtml(t.category)}</span></td>
        <td><span class="badge ${badgeClass}">${t.type}</span></td>
        <td><span class="badge badge-category"><i class="fa-solid fa-wallet"></i> ${escapeHtml(t.payment_method)}</span></td>
        <td class="amount-text ${amountClass}">${amountPrefix}${formatINR(t.amount)}</td>
      </tr>
    `;
  }).join('');
}

async function checkBudgetAlerts() {
  try {
    const res = await fetch('/api/budgets');
    const data = await res.json();
    if (data.success && data.warnings && data.warnings.length > 0) {
      data.warnings.forEach(warn => {
        showToast('Budget Notification', warn, warn.includes('Exceeded') ? 'danger' : 'warning');
      });
    }
  } catch (err) {
    console.error('Budget check error:', err);
  }
}

async function loadFinancialHealth() {
  try {
    const res = await fetch('/api/analytics/financial-health');
    const data = await res.json();
    if (!data.success) return;

    // Score & Grade
    const scoreNumEl = document.getElementById('healthScoreNum');
    const scoreCircleEl = document.getElementById('healthScoreCircle');
    const gradeBadgeEl = document.getElementById('healthGradeBadge');
    const savingsRateBadgeEl = document.getElementById('healthSavingsRateBadge');

    if (scoreNumEl) scoreNumEl.textContent = data.health_score;
    if (gradeBadgeEl) {
      gradeBadgeEl.innerHTML = `<span style="font-weight: 700;">Grade ${data.grade}</span> &bull; ${data.rating}`;
      gradeBadgeEl.style.backgroundColor = data.color + '22';
      gradeBadgeEl.style.color = data.color;
      gradeBadgeEl.style.borderColor = data.color + '55';
    }
    if (scoreCircleEl) {
      scoreCircleEl.style.borderColor = data.color;
    }

    if (savingsRateBadgeEl) {
      const sRate = data.breakdown.savings_rate;
      savingsRateBadgeEl.textContent = `Savings Rate: ${sRate}%`;
      savingsRateBadgeEl.className = sRate >= 20 ? 'badge badge-income' : (sRate > 0 ? 'badge badge-warning' : 'badge badge-expense');
    }

    // 50/30/20 Stacked Bar
    const b = data.breakdown;
    const barNeeds = document.getElementById('barNeeds');
    const barWants = document.getElementById('barWants');
    const barSavings = document.getElementById('barSavings');

    const totalWeight = Math.max(1, (b.needs_pct + b.wants_pct + b.savings_pct));
    const widthNeeds = (b.needs_pct / totalWeight * 100).toFixed(1);
    const widthWants = (b.wants_pct / totalWeight * 100).toFixed(1);
    const widthSavings = (b.savings_pct / totalWeight * 100).toFixed(1);

    if (barNeeds) barNeeds.style.width = `${widthNeeds}%`;
    if (barWants) barWants.style.width = `${widthWants}%`;
    if (barSavings) barSavings.style.width = `${widthSavings}%`;

    const valNeeds = document.getElementById('valNeeds');
    const valWants = document.getElementById('valWants');
    const valSavings = document.getElementById('valSavings');

    if (valNeeds) valNeeds.textContent = `${b.needs_pct}%`;
    if (valWants) valWants.textContent = `${b.wants_pct}%`;
    if (valSavings) valSavings.textContent = `${b.savings_pct}%`;

    // Smart Insights List
    const insightsContainer = document.getElementById('smartInsightsList');
    if (insightsContainer && data.insights) {
      insightsContainer.innerHTML = data.insights.map(ins => `
        <div class="insight-item insight-${ins.type || 'info'}">
          <i class="fa-solid ${ins.icon || 'fa-lightbulb'} insight-icon"></i>
          <div class="insight-text-wrap">
            <div class="insight-item-title">${escapeHtml(ins.title)}</div>
            <div class="insight-item-desc">${escapeHtml(ins.text)}</div>
          </div>
        </div>
      `).join('');
    }

  } catch (err) {
    console.error('Financial health load error:', err);
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

