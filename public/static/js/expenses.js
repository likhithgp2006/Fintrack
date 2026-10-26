/* Add Expense / Transaction Handler */

document.addEventListener('DOMContentLoaded', () => {
  initAddExpenseForm();
  loadCategoryDropdown();
});

function initAddExpenseForm() {
  const form = document.getElementById('addExpenseForm');
  const dateInput = document.getElementById('expenseDate');

  if (dateInput && !dateInput.value) {
    // Set default date to today's date (YYYY-MM-DD)
    dateInput.value = new Date().toISOString().split('T')[0];
  }

  // Type toggle pill behavior (Expense vs Income)
  const typeRadios = document.querySelectorAll('input[name="type"]');
  const toggleBtns = document.querySelectorAll('.type-toggle-btn');

  toggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const radio = btn.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
        updateTypePillUI();
      }
    });
  });

  function updateTypePillUI() {
    const selected = document.querySelector('input[name="type"]:checked')?.value || 'Expense';
    toggleBtns.forEach(btn => {
      const radio = btn.querySelector('input[type="radio"]');
      if (radio.value === 'Expense') {
        if (radio.checked) btn.classList.add('active-expense');
        else btn.classList.remove('active-expense');
      } else {
        if (radio.checked) btn.classList.add('active-income');
        else btn.classList.remove('active-income');
      }
    });
  }
  updateTypePillUI();

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const date = document.getElementById('expenseDate').value;
      const description = document.getElementById('expenseDescription').value.trim();
      const category = document.getElementById('expenseCategory').value;
      const amount = parseFloat(document.getElementById('expenseAmount').value);
      const payment_method = document.getElementById('expensePaymentMethod').value;
      const type = document.querySelector('input[name="type"]:checked')?.value || 'Expense';
      const notes = document.getElementById('expenseNotes')?.value.trim() || '';

      // Frontend Validations
      if (!date) {
        showToast('Validation Error', 'Please select a valid date.', 'warning');
        return;
      }
      if (!description) {
        showToast('Validation Error', 'Description is required.', 'warning');
        return;
      }
      if (!category) {
        showToast('Validation Error', 'Please select a category.', 'warning');
        return;
      }
      if (isNaN(amount) || amount <= 0) {
        showToast('Validation Error', 'Amount must be greater than zero.', 'warning');
        return;
      }
      if (!payment_method) {
        showToast('Validation Error', 'Please select a payment method.', 'warning');
        return;
      }

      const submitBtn = form.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<div class="spinner" style="width:18px;height:18px;border-width:2px;display:inline-block;"></div> Saving...`;

      try {
        const res = await fetch('/api/expenses', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            date,
            description,
            category,
            amount,
            payment_method,
            type,
            notes
          })
        });

        const data = await res.json();
        if (data.success) {
          showToast('Success!', data.message || 'Transaction saved successfully.', 'success');
          form.reset();
          if (dateInput) dateInput.value = new Date().toISOString().split('T')[0];
          updateTypePillUI();

          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 800);
        } else {
          showToast('Error', data.message || 'Failed to save transaction.', 'danger');
        }
      } catch (err) {
        console.error('Save error:', err);
        showToast('Error', 'Server connection error.', 'danger');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }
}

async function loadCategoryDropdown() {
  const catSelect = document.getElementById('expenseCategory');
  if (!catSelect) return;

  try {
    const res = await fetch('/api/categories');
    const data = await res.json();
    if (data.success && data.categories) {
      catSelect.innerHTML = `<option value="">Select Category</option>` +
        data.categories.map(c => `<option value="${escapeHtml(c.name)}">${escapeHtml(c.name)}</option>`).join('');
    }
  } catch (err) {
    console.error('Categories dropdown load error:', err);
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
