/* Reports & Analytics Logic */

document.addEventListener('DOMContentLoaded', () => {
  initReportsPage();
});

function initReportsPage() {
  const monthSelect = document.getElementById('reportMonth');
  const yearSelect = document.getElementById('reportYear');
  const fetchBtn = document.getElementById('fetchReportBtn');

  // Set default month/year
  const now = new Date();
  if (monthSelect) monthSelect.value = String(now.getMonth() + 1).padStart(2, '0');
  if (yearSelect) yearSelect.value = String(now.getFullYear());

  loadMonthlyReport();
  loadCategoryReport();

  if (fetchBtn) {
    fetchBtn.addEventListener('click', () => {
      loadMonthlyReport();
    });
  }
}

async function loadMonthlyReport() {
  const m = document.getElementById('reportMonth')?.value || '09';
  const y = document.getElementById('reportYear')?.value || '2026';

  try {
    const res = await fetch(`/api/reports/monthly?month=${m}&year=${y}`);
    const data = await res.json();
    if (data.success) {
      document.getElementById('reportIncome').textContent = formatINR(data.summary.income);
      document.getElementById('reportExpenses').textContent = formatINR(data.summary.expenses);
      document.getElementById('reportBalance').textContent = formatINR(data.summary.balance);
      document.getElementById('reportCount').textContent = data.summary.transaction_count;
    }
  } catch (err) {
    console.error('Monthly report load error:', err);
  }
}

async function loadCategoryReport() {
  const container = document.getElementById('categoryProgressContainer');
  if (!container) return;

  try {
    const res = await fetch('/api/reports/category');
    const data = await res.json();
    if (!data.success || !data.categories || data.categories.length === 0) {
      container.innerHTML = `<div class="empty-state-desc">No category expense data available.</div>`;
      return;
    }

    const colors = ['#ef4444', '#f59e0b', '#10b981', '#6366f1', '#ec4899', '#8b5cf6', '#3b82f6'];

    container.innerHTML = data.categories.map((c, i) => {
      const color = colors[i % colors.length];
      return `
        <div class="progress-item">
          <div class="progress-header">
            <span><strong>${escapeHtml(c.category)}</strong></span>
            <span>${formatINR(c.amount)} (${c.percentage}%)</span>
          </div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: ${c.percentage}%; background-color: ${color};"></div>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Category report load error:', err);
  }
}

function printReport() {
  window.print();
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
