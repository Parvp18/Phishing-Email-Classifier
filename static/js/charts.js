/**
 * PhishGuard Charts Module
 * Handles Chart.js initializations for the radar chart and dashboard.
 */

// Radar Chart for Analysis Results
let radarChartInstance = null;

function renderRadarChart(features) {
    const ctx = document.getElementById('radarChart');
    if (!ctx) return;

    if (radarChartInstance) {
        radarChartInstance.destroy();
    }

    // Map features to 6 risk axes
    // This is a heuristic mapping for visual effect based on the features available
    const urlRisk = Math.min(100, (features.url_count || 0) * 10 + (features.has_ip_in_url ? 40 : 0) + (features.obfuscated_url ? 30 : 0));
    const keywordRisk = Math.min(100, (features.urgent_keyword_count || 0) * 15 + (features.has_login_form_words ? 30 : 0));
    const domainTrust = features.misspelled_brand ? 100 : (features.sender_domain_mismatch ? 80 : 20); // Inverted: High value = bad trust
    const formatRisk = Math.min(100, (features.html_tag_count || 0) * 2 + (features.capital_ratio || 0) * 100);
    const senderRisk = Math.min(100, (features.spf_pass ? 0 : 50) + (features.dkim_pass ? 0 : 50));
    const urgencyRisk = Math.min(100, (features.exclamation_count || 0) * 10 + (features.subj_exclamations || 0) * 20);

    const data = {
        labels: ['URL Risk', 'Keywords', 'Domain Trust', 'Format Risk', 'Sender Auth', 'Urgency'],
        datasets: [{
            label: 'Threat Profile',
            data: [urlRisk, keywordRisk, domainTrust, formatRisk, senderRisk, urgencyRisk],
            backgroundColor: 'rgba(239, 68, 68, 0.2)',
            borderColor: 'rgba(239, 68, 68, 1)',
            pointBackgroundColor: 'rgba(239, 68, 68, 1)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgba(239, 68, 68, 1)'
        }]
    };

    const config = {
        type: 'radar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(226, 232, 240, 1)' },
                    grid: { color: 'rgba(226, 232, 240, 1)' },
                    pointLabels: { color: '#475569', font: { size: 12, family: 'Plus Jakarta Sans, Inter, sans-serif', weight: '600' } },
                    ticks: { display: false, min: 0, max: 100 }
                }
            },
            plugins: {
                legend: { display: false }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    };

    radarChartInstance = new Chart(ctx, config);
}

// Global scope expose
window.renderRadarChart = renderRadarChart;
