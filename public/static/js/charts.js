/* Dynamic Chart.js Handler */

let categoryChartInstance = null;
let monthlyChartInstance = null;

function renderCategoryChart(canvasId, categoryData) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  if (categoryChartInstance) {
    categoryChartInstance.destroy();
  }

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor = isDark ? '#f8fafc' : '#0f172a';

  const defaultColors = [
    '#ef4444', '#f59e0b', '#10b981', '#6366f1', '#ec4899',
    '#8b5cf6', '#3b82f6', '#06b6d4', '#14b8a6', '#84cc16'
  ];

  categoryChartInstance = new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: categoryData.labels || [],
      datasets: [{
        data: categoryData.datasets || [],
        backgroundColor: defaultColors,
        borderWidth: 2,
        borderColor: isDark ? '#151d2a' : '#ffffff',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: textColor,
            font: { family: 'Plus Jakarta Sans', size: 12 },
            padding: 15,
            usePointStyle: true
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const label = context.label || '';
              const val = context.raw || 0;
              return ` ${label}: ₹${val.toLocaleString('en-IN')}`;
            }
          }
        }
      },
      cutout: '68%'
    }
  });
}

function renderMonthlyChart(canvasId, monthlyData) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  if (monthlyChartInstance) {
    monthlyChartInstance.destroy();
  }

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const textColor = isDark ? '#94a3b8' : '#64748b';
  const gridColor = isDark ? '#263346' : '#e2e8f0';

  // Format month labels (e.g. "2026-09" to "Sep 26")
  const formattedLabels = (monthlyData.labels || []).map(m => {
    const parts = m.split('-');
    if (parts.length === 2) {
      const date = new Date(parts[0], parts[1] - 1);
      return date.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });
    }
    return m;
  });

  monthlyChartInstance = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: formattedLabels,
      datasets: [
        {
          label: 'Income',
          data: monthlyData.income || [],
          backgroundColor: '#10b981',
          borderRadius: 6
        },
        {
          label: 'Expenses',
          data: monthlyData.expense || [],
          backgroundColor: '#ef4444',
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: isDark ? '#f8fafc' : '#0f172a',
            font: { family: 'Plus Jakarta Sans', size: 12 },
            usePointStyle: true
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return ` ${context.dataset.label}: ₹${context.raw.toLocaleString('en-IN')}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: textColor }
        },
        y: {
          grid: { color: gridColor },
          ticks: {
            color: textColor,
            callback: function(val) {
              return '₹' + val.toLocaleString('en-IN');
            }
          }
        }
      }
    }
  });
}
