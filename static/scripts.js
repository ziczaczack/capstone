document.addEventListener('DOMContentLoaded', () => {
    const data = window.MOCK_DATA || {};
    if (!Object.keys(data).length) {
        console.warn('Mock dashboard data missing.');
        return;
    }

    renderSummary(data.summary || {});
    renderInventory(data.inventory || []);
    renderLowStock(data.low_stock || []);
    renderReorder(data.reorder_recommendations || []);
    renderSuppliers(data.suppliers || []);
    renderPurchaseOrders(data.purchase_orders || []);
    renderActivity(data.recent_activity || []);
    renderCharts(data.forecasts || {});
});

function renderSummary(summary) {
    setText('totalItems', formatNumber(summary.total_items));
    setText('stockValue', formatCurrency(summary.stock_value));
    setText('lowStock', formatNumber(summary.low_stock_items));
    setText('pendingOrders', formatNumber(summary.pending_orders));
}

function renderInventory(items) {
    const tbody = document.getElementById('inventoryTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const fragment = document.createDocumentFragment();
    items.forEach(item => {
        const row = document.createElement('tr');
        row.appendChild(createCell(item.id));
        row.appendChild(createCell(item.name));
        row.appendChild(createCell(item.category));
        row.appendChild(createCell(formatQuantity(item.quantity, item.unit)));
        row.appendChild(createCell(formatNumber(item.reorder_level)));
        row.appendChild(createStatusCell(item.status));
        row.appendChild(createCell(item.supplier ?? 'N/A'));
        row.appendChild(createCell(formatDate(item.last_delivery)));
        fragment.appendChild(row);
    });

    tbody.appendChild(fragment);
}

function renderLowStock(alerts) {
    const list = document.getElementById('lowStockList');
    if (!list) return;
    list.innerHTML = '';

    if (!alerts.length) {
        list.appendChild(createEmptyState('All items above reorder points.'));
        return;
    }

    alerts.forEach(entry => {
        const li = document.createElement('li');
        if ((entry.days_until_stockout ?? Infinity) <= 3) {
            li.classList.add('danger');
        }

        const title = document.createElement('p');
        title.className = 'entry-title';
        title.textContent = entry.name;

        const meta = document.createElement('p');
        meta.className = 'entry-meta';
        meta.textContent = `${entry.current_stock} in stock | reorder at ${entry.reorder_level}`;

        const eta = document.createElement('p');
        eta.className = 'entry-meta';
        if (entry.days_until_stockout != null) {
            eta.textContent = `${entry.days_until_stockout} days until stockout | order ${entry.recommended_order}`;
        } else {
            eta.textContent = `Recommended order: ${entry.recommended_order}`;
        }

        li.append(title, meta, eta);
        list.appendChild(li);
    });
}

function renderReorder(recommendations) {
    const list = document.getElementById('reorderList');
    if (!list) return;
    list.innerHTML = '';

    if (!recommendations.length) {
        list.appendChild(createEmptyState('No reorder suggestions at this time.'));
        return;
    }

    recommendations.forEach(entry => {
        const li = document.createElement('li');
        const title = document.createElement('p');
        title.className = 'entry-title';
        title.textContent = entry.supplier;

        const items = document.createElement('p');
        items.className = 'entry-meta';
        items.textContent = `Items: ${(entry.items || []).join(', ')}`;

        const footer = document.createElement('p');
        footer.className = 'entry-meta';
        footer.textContent = `Order by ${formatDate(entry.suggested_date)} | ${formatCurrency(entry.value)}`;

        li.append(title, items, footer);
        list.appendChild(li);
    });
}

function renderSuppliers(suppliers) {
    const tbody = document.getElementById('supplierTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    suppliers.forEach(supplier => {
        const row = document.createElement('tr');
        row.appendChild(createCell(supplier.name));
        row.appendChild(createCell(formatPercent(supplier.on_time_rate)));
        row.appendChild(createCell(formatLeadTime(supplier.avg_lead_time)));
        row.appendChild(createCell(formatDate(supplier.last_order)));
        tbody.appendChild(row);
    });
}

function renderPurchaseOrders(orders) {
    const tbody = document.getElementById('purchaseOrderBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    orders.forEach(order => {
        const row = document.createElement('tr');
        row.appendChild(createCell(order.po_number));
        row.appendChild(createCell(order.supplier));
        row.appendChild(createStatusCell(order.status));
        row.appendChild(createCell(formatDate(order.eta)));
        row.appendChild(createCell(formatCurrency(order.value)));
        tbody.appendChild(row);
    });
}

function renderActivity(entries) {
    const list = document.getElementById('activityList');
    if (!list) return;
    list.innerHTML = '';

    if (!entries.length) {
        list.appendChild(createEmptyState('No recent events in the log.'));
        return;
    }

    entries.forEach(entry => {
        const li = document.createElement('li');
        const title = document.createElement('p');
        title.className = 'entry-title';
        title.textContent = entry.message;

        const meta = document.createElement('p');
        meta.className = 'entry-meta';
        meta.textContent = entry.timestamp;

        li.append(title, meta);
        list.appendChild(li);
    });
}

function renderCharts(forecasts) {
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded; skipping chart render.');
        return;
    }

    const stockConfig = forecasts.stock_levels || {};
    const stockCtx = document.getElementById('stockChart');
    if (stockCtx) {
        new Chart(stockCtx, {
            type: 'line',
            data: {
                labels: stockConfig.labels || [],
                datasets: [
                    {
                        label: 'Actual',
                        data: stockConfig.actual || [],
                        borderColor: '#2b5dff',
                        backgroundColor: 'rgba(43, 93, 255, 0.1)',
                        borderWidth: 3,
                        tension: 0.35,
                        pointRadius: 4
                    },
                    {
                        label: 'Projected',
                        data: stockConfig.projected || [],
                        borderColor: '#ef476f',
                        backgroundColor: 'rgba(239, 71, 111, 0.08)',
                        borderDash: [6, 6],
                        borderWidth: 3,
                        tension: 0.35,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                plugins: {
                    legend: { align: 'end' }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: { color: '#4c4f64' }
                    },
                    x: {
                        ticks: { color: '#4c4f64' }
                    }
                }
            }
        });
    }

    const topConfig = forecasts.top_products || {};
    const topCtx = document.getElementById('topProductsChart');
    if (topCtx) {
        new Chart(topCtx, {
            type: 'bar',
            data: {
                labels: topConfig.labels || [],
                datasets: [
                    {
                        label: 'Units Sold',
                        data: topConfig.values || [],
                        backgroundColor: '#2ec4b6'
                    }
                ]
            },
            options: {
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#4c4f64' }
                    },
                    x: {
                        ticks: { color: '#4c4f64' }
                    }
                }
            }
        });
    }
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = value;
}

function createCell(value) {
    const td = document.createElement('td');
    td.textContent = value == null || value === '' ? 'N/A' : value;
    return td;
}

function createStatusCell(status) {
    const td = document.createElement('td');
    if (!status) {
        td.textContent = 'N/A';
        return td;
    }

    const normalized = String(status).toLowerCase();
    const span = document.createElement('span');
    span.classList.add('status-chip');

    if (normalized.includes('critical') || normalized.includes('out')) {
        span.classList.add('status-critical');
    } else if (normalized.includes('low') || normalized.includes('await')) {
        span.classList.add('status-low');
    } else if (normalized.includes('transit')) {
        span.classList.add('status-in-transit');
    } else if (normalized.includes('receiv')) {
        span.classList.add('status-received');
    } else {
        span.classList.add('status-in-stock');
    }

    span.textContent = status;
    td.appendChild(span);
    return td;
}

function createEmptyState(message) {
    const li = document.createElement('li');
    li.classList.add('empty-state');
    li.textContent = message;
    return li;
}

function formatCurrency(value) {
    if (value == null) {
        return 'N/A';
    }
    const amount = Number(value);
    if (Number.isNaN(amount)) {
        return 'N/A';
    }
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(amount);
}

function formatQuantity(quantity, unit) {
    if (quantity == null) {
        return 'N/A';
    }
    const numeric = Number(quantity);
    if (Number.isNaN(numeric)) {
        return unit ? `${quantity} ${unit}` : `${quantity}`;
    }
    const formatted = numeric.toLocaleString('en-US');
    return unit ? `${formatted} ${unit}` : formatted;
}

function formatDate(input) {
    if (!input) {
        return 'N/A';
    }
    const date = new Date(input);
    if (Number.isNaN(date.getTime())) {
        return input;
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatPercent(value) {
    const num = Number(value);
    if (Number.isNaN(num)) {
        return 'N/A';
    }
    return `${Math.round(num * 100)}%`;
}

function formatLeadTime(value) {
    const num = Number(value);
    if (Number.isNaN(num)) {
        return 'N/A';
    }
    return `${num} day${num === 1 ? '' : 's'}`;
}

function formatNumber(value) {
    if (value == null) {
        return 'N/A';
    }
    const num = Number(value);
    if (Number.isNaN(num)) {
        return 'N/A';
    }
    return num.toLocaleString('en-US');
}
