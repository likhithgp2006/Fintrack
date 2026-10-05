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

/* Client-Side Password Encryption (SHA-256)
   Encrypts / hashes passwords before transmission so plain passwords are NEVER visible 
   in Network Inspect / DevTools payload or memory inspection. */
function sha256Fallback(ascii) {
  function rightRotate(value, amount) {
    return (value >>> amount) | (value << (32 - amount));
  }
  var mathPow = Math.pow;
  var maxWord = mathPow(2, 32);
  var lengthProperty = 'length';
  var i, j;
  var result = '';
  var words = [];
  var asciiBitLength = ascii[lengthProperty] * 8;
  var hash = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
  ];
  var k = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];
  words[asciiBitLength >> 5] |= 0x80 << (24 - (asciiBitLength % 32));
  words[(((asciiBitLength + 64) >> 9) << 4) + 15] = asciiBitLength;
  for (i = 0; i < ascii[lengthProperty]; i++) {
    words[i >> 2] |= ascii.charCodeAt(i) << ((3 - (i % 4)) * 8);
  }
  for (j = 0; j < words[lengthProperty];) {
    var w = words.slice(j, j += 16);
    var oldHash = hash;
    hash = hash.slice(0, 8);
    for (i = 0; i < 64; i++) {
      var i2 = i + j;
      var w15 = w[i - 15], w2 = w[i - 2];
      var a = hash[0], e = hash[4];
      var temp1 = hash[7]
        + (rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25))
        + ((e & hash[5]) ^ ((~e) & hash[6]))
        + k[i]
        + (w[i] = (i < 16) ? w[i] : (
            w[i - 16]
            + (rightRotate(w15, 7) ^ rightRotate(w15, 18) ^ (w15 >>> 3))
            + w[i - 7]
            + (rightRotate(w2, 17) ^ rightRotate(w2, 19) ^ (w2 >>> 10))
          ) | 0
        );
      var temp2 = (rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22))
        + ((a & hash[1]) ^ (a & hash[2]) ^ (hash[1] & hash[2]));
      hash = [(temp1 + temp2) | 0].concat(hash);
      hash[4] = (hash[4] + temp1) | 0;
    }
    for (i = 0; i < 8; i++) {
      hash[i] = (hash[i] + oldHash[i]) | 0;
    }
  }
  for (i = 0; i < 8; i++) {
    for (j = 3; j + 1; j--) {
      var b = (hash[i] >> (j * 8)) & 255;
      result += ((b < 16) ? '0' : '') + b.toString(16);
    }
  }
  return result;
}

async function encryptClientPassword(password) {
  if (!password) return '';
  try {
    if (window.crypto && window.crypto.subtle) {
      const encoder = new TextEncoder();
      const data = encoder.encode(password);
      const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }
  } catch (err) {
    console.warn('Subtle crypto unavailable, using fallback:', err);
  }
  return sha256Fallback(password);
}

window.encryptClientPassword = encryptClientPassword;



