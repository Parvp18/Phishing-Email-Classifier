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

    // Map features to 6 threat risk axes (0 = safe / low threat, 100 = critical threat)
    // 1. URL Risk: count, IP usage, obfuscation, and lookalike domains
    const urlRisk = Math.min(100, 
        (features.url_count ? 25 : 0) + 
        (features.url_count || 0) * 10 + 
        (features.has_ip_in_url ? 35 : 0) + 
        (features.obfuscated_url ? 25 : 0) +
        (features.misspelled_brand ? 30 : 0)
    );

    // 2. Keyword & Intent Risk: urgent trigger words and login form triggers
    const keywordRisk = Math.min(100, 
        (features.urgent_keyword_count || 0) * 20 + 
        (features.has_login_form_words ? 35 : 0)
    );

    // 3. Domain Risk (Mismatch & Impersonation)
    const domainTrust = Math.min(100,
        (features.misspelled_brand ? 60 : 0) + 
        (features.sender_domain_mismatch ? 40 : 0) +
        (features.unique_domain_count > 2 ? 20 : 0)
    );

    // 4. Format Risk: HTML tags, aggressive capitalization, suspicious characters
    const formatRisk = Math.min(100, 
        (features.html_tag_count || 0) * 5 + 
        Math.round((features.capital_ratio || 0) * 200) +
        (features.at_symbol_count || 0) * 20
    );

    // 5. Sender Auth Risk (SPF/DKIM/Domain Mismatch)
    // Only flag risk if explicit SPF/DKIM failures exist or sender domain mismatch is detected
    let senderRisk = 0;
    if (features.spf_pass === false) senderRisk += 40;
    if (features.dkim_pass === false) senderRisk += 40;
    if (features.sender_domain_mismatch) senderRisk += 40;
    senderRisk = Math.min(100, senderRisk);

    // 6. Urgency Risk: urgent keywords + subject/text exclamations
    const urgencyRisk = Math.min(100, 
        (features.urgent_keyword_count || 0) * 25 + 
        (features.exclamation_count || 0) * 15 + 
        (features.subj_exclamations || 0) * 30
    );

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
