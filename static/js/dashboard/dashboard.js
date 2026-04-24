// Revenue Chart
let revenueChart;

function initChart(labels, data) {
    const ctx = document.getElementById('revenueChart')?.getContext('2d');
    if (!ctx) return;
    
    revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels || ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            datasets: [{
                label: 'Revenue',
                data: data || [12500, 15000, 18200, 21000],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Update chart based on period
document.getElementById('chartPeriod')?.addEventListener('change', function() {
    const period = this.value;
    let labels, data;
    
    if (period === 'week') {
        labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        data = [2500, 3200, 2800, 4100, 5300, 6200, 4800];
    } else if (period === 'month') {
        labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
        data = [12500, 15000, 18200, 21000];
    } else {
        labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        data = [45000, 52000, 48000, 61000, 72000, 85000, 92000, 88000, 95000, 102000, 115000, 128000];
    }
    
    if (revenueChart) {
        revenueChart.data.labels = labels;
        revenueChart.data.datasets[0].data = data;
        revenueChart.update();
    }
});

// Animate numbers on scroll
function animateNumbers() {
    const numbers = document.querySelectorAll('.stat-card h2, .stat-number');
    numbers.forEach(num => {
        const textValue = num.innerText.replace(/[^0-9.-]+/g, '');
        const finalValue = parseInt(textValue);
        if (!isNaN(finalValue) && finalValue > 0) {
            let current = 0;
            const increment = finalValue / 30;
            const timer = setInterval(() => {
                current += increment;
                if (current >= finalValue) {
                    num.innerText = num.innerText.includes('$') ? '$' + finalValue.toLocaleString() : finalValue.toLocaleString();
                    clearInterval(timer);
                } else {
                    num.innerText = num.innerText.includes('$') ? '$' + Math.floor(current).toLocaleString() : Math.floor(current).toLocaleString();
                }
            }, 30);
        }
    });
}

// Side-bar hover effects and clickability
document.addEventListener('DOMContentLoaded', function() {
    // Add animation delay to stats
    document.querySelectorAll('.stat-card').forEach((card, index) => {
        card.style.animationDelay = `${0.1 * (index + 1)}s`;
    });
    
    // Make action cards clickable
    document.querySelectorAll('.action-card, .stat-card-mini').forEach(card => {
        card.style.cursor = 'pointer';
    });
});
