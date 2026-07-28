/**
 * PhishGuard Main Frontend Logic
 * Handles tab switching, form submission, API calls, and rendering results.
 */

const API_KEY = "your-secret-key-1"; // For demo purposes. In prod, use real auth/session.

document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.add('hidden'));

            // Add active class
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.remove('hidden');
        });
    });

    // Character counter for Paste Email
    const emailInput = document.getElementById('email_text');
    const charCount = document.getElementById('char_count');
    if (emailInput && charCount) {
        emailInput.addEventListener('input', () => {
            charCount.textContent = emailInput.value.length;
        });

        // Ctrl+Enter to submit
        emailInput.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                analyzePaste();
            }
        });
    }

    // Drag and drop for file upload
    const fileDrop = document.getElementById('file_drop');
    const fileInput = document.getElementById('eml_file');
    if (fileDrop && fileInput) {
        fileDrop.addEventListener('click', () => fileInput.click());

        fileDrop.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileDrop.classList.add('dragover');
        });

        fileDrop.addEventListener('dragleave', () => {
            fileDrop.classList.remove('dragover');
        });

        fileDrop.addEventListener('drop', (e) => {
            e.preventDefault();
            fileDrop.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                updateFileDropLabel(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                updateFileDropLabel(fileInput.files[0]);
            }
        });
    }
    // Drag and drop for bulk upload
    const bulkDrop = document.getElementById('bulk_drop');
    const csvInput = document.getElementById('csv_file');
    if (bulkDrop && csvInput) {
        bulkDrop.addEventListener('click', () => csvInput.click());

        bulkDrop.addEventListener('dragover', (e) => {
            e.preventDefault();
            bulkDrop.classList.add('dragover');
        });

        bulkDrop.addEventListener('dragleave', () => {
            bulkDrop.classList.remove('dragover');
        });

        bulkDrop.addEventListener('drop', (e) => {
            e.preventDefault();
            bulkDrop.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                csvInput.files = e.dataTransfer.files;
                updateCsvDropLabel(e.dataTransfer.files[0]);
            }
        });

        csvInput.addEventListener('change', () => {
            if (csvInput.files.length) {
                updateCsvDropLabel(csvInput.files[0]);
            }
        });
    }
});

function updateFileDropLabel(file) {
    const label = document.getElementById('file_name_label');
    if (label) {
        const size = (file.size / 1024).toFixed(1);
        label.textContent = `${file.name} (${size} KB)`;
    }
}

function updateCsvDropLabel(file) {
    const label = document.getElementById('csv_name_label');
    if (label) {
        const size = (file.size / 1024).toFixed(1);
        label.textContent = `${file.name} (${size} KB)`;
    }
}

function showLoading() {
    document.getElementById('loading_overlay').classList.remove('hidden');
    document.getElementById('results_section').classList.add('hidden');
}

function hideLoading() {
    document.getElementById('loading_overlay').classList.add('hidden');
}

function showError(msg) {
    alert("Error: " + msg);
}

// -----------------------------------------------------------------------------
// API Calls
// -----------------------------------------------------------------------------

async function analyzePaste() {
    const text = document.getElementById('email_text').value;
    const subject = document.getElementById('email_subject').value;
    const sender = document.getElementById('email_sender').value;

    if (!text) {
        alert("Please paste email text.");
        return;
    }

    showLoading();

    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({ email_text: text, subject, sender })
        });

        const rawText = await res.text();
        let data;
        try {
            data = JSON.parse(rawText);
        } catch (err) {
            hideLoading();
            showError(`Server response (${res.status}): ${rawText || res.statusText}`);
            return;
        }
        hideLoading();

        if (res.ok) {
            renderResults(data);
        } else {
            showError(data.error || "Unknown error occurred.");
        }
    } catch (e) {
        hideLoading();
        showError(e.message);
    }
}

async function analyzeFile() {
    const fileInput = document.getElementById('eml_file');
    if (!fileInput.files.length) {
        alert("Please select a file.");
        return;
    }

    showLoading();
    const formData = new FormData();
    formData.append('email_file', fileInput.files[0]);

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            headers: { 'X-API-Key': API_KEY },
            body: formData
        });

        const rawText = await res.text();
        let data;
        try {
            data = JSON.parse(rawText);
        } catch (err) {
            hideLoading();
            showError(`Server response (${res.status}): ${rawText || res.statusText}`);
            return;
        }
        hideLoading();

        if (res.ok) {
            renderResults(data);
        } else {
            showError(data.error);
        }
    } catch (e) {
        hideLoading();
        showError(e.message);
    }
}

// -----------------------------------------------------------------------------
// Result Rendering
// -----------------------------------------------------------------------------

function renderResults(data) {
    const resultsSec = document.getElementById('results_section');
    resultsSec.classList.remove('hidden');

    // Scroll to results
    resultsSec.scrollIntoView({ behavior: 'smooth' });

    // Verdict Banner
    const banner = document.getElementById('verdict_banner');
    const verdictIcon = document.getElementById('verdict_icon');
    const verdictText = document.getElementById('verdict_text');
    const confBadge = document.getElementById('verdict_conf');

    if (data.label === 'PHISHING') {
        banner.className = 'verdict-banner phishing';
        verdictIcon.innerHTML = '⚠️';
        verdictText.textContent = 'Threat Detected';
    } else {
        banner.className = 'verdict-banner safe';
        verdictIcon.innerHTML = '✅';
        verdictText.textContent = 'Email Appears Safe';
    }
    confBadge.textContent = `${data.confidence}% Confidence | ${data.risk_level} Risk`;

    // Models
    document.getElementById('nb_label').textContent = data.model_votes.naive_bayes.label;
    document.getElementById('nb_conf').textContent = `${data.model_votes.naive_bayes.confidence}%`;
    document.getElementById('rf_label').textContent = data.model_votes.random_forest.label;
    document.getElementById('rf_conf').textContent = `${data.model_votes.random_forest.confidence}%`;
    document.getElementById('xgb_label').textContent = data.model_votes.xgboost.label;
    document.getElementById('xgb_conf').textContent = `${data.model_votes.xgboost.confidence}%`;
    document.getElementById('ens_label').textContent = data.model_votes.ensemble.label;
    document.getElementById('ens_conf').textContent = `${data.model_votes.ensemble.confidence}%`;

    // Radar Chart
    if (window.renderRadarChart) {
        window.renderRadarChart(data.features);
    }

    // Heatmap
    const heatmapBox = document.getElementById('heatmap_box');
    heatmapBox.innerHTML = '';
    data.word_heatmap.forEach(item => {
        const span = document.createElement('span');
        span.textContent = item.word + ' ';
        span.className = 'heatmap-word';
        if (item.score > 0) {
            // map score 0-1 to red intensity
            const intensity = Math.floor(item.score * 255);
            span.style.backgroundColor = `rgba(239, 68, 68, ${item.score * 0.8})`;
            if (item.score > 0.5) span.style.color = '#fff';
            span.setAttribute('data-tooltip', `SHAP Score: ${item.score.toFixed(2)}`);
        }
        heatmapBox.appendChild(span);
    });

    // Features
    const featGrid = document.getElementById('feature_grid');
    featGrid.innerHTML = '';
    
    // Top SHAP
    data.shap_top_features.forEach(f => {
        featGrid.innerHTML += `
            <div class="feature-item">
                <span>${f.feature}</span>
                <span class="pill ${f.contribution > 0 ? 'red' : 'green'}">${f.contribution > 0 ? '+' : ''}${f.contribution}</span>
            </div>
        `;
    });

    // Attack Type
    const attackBadge = document.getElementById('attack_type_badge');
    attackBadge.textContent = `${data.attack_type} (${data.attack_type_confidence}%)`;

    // Recommendation
    document.getElementById('recommendation_text').textContent = data.recommendation;

    // URLs Table
    const tbody = document.getElementById('urls_tbody');
    tbody.innerHTML = '';
    if (data.urls_found.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4">No URLs found in email.</td></tr>';
    } else {
        data.urls_found.forEach(u => {
            tbody.innerHTML += `
                <tr>
                    <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;">${u.url}</td>
                    <td>${u.virustotal_score}</td>
                    <td>${u.domain_age_days}</td>
                    <td>${u.is_lookalike ? '<span class="pill red">Yes</span>' : 'No'}</td>
                </tr>
            `;
        });
    }

    // Download Report Link
    const dlBtn = document.getElementById('download_report_btn');
    dlBtn.onclick = () => {
        window.open(`/api/report/${data.id}?X-API-Key=${API_KEY}`, '_blank');
    };
}

// -----------------------------------------------------------------------------
// Bulk Scanning Logic
// -----------------------------------------------------------------------------

window.lastBulkResults = [];

async function analyzeBulk() {
    const fileInput = document.getElementById('csv_file');
    if (!fileInput.files.length) {
        alert("Please select a CSV file.");
        return;
    }

    showLoading();
    const formData = new FormData();
    formData.append('csv_file', fileInput.files[0]);

    try {
        const res = await fetch('/api/bulk', {
            method: 'POST',
            headers: { 'X-API-Key': API_KEY },
            body: formData
        });

        const rawText = await res.text();
        let data;
        try {
            data = JSON.parse(rawText);
        } catch (err) {
            hideLoading();
            showError(`Server response (${res.status}): ${rawText || res.statusText}`);
            return;
        }
        hideLoading();

        if (res.ok) {
            renderBulkResults(data);
        } else {
            showError(data.error);
        }
    } catch (e) {
        hideLoading();
        showError(e.message);
    }
}

function renderBulkResults(data) {
    document.getElementById('results_section').classList.add('hidden');
    window.lastBulkResults = data.results;
    
    let bulkSec = document.getElementById('bulk_results_section');
    if (!bulkSec) {
        bulkSec = document.createElement('div');
        bulkSec.id = 'bulk_results_section';
        bulkSec.className = 'results-container';
        document.querySelector('.main-content').appendChild(bulkSec);
    }
    bulkSec.classList.remove('hidden');
    
    const sum = data.summary;
    let html = `
        <div class="card" style="margin-bottom: 2rem;">
            <h2>Bulk Scan Summary</h2>
            <div style="display: flex; gap: 2rem; margin-top: 1rem;">
                <div><strong>Total Processed:</strong> ${sum.total_processed}</div>
                <div style="color: var(--danger);"><strong>Phishing Found:</strong> ${sum.phishing_found}</div>
                <div style="color: var(--success);"><strong>Safe Found:</strong> ${sum.safe_found}</div>
            </div>
        </div>
        <div class="card">
            <h3 style="margin-bottom: 1rem;">Detailed Results</h3>
            <div style="overflow-x: auto; max-height: 400px; overflow-y: auto;">
                <table class="urls-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Label</th>
                            <th>Confidence</th>
                            <th>Attack Type</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id="bulk_tbody">
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    bulkSec.innerHTML = html;
    
    const tbody = document.getElementById('bulk_tbody');
    data.results.forEach((r, idx) => {
        const isPhishing = r.label === 'PHISHING';
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${r.original_id}</td>
            <td><span class="pill ${isPhishing ? 'red' : 'green'}">${r.label}</span></td>
            <td>${r.confidence}%</td>
            <td>${r.attack_type || '-'}</td>
            <td><button class="btn-demo" data-idx="${idx}">View</button></td>
        `;
        tbody.appendChild(tr);
    });
    
    // Add event listeners to buttons
    const btns = tbody.querySelectorAll('.btn-demo');
    btns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const idx = e.target.getAttribute('data-idx');
            showSingleResult(window.lastBulkResults[idx]);
        });
    });

    bulkSec.scrollIntoView({ behavior: 'smooth' });
}

window.showSingleResult = function(resData) {
    const bulkSec = document.getElementById('bulk_results_section');
    if (bulkSec) bulkSec.classList.add('hidden');
    renderResults(resData);
};
