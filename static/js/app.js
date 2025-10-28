// Global state
let currentDate = null;
let currentZScore = 3.0;
let volumeChart = null;
let priceChart = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadAnomalies();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('prev-date').addEventListener('click', () => navigateDate(-1));
    document.getElementById('next-date').addEventListener('click', () => navigateDate(1));
    document.getElementById('date-input').addEventListener('change', (e) => {
        currentDate = e.target.value;
        loadAnomalies();
    });
    document.getElementById('apply-filter').addEventListener('click', () => {
        currentZScore = parseFloat(document.getElementById('z-score-filter').value);
        loadAnomalies();
    });
    
    // Modal close
    document.querySelector('.close').addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            closeModal();
        }
    });
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        document.getElementById('latest-date').textContent = data.latest_date || 'N/A';
        document.getElementById('anomaly-count').textContent = data.anomaly_count_today || 0;
        document.getElementById('total-tickers').textContent = data.total_tickers.toLocaleString();
        document.getElementById('total-anomalies').textContent = data.total_anomalies.toLocaleString();
        
        if (data.latest_date && !currentDate) {
            currentDate = data.latest_date;
            document.getElementById('date-input').value = currentDate;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load anomalies
async function loadAnomalies() {
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const list = document.getElementById('anomalies-list');
    
    loading.style.display = 'block';
    error.style.display = 'none';
    list.innerHTML = '';
    
    try {
        const params = new URLSearchParams();
        if (currentDate) params.append('date', currentDate);
        if (currentZScore) params.append('min_z_score', currentZScore);
        
        const response = await fetch(`/api/anomalies?${params}`);
        const data = await response.json();
        
        loading.style.display = 'none';
        
        if (data.anomalies.length === 0) {
            list.innerHTML = '<div class="loading">No anomalies found for this date.</div>';
            return;
        }
        
        currentDate = data.date;
        document.getElementById('date-input').value = currentDate;
        
        data.anomalies.forEach(anomaly => {
            const card = createAnomalyCard(anomaly);
            list.appendChild(card);
        });
        
    } catch (err) {
        loading.style.display = 'none';
        error.style.display = 'block';
        error.textContent = `Error loading anomalies: ${err.message}`;
    }
}

// Create anomaly card
function createAnomalyCard(anomaly) {
    const card = document.createElement('div');
    card.className = 'anomaly-card';
    card.onclick = () => showDetails(anomaly.ticker, anomaly.date);
    
    const priceChangeClass = anomaly.price_diff >= 0 ? 'positive' : 'negative';
    const priceChangeSymbol = anomaly.price_diff >= 0 ? '+' : '';
    
    card.innerHTML = `
        <div class="anomaly-header">
            <div class="ticker-name">${anomaly.ticker}</div>
            <div class="z-score-badge">Z-Score: ${anomaly.z_score.toFixed(2)}</div>
        </div>
        <div class="anomaly-metrics">
            <div class="metric">
                <div class="metric-label">Trades</div>
                <div class="metric-value">${anomaly.trades.toLocaleString()}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Trades (5d)</div>
                <div class="metric-value">${anomaly.avg_trades.toLocaleString()}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Price Change</div>
                <div class="metric-value ${priceChangeClass}">
                    ${priceChangeSymbol}${anomaly.price_diff.toFixed(2)}%
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Close Price</div>
                <div class="metric-value">$${anomaly.close_price.toFixed(2)}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Volume</div>
                <div class="metric-value">${(anomaly.volume || 0).toLocaleString()}</div>
            </div>
        </div>
    `;
    
    return card;
}

// Navigate dates
function navigateDate(direction) {
    if (!currentDate) return;
    
    const date = new Date(currentDate);
    date.setDate(date.getDate() + direction);
    
    // Skip weekends
    while (date.getDay() === 0 || date.getDay() === 6) {
        date.setDate(date.getDate() + direction);
    }
    
    currentDate = date.toISOString().split('T')[0];
    document.getElementById('date-input').value = currentDate;
    loadAnomalies();
}

// Show details modal
async function showDetails(ticker, date) {
    const modal = document.getElementById('detail-modal');
    const modalLoading = document.getElementById('modal-loading');
    const modalBody = document.getElementById('modal-body');
    
    document.getElementById('modal-ticker').textContent = ticker;
    modal.style.display = 'block';
    modalLoading.style.display = 'block';
    modalBody.style.display = 'none';
    
    try {
        const response = await fetch(`/api/ticker/${ticker}?date=${date}`);
        const data = await response.json();
        
        modalLoading.style.display = 'none';
        modalBody.style.display = 'block';
        
        // Populate details
        const anomaly = data.anomaly;
        document.getElementById('detail-date').textContent = anomaly.date;
        document.getElementById('detail-trades').textContent = anomaly.trades.toLocaleString();
        document.getElementById('detail-avg-trades').textContent = anomaly.avg_trades.toLocaleString();
        document.getElementById('detail-z-score').textContent = anomaly.z_score.toFixed(2);
        
        const priceChangeClass = anomaly.price_diff >= 0 ? 'positive' : 'negative';
        const priceChangeSymbol = anomaly.price_diff >= 0 ? '+' : '';
        document.getElementById('detail-price-change').innerHTML = 
            `<span class="${priceChangeClass}">${priceChangeSymbol}${anomaly.price_diff.toFixed(2)}%</span>`;
        document.getElementById('detail-close-price').textContent = `$${anomaly.close_price.toFixed(2)}`;
        
        // Create charts
        createVolumeChart(data.historical);
        createPriceChart(data.historical);
        
    } catch (error) {
        modalLoading.style.display = 'none';
        modalBody.innerHTML = `<div class="error">Error loading details: ${error.message}</div>`;
        modalBody.style.display = 'block';
    }
}

// Close modal
function closeModal() {
    document.getElementById('detail-modal').style.display = 'none';
    if (volumeChart) volumeChart.destroy();
    if (priceChart) priceChart.destroy();
}

// Create volume chart
function createVolumeChart(historical) {
    const ctx = document.getElementById('volume-chart');
    
    if (volumeChart) volumeChart.destroy();
    
    const dates = historical.map(h => h.date);
    const volumes = historical.map(h => h.volume || 0);
    const transactions = historical.map(h => h.transactions || 0);
    
    volumeChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Volume',
                    data: volumes,
                    backgroundColor: 'rgba(102, 126, 234, 0.5)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Transactions',
                    data: transactions,
                    type: 'line',
                    borderColor: 'rgba(239, 68, 68, 1)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Volume'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Transactions'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

// Create price chart
function createPriceChart(historical) {
    const ctx = document.getElementById('price-chart');
    
    if (priceChart) priceChart.destroy();
    
    const dates = historical.map(h => h.date);
    const prices = historical.map(h => h.close);
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Close Price',
                data: prices,
                borderColor: 'rgba(16, 185, 129, 1)',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Price ($)'
                    }
                }
            }
        }
    });
}

