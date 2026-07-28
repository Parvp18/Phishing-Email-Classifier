/**
 * PhishGuard Threat Simulator Module
 * Real-time client-side ML risk score simulation laboratory.
 */

function runThreatSimulation() {
    const urgentCount = parseInt(document.getElementById('sim_urgent_words')?.value || '0', 10);
    const lookalike = document.getElementById('sim_lookalike')?.checked || false;
    const spfPass = document.getElementById('sim_spf')?.checked || false;
    const dkimPass = document.getElementById('sim_dkim')?.checked || false;
    const loginForm = document.getElementById('sim_login')?.checked || false;
    const exclamations = parseInt(document.getElementById('sim_exclamations')?.value || '0', 10);

    // Update label displays
    if (document.getElementById('sim_urgent_val')) document.getElementById('sim_urgent_val').innerText = urgentCount;
    if (document.getElementById('sim_excl_val')) document.getElementById('sim_excl_val').innerText = exclamations;

    // Calculate heuristic risk score
    let score = 5; // base baseline score

    score += urgentCount * 12;
    if (lookalike) score += 35;
    if (!spfPass) score += 20;
    if (!dkimPass) score += 15;
    if (loginForm) score += 25;
    score += exclamations * 3;

    score = Math.min(99, Math.max(1, score));

    // Update UI elements
    const meterFill = document.getElementById('sim_meter_fill');
    const scoreVal = document.getElementById('sim_score_val');
    const verdictBadge = document.getElementById('sim_verdict_badge');

    if (scoreVal) scoreVal.innerText = `${score}% Risk`;

    if (meterFill) {
        meterFill.style.width = `${score}%`;
        if (score >= 65) {
            meterFill.style.backgroundColor = '#dc2626';
        } else if (score >= 35) {
            meterFill.style.backgroundColor = '#d97706';
        } else {
            meterFill.style.backgroundColor = '#16a34a';
        }
    }

    if (verdictBadge) {
        if (score >= 60) {
            verdictBadge.className = 'pill red';
            verdictBadge.innerText = 'HIGH RISK PHISHING';
        } else if (score >= 30) {
            verdictBadge.className = 'pill yellow';
            verdictBadge.innerText = 'SUSPICIOUS WARNING';
        } else {
            verdictBadge.className = 'pill green';
            verdictBadge.innerText = 'SAFE EMAIL';
        }
    }

    // Model Consensus Simulation
    const nbProb = Math.min(0.99, Math.max(0.01, score / 100 + 0.05));
    const rfProb = Math.min(0.99, Math.max(0.01, score / 100 - 0.02));
    const xgbProb = Math.min(0.99, Math.max(0.01, score / 100 + 0.01));

    if (document.getElementById('sim_nb_prob')) document.getElementById('sim_nb_prob').innerText = `${Math.round(nbProb * 100)}%`;
    if (document.getElementById('sim_rf_prob')) document.getElementById('sim_rf_prob').innerText = `${Math.round(rfProb * 100)}%`;
    if (document.getElementById('sim_xgb_prob')) document.getElementById('sim_xgb_prob').innerText = `${Math.round(xgbProb * 100)}%`;
}

// Global scope export
window.runThreatSimulation = runThreatSimulation;

// Auto initialize when tab is clicked
document.addEventListener('DOMContentLoaded', () => {
    runThreatSimulation();
});
