/* Global Auth, Theme, Toast, and Utility Functions */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initMobileMenu();
  initLogoutBtn();
  initCurrencySelector();
  initCsvImportModal();
});

// Theme Management (Light / Dark Mode with localStorage)
function initTheme() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  const themeToggle = document.getElementById('themeToggleBtn');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
      updateThemeIcon(newTheme);
      
      // Notify chart renders if available
      if (window.renderDashboardCharts) {
        window.renderDashboardCharts();
      }
    });
  }
}

function updateThemeIcon(theme) {
  const themeToggle = document.getElementById('themeToggleBtn');
  if (themeToggle) {
    themeToggle.innerHTML = theme === 'dark' 
      ? '<i class="fa-solid fa-sun"></i>' 
      : '<i class="fa-solid fa-moon"></i>';
  }
}

// Mobile Hamburger Menu
function initMobileMenu() {
  const toggleBtn = document.getElementById('mobileMenuToggle');
  const sidebar = document.querySelector('.sidebar');
  const backdrop = document.getElementById('sidebarBackdrop');

  if (toggleBtn && sidebar && backdrop) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('mobile-open');
      backdrop.classList.toggle('active');
    });

    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('mobile-open');
      backdrop.classList.remove('active');
    });
  }
}

// Logout Action
function initLogoutBtn() {
  const logoutBtns = document.querySelectorAll('.logout-trigger');
  logoutBtns.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        const res = await fetch('/api/logout', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          showToast('Logged Out', 'You have been logged out successfully.', 'info');
          setTimeout(() => {
            window.location.href = '/login';
          }, 600);
        }
      } catch (err) {
        console.error('Logout error:', err);
      }
    });
  });
}

// Reusable Toast Notification System
function showToast(title, message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let iconClass = 'fa-circle-info';
  if (type === 'success') iconClass = 'fa-circle-check';
  if (type === 'danger') iconClass = 'fa-circle-exclamation';
  if (type === 'warning') iconClass = 'fa-triangle-exclamation';

  toast.innerHTML = `
    <i class="fa-solid ${iconClass} toast-icon"></i>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// --- Multi-Currency System ---
const CURRENCY_CONFIGS = {
  INR: { code: 'INR', symbol: '₹', locale: 'en-IN', label: 'INR (₹)' },
  USD: { code: 'USD', symbol: '$', locale: 'en-US', label: 'USD ($)' },
  EUR: { code: 'EUR', symbol: '€', locale: 'de-DE', label: 'EUR (€)' },
  GBP: { code: 'GBP', symbol: '£', locale: 'en-GB', label: 'GBP (£)' },
  AED: { code: 'AED', symbol: 'AED ', locale: 'en-AE', label: 'AED (د.إ)' },
  CAD: { code: 'CAD', symbol: 'CA$', locale: 'en-CA', label: 'CAD (C$)' },
  AUD: { code: 'AUD', symbol: 'AU$', locale: 'en-AU', label: 'AUD (A$)' },
  JPY: { code: 'JPY', symbol: '¥', locale: 'ja-JP', label: 'JPY (¥)' }
};

function getPreferredCurrency() {
  return localStorage.getItem('preferred_currency') || 'INR';
}

function getCurrencySymbol() {
  const code = getPreferredCurrency();
  return (CURRENCY_CONFIGS[code] || CURRENCY_CONFIGS.INR).symbol;
}

function setPreferredCurrency(currencyCode) {
  if (CURRENCY_CONFIGS[currencyCode]) {
    localStorage.setItem('preferred_currency', currencyCode);
    showToast('Currency Updated', `Display currency changed to ${currencyCode}`, 'success');
    window.dispatchEvent(new CustomEvent('currencyChanged', { detail: { currency: currencyCode } }));
    // Trigger soft reload of current view to update all formatted elements
    setTimeout(() => {
      window.location.reload();
    }, 400);
  }
}

function initCurrencySelector() {
  const selects = document.querySelectorAll('.global-currency-select');
  const current = getPreferredCurrency();
  selects.forEach(sel => {
    sel.value = current;
    sel.addEventListener('change', (e) => {
      setPreferredCurrency(e.target.value);
    });
  });
}

// Global Currency Formatter
function formatCurrency(amount) {
  const num = parseFloat(amount) || 0;
  const code = getPreferredCurrency();
  const cfg = CURRENCY_CONFIGS[code] || CURRENCY_CONFIGS.INR;
  return new Intl.NumberFormat(cfg.locale, {
    style: 'currency',
    currency: cfg.code,
    maximumFractionDigits: (cfg.code === 'JPY' ? 0 : 2)
  }).format(num);
}

// Backward-compatible alias for formatINR
function formatINR(amount) {
  return formatCurrency(amount);
}

// Date Formatter (YYYY-MM-DD to "26 Sep 2026")
function formatDate(dateStr) {
  if (!dateStr) return '';
  const parts = dateStr.split('-');
  if (parts.length < 3) return dateStr;
  const d = new Date(parts[0], parts[1] - 1, parts[2]);
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

// Global CSV Import Modal Handler
function initCsvImportModal() {
  const modal = document.getElementById('csvImportModal');
  const openBtns = document.querySelectorAll('#openCsvImportModalBtn, .trigger-csv-import');
  const closeBtn = document.getElementById('closeCsvImportBtn');
  const cancelBtn = document.getElementById('cancelCsvImportBtn');
  const dropzone = document.getElementById('csvDropzone');
  const fileInput = document.getElementById('csvFileInput');
  const fileLabel = document.getElementById('selectedFileName');
  const form = document.getElementById('csvImportForm');
  const submitBtn = document.getElementById('submitCsvImportBtn');

  if (!modal) return;

  const openModal = () => {
    modal.classList.add('active');
    if (form) form.reset();
    if (fileLabel) {
      fileLabel.style.display = 'none';
      fileLabel.textContent = '';
    }
  };

  const closeModal = () => {
    modal.classList.remove('active');
  };

  openBtns.forEach(btn => btn.addEventListener('click', (e) => {
    e.preventDefault();
    openModal();
  }));

  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    ['dragleave', 'dragend'].forEach(type => {
      dropzone.addEventListener(type, () => dropzone.classList.remove('dragover'));
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        updateFileLabel();
      }
    });

    fileInput.addEventListener('change', updateFileLabel);

    function updateFileLabel() {
      if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        if (fileLabel) {
          fileLabel.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
          fileLabel.style.display = 'block';
        }
      }
    }
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!fileInput.files || fileInput.files.length === 0) {
        showToast('Error', 'Please choose a CSV file to import.', 'danger');
        return;
      }

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Importing...';
      }

      try {
        const res = await fetch('/api/import/csv', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();

        if (data.success) {
          showToast('Import Success', data.message || 'Transactions imported successfully!', 'success');
          closeModal();
          setTimeout(() => {
            window.location.reload();
          }, 800);
        } else {
          showToast('Import Failed', data.message || 'Error importing CSV data.', 'danger');
        }
      } catch (err) {
        console.error('CSV import error:', err);
        showToast('Error', 'Network error during CSV upload.', 'danger');
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="fa-solid fa-upload"></i> Import Transactions';
        }
      }
    });
  }
}


