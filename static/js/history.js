/**
 * PhishGuard History Logic
 * Fetches and renders scan history with pagination.
 */

const API_KEY = "your-secret-key-1";
let currentPage = 1;

document.addEventListener('DOMContentLoaded', () => {
    loadHistory(1);

    const searchInput = document.getElementById('history_search');
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                loadHistory(1);
            }
        });
    }

    const filterSelect = document.getElementById('label_filter');
    if (filterSelect) {
        filterSelect.addEventListener('change', () => {
            loadHistory(1);
        });
    }

    // Auto-reload history when tab gets focus or visibility changes
    window.addEventListener('focus', () => {
        loadHistory(currentPage);
    });
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            loadHistory(currentPage);
        }
    });
});

async function loadHistory(page = 1) {
    currentPage = page;
    const search = document.getElementById('history_search')?.value || "";
    const filter = document.getElementById('label_filter')?.value || "";
    
    let url = `/api/history?page=${page}&per_page=10`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (filter) url += `&label_filter=${encodeURIComponent(filter)}`;

    try {
        const res = await fetch(url, {
            headers: { 'X-API-Key': API_KEY }
        });
        const data = await res.json();
        
        if (res.ok) {
            renderHistoryTable(data.items);
            renderPagination(data.current_page, data.pages);
        } else {
            console.error(data.error);
        }
    } catch (e) {
        console.error("Failed to load history:", e);
    }
}

function renderHistoryTable(items) {
    const tbody = document.getElementById('history_tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No records found.</td></tr>';
        return;
    }

    items.forEach(item => {
        const date = new Date(item.created_at).toLocaleString();
        const subject = item.subject || '<i>No Subject</i>';
        const sender = item.sender || '<i>Unknown Sender</i>';
        const labelClass = item.label === 'PHISHING' ? 'red' : 'green';
        
        tbody.innerHTML += `
            <tr>
                <td>${date}</td>
                <td>
                    <div><strong>${subject}</strong></div>
                    <div style="font-size:0.75rem;color:var(--text-muted)">${sender}</div>
                </td>
                <td><span class="pill ${labelClass}">${item.label}</span></td>
                <td>${item.confidence}%</td>
                <td>${item.attack_type || 'N/A'}</td>
                <td>
                    <button class="btn-demo" style="padding: 0.25rem 0.5rem" onclick="viewReport('${item.id}')">PDF</button>
                </td>
            </tr>
        `;
    });
}

function renderPagination(current, total) {
    const controls = document.getElementById('pagination_controls');
    if (!controls) return;
    
    controls.innerHTML = '';
    
    if (total <= 1) return;
    
    if (current > 1) {
        controls.innerHTML += `<button class="btn-demo" style="width:auto;padding:0.25rem 0.5rem;" onclick="loadHistory(${current - 1})">Prev</button>`;
    }
    
    controls.innerHTML += `<span style="margin: 0 1rem;">Page ${current} of ${total}</span>`;
    
    if (current < total) {
        controls.innerHTML += `<button class="btn-demo" style="width:auto;padding:0.25rem 0.5rem;" onclick="loadHistory(${current + 1})">Next</button>`;
    }
}

function viewReport(id) {
    window.open(`/api/report/${id}?X-API-Key=${API_KEY}`, '_blank');
}
