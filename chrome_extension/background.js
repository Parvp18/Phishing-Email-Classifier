chrome.runtime.onInstalled.addListener(() => {
    // Set default API key and endpoint on install
    chrome.storage.local.get(['phishguard_api_key', 'phishguard_endpoint', 'phishguard_enabled'], (res) => {
        const defaults = {};
        if (!res.phishguard_api_key) defaults.phishguard_api_key = "your-secret-key-1";
        if (!res.phishguard_endpoint) defaults.phishguard_endpoint = "http://localhost:5000/api/analyze";
        if (res.phishguard_enabled === undefined) defaults.phishguard_enabled = true;
        
        if (Object.keys(defaults).length > 0) {
            chrome.storage.local.set(defaults);
            console.log("PhishGuard default settings applied.");
        }
    });
});
