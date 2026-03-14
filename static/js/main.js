/**
 * ===========================================
 * School FMS — Main JavaScript
 * ===========================================
 * Sidebar toggle, mobile menu, chart initialization,
 * and interactive UI behaviours.
 */

document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initAlerts();
});

// -----------------------------------------------
// Sidebar Toggle
// -----------------------------------------------
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileToggle = document.getElementById('mobileToggle');

    // Desktop sidebar collapse — CSS handles all layout via .collapsed class
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }

    // Mobile sidebar toggle
    if (mobileToggle) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768
                && !sidebar.contains(e.target)
                && !mobileToggle.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }
}

// -----------------------------------------------
// Auto-dismiss alerts after 5 seconds
// -----------------------------------------------
function initAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

// -----------------------------------------------
// Chart Helpers (reusable for dashboard)
// -----------------------------------------------

/**
 * Create a line/bar chart for income vs expense trends.
 * @param {string} canvasId - Canvas element ID
 * @param {Array} labels - Month labels
 * @param {Array} incomeData - Income amounts
 * @param {Array} expenseData - Expense amounts
 */
function createTrendChart(canvasId, labels, incomeData, expenseData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    backgroundColor: 'rgba(249, 115, 22, 0.7)',
                    borderColor: '#F97316',
                    borderWidth: 2,
                    borderRadius: 6,
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    backgroundColor: 'rgba(220, 38, 38, 0.5)',
                    borderColor: '#DC2626',
                    borderWidth: 2,
                    borderRadius: 6,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#6B7280', font: { family: 'Inter' } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    ticks: { color: '#6B7280' },
                },
                y: {
                    grid: { color: 'rgba(0,0,0,0.04)' },
                    ticks: { color: '#6B7280' },
                },
            },
        },
    });
}

/**
 * Create a doughnut chart for expense distribution.
 * @param {string} canvasId - Canvas element ID
 * @param {Array} labels - Category labels
 * @param {Array} data - Amounts per category
 */
function createDistributionChart(canvasId, labels, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const colors = [
        '#F97316', '#0D9488', '#2563EB', '#F59E0B',
        '#8B5CF6', '#EC4899', '#14B8A6', '#EF4444',
    ];

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, data.length),
                borderColor: '#FFFFFF',
                borderWidth: 3,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#6B7280', font: { family: 'Inter' }, padding: 16 }
                }
            },
            cutout: '65%',
        },
    });
}

// -----------------------------------------------
// Journal Entry Form — Dynamic Line Management
// -----------------------------------------------
function addJournalLine() {
    const container = document.getElementById('journal-lines');
    const countInput = document.getElementById('line_count');
    const count = parseInt(countInput.value);

    const row = document.createElement('div');
    row.className = 'journal-line form-row';
    row.style.gridTemplateColumns = '2fr 1fr 1fr 2fr auto';
    row.style.gap = '10px';
    row.style.marginBottom = '8px';
    row.innerHTML = `
        <select name="lines-${count}-account" class="form-control" required>
            ${document.getElementById('account-options').innerHTML}
        </select>
        <input type="number" name="lines-${count}-debit" step="0.01" value="0" class="form-control" placeholder="Debit" onchange="updateBalance()">
        <input type="number" name="lines-${count}-credit" step="0.01" value="0" class="form-control" placeholder="Credit" onchange="updateBalance()">
        <input type="text" name="lines-${count}-description" class="form-control" placeholder="Description">
        <button type="button" class="btn btn-danger btn-sm" onclick="this.parentElement.remove(); updateBalance();">
            <i class="fas fa-trash"></i>
        </button>
    `;
    container.appendChild(row);
    countInput.value = count + 1;
}

function updateBalance() {
    let totalDebit = 0, totalCredit = 0;
    document.querySelectorAll('[name$="-debit"]').forEach(el => {
        totalDebit += parseFloat(el.value) || 0;
    });
    document.querySelectorAll('[name$="-credit"]').forEach(el => {
        totalCredit += parseFloat(el.value) || 0;
    });

    const debitEl = document.getElementById('total-debit');
    const creditEl = document.getElementById('total-credit');
    const diffEl = document.getElementById('balance-diff');

    if (debitEl) debitEl.textContent = totalDebit.toFixed(2);
    if (creditEl) creditEl.textContent = totalCredit.toFixed(2);
    if (diffEl) {
        const diff = Math.abs(totalDebit - totalCredit);
        diffEl.textContent = diff.toFixed(2);
        diffEl.style.color = diff === 0 ? '#16A34A' : '#DC2626';
    }
}

// -----------------------------------------------
// Format numbers with Ghanaian Cedi
// -----------------------------------------------
function formatCurrency(amount) {
    return 'GH₵' + new Intl.NumberFormat('en-GH', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(amount);
}
