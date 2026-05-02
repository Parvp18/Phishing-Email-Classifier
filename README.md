# 🛡️ PhishGuard — Production-Grade Phishing Email Detection System

PhishGuard is a full-stack cybersecurity application that detects phishing emails using a hybrid approach of machine learning, behavioral analysis, and real-time threat intelligence.

It supports single email analysis, `.eml` file uploads, and bulk CSV scanning, and provides detailed, explainable threat reports with visualizations and PDF export.

---

## 🚀 Features

### 🔍 Multi-Layer Phishing Detection

* Machine learning ensemble (Naive Bayes + Random Forest + XGBoost)
* Behavioral and structural email feature analysis
* URL and domain reputation checks

### 🧠 Explainable AI

* SHAP-based feature importance
* Word-level heatmap visualization
* Model comparison insights

### 🌐 Threat Intelligence Integration

* VirusTotal URL scanning
* WHOIS domain age detection
* SPF/DKIM validation
* IP geolocation lookup

### 📊 Interactive Dashboard

* Real-time analytics
* Attack type distribution
* Scan history with filters and search

### 📄 Reporting

* Export detailed PDF reports
* JSON export for integrations

### 🔐 Secure API

* API key authentication
* Rate limiting
* Bulk processing support

### 🔄 Auto-Retraining

* Weekly model retraining using user feedback

### 🧩 Chrome Extension

* Gmail phishing detection in real time
* Inline risk badges

### 🐳 Dockerized Deployment

* One-command startup using Docker Compose

---

### 📥 Analyze Email

**POST /api/analyze**

```json
{
  "email_text": "Your account has been suspended...",
  "subject": "Urgent action required",
  "sender": "support@fakebank.com"
}
```

## 🧠 Machine Learning Pipeline

* Text preprocessing (NLTK + BeautifulSoup)
* TF-IDF vectorization (1–3 grams)
* Custom phishing features:

  * URL count
  * Urgent keywords
  * Domain mismatch
  * Obfuscation detection
* Models:

  * Multinomial Naive Bayes
  * Random Forest
  * XGBoost
* Ensemble voting classifier

---

## 🔍 Detection Capabilities

PhishGuard identifies:

* Credential harvesting attacks
* Malware delivery emails
* Business email compromise (BEC)
* Fake brand impersonation
* Lookalike domains (typosquatting)

## 📌 Configuration

All configs are in `config.py`:

* API keys
* rate limits
* file size limits
* database path
* retraining thresholds

---

## 🛠️ Tech Stack

| Layer          | Technology            |
| -------------- | --------------------- |
| Backend        | Flask                 |
| ML             | scikit-learn, XGBoost |
| Explainability | SHAP                  |
| Frontend       | HTML, CSS, JS         |
| Database       | SQLite                |
| DevOps         | Docker                |
| Scheduler      | APScheduler           |

---

## ⚠️ Limitations

* VirusTotal free tier has rate limits
* SQLite not suitable for large-scale production
* Model accuracy depends on training dataset quality

---

## 🔐 Security Notes

* Never expose API keys publicly
* Use HTTPS in production
* Implement stronger auth for enterprise use

---

## 🤝 Contribution

Contributions are welcome. You can:

* Improve model accuracy
* Add new threat intel sources
* Enhance UI/UX
* Optimize performance

---

## ✅ Status

✔ Production-ready architecture
✔ Modular design
✔ Fully dockerized
✔ API + UI + ML integrated

---

## ⭐ If You Like This Project

Give it a star ⭐ on GitHub and share it.

---
