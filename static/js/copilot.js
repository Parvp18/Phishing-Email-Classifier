/**
 * PhishGuard Cyber Copilot Module
 * Provides instant AI-like security advice, Q&A, and response templates.
 */

const COPILOT_KNOWLEDGE = [
    {
        keywords: ['spf', 'dkim', 'authentication', 'header', 'spoof'],
        response: `🛡️ **Sender Authentication Analysis:**\n\n- **SPF (Sender Policy Framework):** Validates if the sending mail server IP is authorized by the domain's DNS records.\n- **DKIM (DomainKeys Identified Mail):** Uses cryptographic signatures to ensure email body content was not tampered with in transit.\n\n*Security Recommendation:* If SPF or DKIM fails, quarantine the message immediately as it indicates domain spoofing.`
    },
    {
        keywords: ['lookalike', 'typosquatting', 'domain', 'fake', 'paypal', 'google', 'microsoft', 'apple', 'amazon'],
        response: `⚠️ **Lookalike & Typosquatting Detection:**\n\nAttackers often use visually similar characters (e.g. \`paypa1.com\` or \`micros0ft-security.com\`) to trick victims.\n\n*Action Steps:*\n1. Check the domain extension closely.\n2. Do NOT click links inside the email.\n3. Navigate directly to the official website by typing the URL manually.`
    },
    {
        keywords: ['report', 'soc', 'helpdesk', 'it', 'incident', 'ticket'],
        response: `📋 **SOC Incident Reporting Procedure:**\n\n1. Use the **"Copy SOC Incident Report"** button below any completed scan.\n2. Paste the formatted incident ticket into your organization's Helpdesk / Jira / Service-Now queue.\n3. Include the original \`.eml\` file as an attachment if submitting to Security Analysis.`
    },
    {
        keywords: ['safe', 'verify', 'draft', 'reply', 'respond'],
        response: `✉️ **Safe Response Template for Suspicious Emails:**\n\n*"Dear [Sender Name],\n\nWe received an email claiming to be from your organization regarding [Subject]. To protect our network security, please confirm this request through an official secondary communication channel (phone/company portal).\n\nThank you,\nIT Security Team"*`
    }
];

function sendCopilotMessage() {
    const inputEl = document.getElementById('copilot_input');
    const chatContainer = document.getElementById('copilot_chat');
    if (!inputEl || !chatContainer) return;

    const query = inputEl.value.trim();
    if (!query) return;

    // Append User Message
    const userMsg = document.createElement('div');
    userMsg.className = 'chat-msg user';
    userMsg.innerHTML = `<strong>You:</strong> ${escapeHTML(query)}`;
    chatContainer.appendChild(userMsg);

    inputEl.value = '';
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Simulate instant AI analysis
    setTimeout(() => {
        const botMsg = document.createElement('div');
        botMsg.className = 'chat-msg bot';
        
        const qLower = query.toLowerCase();
        let answer = null;
        for (const item of COPILOT_KNOWLEDGE) {
            if (item.keywords.some(k => qLower.includes(k))) {
                answer = item.response;
                break;
            }
        }

        if (!answer) {
            answer = `🤖 **Cyber Copilot Advice:**\n\nFor suspicious emails with high risk scores:\n1. Never click embedded links or download attachments.\n2. Verify the sender's full email address and domain age.\n3. If uncertain, forward the raw \`.eml\` header to your SOC security team.`;
        }

        botMsg.innerHTML = `<strong>Cyber Copilot:</strong><br>${answer.replace(/\n/g, '<br>')}`;
        chatContainer.appendChild(botMsg);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 400);
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

window.sendCopilotMessage = sendCopilotMessage;
