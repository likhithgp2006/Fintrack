/* Recurring Subscriptions Logic */

document.addEventListener('DOMContentLoaded', () => {
  loadSubscriptions();
  initSubModals();
});

let cachedSubs = [];

async function loadSubscriptions() {
  const tbody = document.getElementById('subscriptionsTableBody');
  try {
    const res = await fetch('/api/subscriptions');
    if (res.status === 401) {
      window.location.href = '/login';
      return;
    }
    const data = await res.json();
    if (!data.success) {
      showToast('Error', data.message || 'Could not fetch subscriptions.', 'danger');
      return;
    }

    cachedSubs = data.subscriptions || [];
    updateSubsSummary(data.summary);
    renderSubsTable(cachedSubs);

  } catch (err) {
    console.error('Failed to load subscriptions:', err);
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="empty-state">
            <i class="fa-solid fa-triangle-exclamation empty-state-icon text-danger"></i>
            <div class="empty-state-title">Failed to load subscriptions</div>
          </td>
        </tr>
      `;
    }
  }
}

function updateSubsSummary(summary) {
  if (!summary) return;
  const monthEl = document.getElementById('subMonthlyTotal');
  const yearEl = document.getElementById('subYearlyTotal');
  const activeEl = document.getElementById('subActiveCount');
  const upcomingEl = document.getElementById('subUpcomingCount');

  if (monthEl) monthEl.textContent = formatCurrency(summary.total_monthly);
  if (yearEl) yearEl.textContent = formatCurrency(summary.total_yearly);
  if (activeEl) activeEl.textContent = summary.active_count;
  if (upcomingEl) upcomingEl.textContent = summary.renewing_soon_count;
}

function getServiceIcon(name) {
  const n = name.toLowerCase();
  if (n.includes('netflix')) return 'fa-film';
  if (n.includes('spotify') || n.includes('music')) return 'fa-music';
  if (n.includes('gym') || n.includes('fitness')) return 'fa-dumbbell';
  if (n.includes('prime') || n.includes('amazon')) return 'fa-box-open';
  if (n.includes('youtube')) return 'fa-play';
  if (n.includes('github') || n.includes('code') || n.includes('copilot')) return 'fa-code';
  if (n.includes('wi-fi') || n.includes('internet') || n.includes('broadband')) return 'fa-wifi';
  if (n.includes('apple') || n.includes('icloud')) return 'fa-cloud';
  return 'fa-repeat';
}

function renderSubsTable(subs) {
  const tbody = document.getElementById('subscriptionsTableBody');
  if (!tbody) return;

  if (subs.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="empty-state">
          <i class="fa-solid fa-repeat empty-state-icon"></i>
          <div class="empty-state-title">No subscriptions added yet</div>
          <div class="empty-state-desc">Add recurring memberships like Netflix, Spotify, Gym, or Wi-Fi to track monthly costs.</div>
          <button class="btn btn-primary btn-sm" onclick="document.getElementById('openNewSubModalBtn').click()" style="margin-top: 0.75rem;">
            <i class="fa-solid fa-plus"></i> Add First Subscription
          </button>
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = subs.map(s => {
    const isActive = s.status === 'Active';
    const icon = getServiceIcon(s.name);

    let renewalBadge = '';
    if (!isActive) {
      renewalBadge = `<span class="badge" style="background: var(--border-color); color: var(--text-muted);">Paused</span>`;
    } else if (s.days_until_renewal === null) {
      renewalBadge = `<span class="badge badge-category">${formatDate(s.next_billing_date)}</span>`;
    } else if (s.days_until_renewal < 0) {
      renewalBadge = `<span class="badge badge-expense" title="${formatDate(s.next_billing_date)}"><i class="fa-solid fa-circle-exclamation"></i> Overdue (${Math.abs(s.days_until_renewal)}d)</span>`;
    } else if (s.days_until_renewal === 0) {
      renewalBadge = `<span class="badge badge-expense" title="${formatDate(s.next_billing_date)}"><i class="fa-solid fa-bell"></i> Renews Today!</span>`;
    } else if (s.days_until_renewal <= 3) {
      renewalBadge = `<span class="badge badge-expense" title="${formatDate(s.next_billing_date)}"><i class="fa-solid fa-clock"></i> In ${s.days_until_renewal} days</span>`;
    } else if (s.days_until_renewal <= 7) {
      renewalBadge = `<span class="badge badge-warning" title="${formatDate(s.next_billing_date)}"><i class="fa-regular fa-clock"></i> In ${s.days_until_renewal} days</span>`;
    } else {
      renewalBadge = `<span class="badge badge-category" title="${formatDate(s.next_billing_date)}">${formatDate(s.next_billing_date)} (${s.days_until_renewal}d)</span>`;
    }

    const statusBadge = isActive 
      ? `<button class="badge badge-income" onclick="toggleSubStatus(${s.id}, 'Paused')" title="Click to pause" style="cursor: pointer; border: none;"><i class="fa-solid fa-check"></i> Active</button>`
      : `<button class="badge" onclick="toggleSubStatus(${s.id}, 'Active')" title="Click to activate" style="background: var(--border-color); color: var(--text-muted); cursor: pointer; border: none;"><i class="fa-solid fa-pause"></i> Paused</button>`;

    return `
      <tr>
        <td>
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div class="user-avatar" style="width: 38px; height: 38px; font-size: 1rem; background: var(--primary-light); color: var(--primary); border-radius: 10px;">
              <i class="fa-solid ${icon}"></i>
            </div>
            <div>
              <div style="font-weight: 600;">${escapeHtml(s.name)}</div>
              <small class="text-muted">${escapeHtml(s.category)}</small>
            </div>
          </div>
        </td>
        <td><span class="badge badge-category">${s.billing_cycle}</span></td>
        <td><strong class="amount-expense">${formatCurrency(s.amount)}</strong></td>
        <td><span class="text-muted">${formatCurrency(s.monthly_equivalent)}/mo</span></td>
        <td>${renewalBadge}</td>
        <td><span class="badge badge-category"><i class="fa-regular fa-credit-card"></i> ${escapeHtml(s.payment_method)}</span></td>
        <td>${statusBadge}</td>
        <td>
          <div style="display: flex; gap: 0.35rem; align-items: center;">
            <button class="btn btn-sm btn-primary" onclick="logSubExpense(${s.id})" title="Log current payment as expense and advance renewal date" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;">
              <i class="fa-solid fa-bolt"></i> Log
            </button>
            <button class="btn btn-sm btn-secondary btn-icon" onclick="openEditSubModal(${s.id})" title="Edit Subscription">
              <i class="fa-solid fa-pen-to-square"></i>
            </button>
            <button class="btn btn-sm btn-danger btn-icon" onclick="deleteSub(${s.id})" title="Delete Subscription">
              <i class="fa-solid fa-trash-can"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function initSubModals() {
  const newSubModal = document.getElementById('newSubModal');
  const openNewBtn = document.getElementById('openNewSubModalBtn');
  const closeBtns = document.querySelectorAll('.close-modal-btn');
  const newForm = document.getElementById('newSubForm');
  const editForm = document.getElementById('editSubForm');

  if (openNewBtn && newSubModal) {
    openNewBtn.addEventListener('click', () => {
      newForm.reset();
      // default next date 1 month from now
      const d = new Date();
      d.setMonth(d.getMonth() + 1);
      document.getElementById('subNextBillingDate').value = d.toISOString().split('T')[0];
      newSubModal.classList.add('active');
    });
  }

  closeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
    });
  });

  document.querySelectorAll('.modal-overlay').forEach(m => {
    m.addEventListener('click', (e) => {
      if (e.target === m) m.classList.remove('active');
    });
  });

  if (newForm) {
    newForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('subName').value.trim();
      const amount = parseFloat(document.getElementById('subAmount').value) || 0;
      const billing_cycle = document.getElementById('subBillingCycle').value;
      const next_billing_date = document.getElementById('subNextBillingDate').value;
      const category = document.getElementById('subCategory').value;
      const payment_method = document.getElementById('subPaymentMethod').value;
      const status = document.getElementById('subStatus').value;

      try {
        const res = await fetch('/api/subscriptions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, amount, billing_cycle, next_billing_date, category, payment_method, status })
        });
        const data = await res.json();
        if (data.success) {
          showToast('Added', data.message, 'success');
          newSubModal.classList.remove('active');
          loadSubscriptions();
        } else {
          showToast('Error', data.message || 'Failed to add subscription.', 'danger');
        }
      } catch (err) {
        showToast('Error', 'Network error adding subscription.', 'danger');
      }
    });
  }

  if (editForm) {
    editForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const subId = document.getElementById('editSubId').value;
      const name = document.getElementById('editSubName').value.trim();
      const amount = parseFloat(document.getElementById('editSubAmount').value) || 0;
      const billing_cycle = document.getElementById('editSubBillingCycle').value;
      const next_billing_date = document.getElementById('editSubNextBillingDate').value;
      const category = document.getElementById('editSubCategory').value;
      const payment_method = document.getElementById('editSubPaymentMethod').value;
      const status = document.getElementById('editSubStatus').value;

      try {
        const res = await fetch(`/api/subscriptions/${subId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, amount, billing_cycle, next_billing_date, category, payment_method, status })
        });
        const data = await res.json();
        if (data.success) {
          showToast('Updated', data.message, 'success');
          document.getElementById('editSubModal').classList.remove('active');
          loadSubscriptions();
        } else {
          showToast('Error', data.message, 'danger');
        }
      } catch (err) {
        showToast('Error', 'Network error updating subscription.', 'danger');
      }
    });
  }
}

window.toggleSubStatus = async function(id, newStatus) {
  try {
    const res = await fetch(`/api/subscriptions/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Status Updated', `Subscription set to ${newStatus}`, 'info');
      loadSubscriptions();
    }
  } catch (err) {
    showToast('Error', 'Failed to update status.', 'danger');
  }
};

window.logSubExpense = async function(id) {
  const sub = cachedSubs.find(s => String(s.id) === String(id));
  const name = sub ? sub.name : 'this service';
  if (!confirm(`Log ${formatCurrency(sub.amount)} payment for "${name}" as an Expense? (This will also advance the next renewal date)`)) return;

  try {
    const res = await fetch(`/api/subscriptions/${id}/log-expense`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast('Logged to Ledger', data.message, 'success');
      loadSubscriptions();
    } else {
      showToast('Error', data.message, 'danger');
    }
  } catch (err) {
    showToast('Error', 'Failed to log subscription expense.', 'danger');
  }
};

window.openEditSubModal = function(id) {
  const sub = cachedSubs.find(s => String(s.id) === String(id));
  if (!sub) return;

  document.getElementById('editSubId').value = sub.id;
  document.getElementById('editSubName').value = sub.name;
  document.getElementById('editSubAmount').value = sub.amount;
  document.getElementById('editSubBillingCycle').value = sub.billing_cycle;
  document.getElementById('editSubNextBillingDate').value = sub.next_billing_date;
  document.getElementById('editSubCategory').value = sub.category;
  document.getElementById('editSubPaymentMethod').value = sub.payment_method;
  document.getElementById('editSubStatus').value = sub.status;

  document.getElementById('editSubModal').classList.add('active');
};

window.deleteSub = async function(id) {
  const sub = cachedSubs.find(s => String(s.id) === String(id));
  const name = sub ? sub.name : 'this subscription';
  if (!confirm(`Are you sure you want to remove "${name}"?`)) return;

  try {
    const res = await fetch(`/api/subscriptions/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Removed', data.message, 'info');
      loadSubscriptions();
    } else {
      showToast('Error', data.message, 'danger');
    }
  } catch (err) {
    showToast('Error', 'Failed to remove subscription.', 'danger');
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
