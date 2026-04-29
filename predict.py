"""
Prediction Engine
=================
Loads trained models, orchestrates feature extraction, threat intel,
and lookalike detection, and returns a unified analysis dictionary.
"""

import os
import re
import time
import pickle
import hashlib
import logging
from urllib.parse import urlparse
import pandas as pd
from scipy.sparse import hstack

from config import MODEL_DIR
from classifier import preprocess_text, FeatureExtractor
from threat_intel import ThreatIntelEngine
from lookalike import LookalikeDomainDetector
from explainer import SHAPExplainer

# Hack to allow unpickling of FeatureExtractor which was trained as __main__
import __main__
__main__.FeatureExtractor = FeatureExtractor

logger = logging.getLogger(__name__)


class PhishingPredictor:
    """Core engine that ties together ML, threat intel, and explanations."""

    def __init__(self):
        self.models_loaded = False
        self.load_models()
        self.threat_intel = ThreatIntelEngine()
        self.lookalike = LookalikeDomainDetector()
        self.explainer = SHAPExplainer()

    def load_models(self):
        """Load trained models from disk."""
        try:
            with open(os.path.join(MODEL_DIR, "nb_model.pkl"), "rb") as f:
                self.nb_model = pickle.load(f)
            with open(os.path.join(MODEL_DIR, "rf_model.pkl"), "rb") as f:
                self.rf_model = pickle.load(f)
            with open(os.path.join(MODEL_DIR, "xgb_model.pkl"), "rb") as f:
                self.xgb_model = pickle.load(f)
            with open(os.path.join(MODEL_DIR, "ensemble_model.pkl"), "rb") as f:
                self.ensemble = pickle.load(f)
            with open(os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"), "rb") as f:
                self.tfidf = pickle.load(f)
            with open(os.path.join(MODEL_DIR, "feature_extractor.pkl"), "rb") as f:
                self.fe = pickle.load(f)
                
            # Construct total feature names list for SHAP
            self.feature_names = self.fe.feature_names + self.tfidf.get_feature_names_out().tolist()
            self.models_loaded = True
            logger.info("Models loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load models. Did you run classifier.py? Error: {e}")
            self.models_loaded = False

    def analyze(self, email_text: str, subject: str = "", sender: str = "") -> dict:
        """Run full analysis pipeline on an email."""
        start_time = time.time()
        
        if not self.models_loaded:
            self.load_models()
            if not self.models_loaded:
                return {"error": "Models not loaded. Cannot process request."}

        # 1. Feature Extraction (Manual)
        df_input = pd.DataFrame([{"text": email_text, "subject": subject, "sender": sender}])
        X_manual = self.fe.extract_features(df_input)
        manual_features_dict = self.fe._extract_single(email_text, subject, sender)
        
        # 2. Text Preprocessing & TF-IDF
        clean_text = preprocess_text(email_text)
        X_tfidf = self.tfidf.transform([clean_text])
        
        # 3. Combine Features
        X_combined = hstack([X_manual, X_tfidf])
        
        # 4. Predictions
        nb_prob = self.nb_model.predict_proba(X_combined)[0][1]
        rf_prob = self.rf_model.predict_proba(X_combined)[0][1]
        xgb_prob = self.xgb_model.predict_proba(X_combined)[0][1]
        ens_prob = self.ensemble.predict_proba(X_combined)[0][1]
        
        is_phishing = ens_prob >= 0.5
        label = "PHISHING" if is_phishing else "SAFE"
        
        # 5. Risk Scoring
        risk_score = float(ens_prob)
        if risk_score > 0.85:
            risk_level = "CRITICAL"
        elif risk_score > 0.65:
            risk_level = "HIGH"
        elif risk_score > 0.40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
            
        # 6. Extract URLs and perform Threat Intel + Lookalike
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', email_text)
        urls_found = []
        for u in set(urls):
            domain = urlparse(u).netloc.split(':')[0]
            vt_info = self.threat_intel.check_virustotal(u)
            la_info = self.lookalike.check(domain)
            age = self.threat_intel.check_domain_age(domain)
            
            vt_score_str = f"{vt_info['malicious_count']}/{vt_info['total_engines']} engines flagged" if vt_info else "Not Scanned"
            
            urls_found.append({
                "url": u,
                "virustotal_score": vt_score_str,
                "is_lookalike": la_info.get("is_lookalike", False),
                "lookalike_of": la_info.get("lookalike_of", ""),
                "domain_age_days": age
            })
            
            # Boost risk if VT flags it
            if vt_info and vt_info['malicious_count'] > 0:
                is_phishing = True
                label = "PHISHING"
                risk_level = "CRITICAL"
                
        # 7. Extract Sender IP, SPF/DKIM, Geolocation
        sender_ip = self.threat_intel.extract_sender_ip(email_text)
        geo_info = self.threat_intel.geolocate_sender_ip(sender_ip) if sender_ip else {}
        auth_info = self.threat_intel.check_spf_dkim(email_text)

        # Merge intel into features dict for output
        features = manual_features_dict.copy()
        features["spf_pass"] = (auth_info["spf"] == "pass")
        features["dkim_pass"] = auth_info["dkim"]
        features["sender_ip"] = sender_ip
        features["sender_country"] = geo_info.get("country", "")
        
        # 8. SHAP Explainability
        # Use RF for explanation as it's robust
        shap_res = self.explainer.explain(self.rf_model, X_combined, self.feature_names, "rf")
        heatmap = self.explainer.generate_word_scores(clean_text, shap_res["raw_shap_values"], self.feature_names, self.tfidf)
        
        # 9. Attack Type Estimation
        attack_type = "Unknown"
        if manual_features_dict["has_login_form_words"] or "verify" in clean_text:
            attack_type = "Credential Harvesting"
        elif "invoice" in clean_text or "payment" in clean_text:
            attack_type = "Business Email Compromise"
        elif "prize" in clean_text or "winner" in clean_text:
            attack_type = "Advance Fee Fraud"

        # 10. Recommendations
        if label == "PHISHING":
            rec = "Do not click any links or download attachments. Report to IT immediately."
        else:
            rec = "Email appears safe, but always exercise caution."

        # Compile final dict
        result = {
            "label": label,
            "confidence": round(float(ens_prob) * 100, 1),
            "risk_score": round(float(risk_score), 3),
            "risk_level": risk_level,
            "model_votes": {
                "naive_bayes": {"label": "PHISHING" if nb_prob >= 0.5 else "SAFE", "confidence": round(float(nb_prob) * 100, 1)},
                "random_forest": {"label": "PHISHING" if rf_prob >= 0.5 else "SAFE", "confidence": round(float(rf_prob) * 100, 1)},
                "xgboost": {"label": "PHISHING" if xgb_prob >= 0.5 else "SAFE", "confidence": round(float(xgb_prob) * 100, 1)},
                "ensemble": {"label": "PHISHING" if ens_prob >= 0.5 else "SAFE", "confidence": round(float(ens_prob) * 100, 1)},
            },
            "features": features,
            "urls_found": urls_found,
            "shap_top_features": shap_res["top_features"],
            "word_heatmap": heatmap,
            "attack_type": attack_type,
            "attack_type_confidence": round(float(rf_prob) * 100, 1), # approximation
            "recommendation": rec,
            "email_hash": hashlib.sha256(email_text.encode('utf-8')).hexdigest(),
            "analysis_time_ms": int((time.time() - start_time) * 1000)
        }

        return result
