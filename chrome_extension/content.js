console.log("PhishGuard Content Script Loaded");

let currentScannedEmailId = null;

// Observe DOM for Gmail email view changes
const observer = new MutationObserver((mutations) => {
    // A simple heuristic for Gmail: when an element with role="main" or the email body area updates
    // In actual production, we'd use InboxSDK or a more robust selector.
    // For this prototype, we check if an email body exists and hasn't been scanned.
    const emailBodies = document.querySelectorAll('.a3s.aiL');
    
    if (emailBodies.length > 0) {
        const body = emailBodies[0];
        // Unique ID could be based on a hidden attribute or text hash
        const emailText = body.innerText;
        const emailId = btoa(emailText.substring(0, 100)); // crude hash

        if (currentScannedEmailId !== emailId && emailText.length > 20) {
            currentScannedEmailId = emailId;
            
            // Extract Subject and Sender
            const subjectEl = document.querySelector('h2.hP');
            const subject = subjectEl ? subjectEl.innerText : '';
            
            const senderEl = document.querySelector('.gD');
            const sender = senderEl ? senderEl.getAttribute('email') || senderEl.innerText : '';

            chrome.storage.local.get(['phishguard_enabled', 'phishguard_api_key', 'phishguard_endpoint'], (res) => {
                if (res.phishguard_enabled) {
                    analyzeEmail(emailText, subject, sender, res.phishguard_api_key, res.phishguard_endpoint, body);
                }
            });
        }
    }
});

// Start observing
observer.observe(document.body, { childList: true, subtree: true });

async function analyzeEmail(text, subject, sender, apiKey, endpoint, bodyEl) {
    // Inject Loading Badge
    const headerContainer = document.querySelector('.gE.iv.gt') || bodyEl.parentElement;
    if (!headerContainer) return;

    let badge = document.getElementById('phishguard_badge');
    if (!badge) {
        badge = document.createElement('div');
        badge.id = 'phishguard_badge';
        badge.style.display = 'inline-block';
        badge.style.padding = '4px 8px';
        badge.style.borderRadius = '12px';
        badge.style.marginLeft = '10px';
        badge.style.fontSize = '12px';
        badge.style.fontWeight = 'bold';
        badge.style.color = '#fff';
        badge.style.backgroundColor = '#6c63ff';
        badge.style.cursor = 'help';
        headerContainer.appendChild(badge);
    }
    
    badge.innerText = "PhishGuard: Scanning...";
    badge.style.backgroundColor = '#6c63ff';

    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey
            },
            body: JSON.stringify({ email_text: text, subject: subject, sender: sender })
        });

        if (res.ok) {
            const data = await res.json();
            
            // Save last result for popup
            chrome.storage.local.set({ last_scan: data });

            if (data.label === 'PHISHING') {
                badge.innerText = `Phishing ${data.confidence}%`;
                badge.style.backgroundColor = '#ef4444';
            } else {
                badge.innerText = `Safe ${data.confidence}%`;
                badge.style.backgroundColor = '#22c55e';
            }

            // Build tooltip
            const topFactors = data.shap_top_features.slice(0, 3).map(f => f.feature).join(', ');
            badge.title = `Risk: ${data.risk_level}\nTop Factors: ${topFactors || 'None'}`;
            
        } else {
            badge.innerText = "PhishGuard: Error";
            badge.style.backgroundColor = '#f59e0b';
        }
    } catch (e) {
        console.error("PhishGuard Analysis Failed", e);
        badge.innerText = "PhishGuard: Offline";
        badge.style.backgroundColor = '#64748b';
    }
}
