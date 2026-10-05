/* Transactions Page Logic (CRUD, Search, Filter, Sort, Pagination) */

let currentPage = 1;
let currentLimit = 10;
let currentSortBy = 'date';
let currentSortOrder = 'desc';
let editModalId = null;

document.addEventListener('DOMContentLoaded', () => {
  initTransactionsPage();
});

function initTransactionsPage() {
  loadCategoryFilterOptions();
  fetchAndRenderTransactions();

  // Search input listener with debounce
  const searchInput = document.getElementById('tableSearchInput');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        currentPage = 1;
        fetchAndRenderTransactions();
      }, 300);
    });
  }

  // Filter form listeners
  const filterForm = document.getElementById('filterForm');
  if (filterForm) {
    filterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      currentPage = 1;
      fetchAndRenderTransactions();
    });

    const resetBtn = document.getElementById('resetFilterBtn');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        filterForm.reset();
        if (searchInput) searchInput.value = '';
        currentPage = 1;
        fetchAndRenderTransactions();
      });
    }
  }

  // Filter Drawer Toggle
  const toggleFilterBtn = document.getElementById('toggleFilterBtn');
  const filterDrawer = document.getElementById('filterDrawer');
  if (toggleFilterBtn && filterDrawer) {
    toggleFilterBtn.addEventListener('click', () => {
      filterDrawer.style.display = filterDrawer.style.display === 'none' ? 'grid' : 'none';
    });
  }

  // Edit Modal Event Handlers
  initEditModal();
}

async function loadCategoryFilterOptions() {
  const catSelect = document.getElementById('filterCategory');
  const editCatSelect = document.getElementById('editExpenseCategory');
  if (!catSelect && !editCatSelect) return;

  try {
    const res = await fetch('/api/categories');
    const data = await res.json();
    if (data.success && data.categories) {
      const optionsHtml = data.categories.map(c => `<option value="${escapeHtml(c.name)}">${escapeHtml(c.name)}</option>`).join('');
      if (catSelect) catSelect.innerHTML = `<option value="">All Categories</option>` + optionsHtml;
      if (editCatSelect) editCatSelect.innerHTML = `<option value="">Select Category</option>` + optionsHtml;
    }
  } catch (err) {
    console.error('Filter categories load error:', err);
  }
}

async function fetchAndRenderTransactions() {
  const tableBody = document.getElementById('transactionsTableBody');
  if (!tableBody) return;

  tableBody.innerHTML = `
    <tr>
      <td colspan="7" class="empty-state">
        <div class="spinner" style="margin: 0 auto 1rem;"></div>
        <div class="empty-state-title">Loading transactions...</div>
      </td>
    </tr>
  `;

  // Build Query String
  const search = document.getElementById('tableSearchInput')?.value || '';
  const category = document.getElementById('filterCategory')?.value || '';
  const type = document.getElementById('filterType')?.value || '';
  const paymentMethod = document.getElementById('filterPaymentMethod')?.value || '';
  const startDate = document.getElementById('filterStartDate')?.value || '';
  const endDate = document.getElementById('filterEndDate')?.value || '';
  const minAmount = document.getElementById('filterMinAmount')?.value || '';
  const maxAmount = document.getElementById('filterMaxAmount')?.value || '';

  const params = new URLSearchParams({
    page: currentPage,
    limit: currentLimit,
    sort_by: currentSortBy,
    sort_order: currentSortOrder,
    search: search,
    category: category,
    type: type,
    payment_method: paymentMethod,
    start_date: startDate,
    end_date: endDate,
    min_amount: minAmount,
    max_amount: maxAmount
  });

  try {
    const res = await fetch(`/api/expenses?${params.toString()}`);
    const data = await res.json();

    if (!data.success) {
      showToast('Error', data.message || 'Failed to fetch transactions.', 'danger');
      return;
    }

    renderTableRows(data.expenses);
    renderPaginationControls(data.pagination);
    updateFilteredSummary(data.summary);

  } catch (err) {
    console.error('Fetch transactions error:', err);
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state" style="color:var(--danger)">
          <i class="fa-solid fa-triangle-exclamation empty-state-icon"></i>
          <div>Error loading data from server.</div>
        </td>
      </tr>
    `;
  }
}

function renderTableRows(expenses) {
  const tableBody = document.getElementById('transactionsTableBody');
  if (!tableBody) return;

  if (!expenses || expenses.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">
          <i class="fa-solid fa-folder-open empty-state-icon"></i>
          <div class="empty-state-title">No transactions found</div>
          <div class="empty-state-desc">Try adjusting your search query or filters.</div>
          <a href="/add-expense" class="btn btn-primary btn-sm"><i class="fa-solid fa-plus"></i> Add New Transaction</a>
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = expenses.map(t => {
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
        <td>
          <div class="table-actions">
            <button class="icon-btn icon-btn-edit" onclick="openEditModal('${t.id}')" title="Edit Transaction">
              <i class="fa-solid fa-pen-to-square"></i>
            </button>
            <button class="icon-btn icon-btn-delete" onclick="confirmDeleteTransaction('${t.id}', '${escapeHtml(t.description)}') " title="Delete Transaction">
              <i class="fa-solid fa-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function renderPaginationControls(meta) {
  const container = document.getElementById('paginationControls');
  const info = document.getElementById('paginationInfo');
  if (!container || !meta) return;

  if (meta.total === 0) {
    container.innerHTML = '';
    if (info) info.textContent = 'Showing 0 transactions';
    return;
  }

  const start = (meta.page - 1) * meta.limit + 1;
  const end = Math.min(meta.page * meta.limit, meta.total);
  if (info) info.textContent = `Showing ${start} to ${end} of ${meta.total} transactions`;

  let btns = '';
  btns += `<button class="page-btn" ${meta.page <= 1 ? 'disabled' : ''} onclick="changePage(${meta.page - 1})"><i class="fa-solid fa-chevron-left"></i></button>`;

  for (let p = 1; p <= meta.pages; p++) {
    btns += `<button class="page-btn ${p === meta.page ? 'active' : ''}" onclick="changePage(${p})">${p}</button>`;
  }

  btns += `<button class="page-btn" ${meta.page >= meta.pages ? 'disabled' : ''} onclick="changePage(${meta.page + 1})"><i class="fa-solid fa-chevron-right"></i></button>`;

  container.innerHTML = btns;
}

function changePage(newPage) {
  currentPage = newPage;
  fetchAndRenderTransactions();
}

function handleSort(column) {
  if (currentSortBy === column) {
    currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
  } else {
    currentSortBy = column;
    currentSortOrder = 'desc';
  }
  fetchAndRenderTransactions();
}

function updateFilteredSummary(summary) {
  const sumIncomeEl = document.getElementById('filteredTotalIncome');
  const sumExpenseEl = document.getElementById('filteredTotalExpense');
  if (sumIncomeEl) sumIncomeEl.textContent = formatINR(summary.filtered_income);
  if (sumExpenseEl) sumExpenseEl.textContent = formatINR(summary.filtered_expense);
}

/* Edit Modal Logic */
async function openEditModal(id) {
  editModalId = id;
  try {
    const res = await fetch(`/api/expenses/${id}`);
    const data = await res.json();
    if (data.success && data.expense) {
      const e = data.expense;
      document.getElementById('editExpenseDate').value = e.date;
      document.getElementById('editExpenseDescription').value = e.description;
      document.getElementById('editExpenseCategory').value = e.category;
      document.getElementById('editExpenseAmount').value = e.amount;
      document.getElementById('editExpensePaymentMethod').value = e.payment_method;
      document.getElementById('editExpenseType').value = e.type;
      document.getElementById('editExpenseNotes').value = e.notes || '';

      const modal = document.getElementById('editTransactionModal');
      if (modal) modal.classList.add('active');
    }
  } catch (err) {
    console.error('Fetch transaction details error:', err);
    showToast('Error', 'Unable to fetch transaction details.', 'danger');
  }
}

function initEditModal() {
  const modal = document.getElementById('editTransactionModal');
  const closeBtns = document.querySelectorAll('.close-modal-btn');
  const form = document.getElementById('editTransactionForm');

  closeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      if (modal) modal.classList.remove('active');
    });
  });

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!editModalId) return;

      const date = document.getElementById('editExpenseDate').value;
      const description = document.getElementById('editExpenseDescription').value.trim();
      const category = document.getElementById('editExpenseCategory').value;
      const amount = parseFloat(document.getElementById('editExpenseAmount').value);
      const payment_method = document.getElementById('editExpensePaymentMethod').value;
      const type = document.getElementById('editExpenseType').value;
      const notes = document.getElementById('editExpenseNotes').value.trim();

      try {
        const res = await fetch(`/api/expenses/${editModalId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ date, description, category, amount, payment_method, type, notes })
        });
        const data = await res.json();
        if (data.success) {
          showToast('Success', data.message || 'Transaction updated successfully.', 'success');
          if (modal) modal.classList.remove('active');
          fetchAndRenderTransactions();
        } else {
          showToast('Error', data.message || 'Failed to update transaction.', 'danger');
        }
      } catch (err) {
        console.error('Update error:', err);
        showToast('Error', 'Failed to update transaction.', 'danger');
      }
    });
  }
}

/* Delete Confirmation */
async function confirmDeleteTransaction(id, desc) {
  if (confirm(`Are you sure you want to delete "${desc}"?`)) {
    try {
      const res = await fetch(`/api/expenses/${id}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.success) {
        showToast('Deleted', data.message || 'Transaction deleted.', 'info');
        fetchAndRenderTransactions();
      } else {
        showToast('Error', data.message || 'Failed to delete transaction.', 'danger');
      }
    } catch (err) {
      console.error('Delete error:', err);
      showToast('Error', 'Network error deleting transaction.', 'danger');
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
