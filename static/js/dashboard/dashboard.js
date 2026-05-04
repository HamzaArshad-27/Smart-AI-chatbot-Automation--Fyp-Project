// ============================================
// VENDORA 2.0 - Dashboard Interactions
// ============================================

let revenueChart;

// Initialize Chart
function initChart(labels, data) {
    const ctx = document.getElementById('revenueChart')?.getContext('2d');
    if (!ctx) return;
    
    Chart.defaults.color = '#737373';
    Chart.defaults.borderColor = '#e5e5e5';
    Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(91, 95, 227, 0.12)');
    gradient.addColorStop(1, 'rgba(91, 95, 227, 0)');
    
    revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels || ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            datasets: [{
                label: 'Revenue',
                data: data || [12500, 18200, 15600, 24500],
                borderColor: '#5b5fe3',
                backgroundColor: gradient,
                borderWidth: 3,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#ffffff',
                pointBorderColor: '#5b5fe3',
                pointBorderWidth: 3,
                pointRadius: 6,
                pointHoverRadius: 9,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    labels: {
                        usePointStyle: true,
                        pointStyleWidth: 8,
                        padding: 20,
                        font: { size: 12, weight: '600' }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#f5f5f5' },
                    ticks: {
                        callback: value => '$' + value.toLocaleString()
                    }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

// Chart Period Toggle
document.getElementById('chartPeriod')?.addEventListener('change', function() {
    const dataMap = {
        week: { labels: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], data: [3200,4500,3800,5200,6800,7900,6100] },
        month: { labels: ['W1','W2','W3','W4'], data: [15800,19200,23500,28600] },
        year: { labels: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], data: [52,61,58,72,85,98,105,102,112,125,138,152].map(v => v*1000) }
    };
    
    const selected = dataMap[this.value];
    if (revenueChart && selected) {
        revenueChart.data.labels = selected.labels;
        revenueChart.data.datasets[0].data = selected.data;
        revenueChart.update();
    }
});

// Smooth Counter Animation
function animateCounters() {
    document.querySelectorAll('.stat-card h2, .stat-number').forEach(el => {
        const text = el.innerText.replace(/[^0-9.-]/g, '');
        const target = parseFloat(text);
        if (isNaN(target)) return;
        
        const isCurrency = el.innerText.includes('$');
        const duration = 1200;
        let start = null;
        
        function step(timestamp) {
            if (!start) start = timestamp;
            const progress = Math.min((timestamp - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = target * eased;
            
            el.innerText = isCurrency 
                ? '$' + Math.floor(current).toLocaleString() 
                : Math.floor(current).toLocaleString();
            
            if (progress < 1) requestAnimationFrame(step);
            else el.innerText = isCurrency 
                ? '$' + target.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})
                : target.toLocaleString();
        }
        
        requestAnimationFrame(step);
    });
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('revenueChart') && !revenueChart) initChart();
    setTimeout(animateCounters, 200);
});