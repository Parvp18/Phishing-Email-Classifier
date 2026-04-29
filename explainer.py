"""
Explainability Module
=====================
Uses SHAP (SHapley Additive exPlanations) to explain model predictions,
identifying which features and specific words contributed most to the verdict.
"""

import logging
import numpy as np
import shap
from scipy.sparse import issparse

logger = logging.getLogger(__name__)


class SHAPExplainer:
    """Generates feature importance and word-level heatmaps using SHAP."""

    def __init__(self) -> None:
        pass

    def explain(self, model, X_input, feature_names: list, model_type: str) -> dict:
        """
        Explain a single prediction using SHAP.
        
        Args:
            model: The trained ML model (NB, RF, or XGB).
            X_input: The feature vector (sparse or dense) for a single email. Shape (1, N).
            feature_names: List of all feature names (hand-crafted + TF-IDF words).
            model_type: String identifier ('nb', 'rf', 'xgb').
            
        Returns:
            dict: {
                "top_features": [{"feature": str, "contribution": float}],
                "raw_shap_values": np.ndarray
            }
        """
        try:
            # Convert sparse to dense if needed for specific explainers
            if issparse(X_input):
                X_dense = X_input.toarray()
            else:
                X_dense = X_input

            shap_values = None

            if model_type in ["rf", "xgb"]:
                # TreeExplainer is ideal for Random Forest and XGBoost
                # For XGBoost, using the sparse matrix directly is often fine,
                # but Dense is safer for general TreeExplainer unless optimized.
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_dense)
                
                # Extract the actual values
                if hasattr(shap_values, 'values'):
                    shap_values = shap_values.values
                if isinstance(shap_values, list):
                    shap_values = shap_values[1]

                shap_values = np.array(shap_values)
                if len(shap_values.shape) == 3:
                    shap_values = shap_values[0, :, 1]
                elif len(shap_values.shape) == 2:
                    shap_values = shap_values[0]

            # Get top 10 features by absolute contribution
            top_indices = np.argsort(np.abs(shap_values))[-10:][::-1]
            
            top_features = []
            for idx in top_indices:
                val = float(shap_values[idx])
                if abs(val) > 0.001:  # Only include meaningful contributions
                    top_features.append({
                        "feature": feature_names[idx],
                        "contribution": round(val, 4)
                    })

            return {
                "top_features": top_features,
                "raw_shap_values": shap_values
            }

        except Exception as e:
            logger.error(f"SHAP Explainer error: {e}")
            return {"top_features": [], "raw_shap_values": np.zeros(len(feature_names))}

    def generate_word_scores(self, email_text: str, shap_values: np.ndarray, feature_names: list, vectorizer) -> list:
        """
        Map SHAP values back to original words in the email text to generate a heatmap.
        
        Args:
            email_text: The raw input text.
            shap_values: Array of SHAP values corresponding to feature_names.
            feature_names: List of feature names.
            vectorizer: The fitted TF-IDF vectorizer.
            
        Returns:
            list: [{"word": str, "score": float (0.0-1.0)}]
        """
        if not email_text or shap_values is None:
            return []

        # Create a mapping of word -> shap value from the vocabulary
        word_to_shap = {}
        vocab = vectorizer.vocabulary_
        
        for word, idx in vocab.items():
            # In the combined feature array, TF-IDF features come AFTER hand-crafted features
            # We need to know the offset. Let's assume the caller passes the FULL shap_values
            # and FULL feature_names, so we just match by string.
            try:
                # Find the index of the word in feature_names
                feature_idx = feature_names.index(word)
                val = shap_values[feature_idx]
                word_to_shap[word] = float(val)
            except ValueError:
                continue

        # Split email text into words naively to build the heatmap
        words = email_text.split()
        heatmap = []
        
        # We only care about positive contributions (phishing signals) for the red heatmap
        max_val = max(word_to_shap.values()) if word_to_shap else 0.001
        if max_val <= 0:
            max_val = 0.001

        for raw_word in words:
            # Clean word for lookup
            clean_word = "".join(c for c in raw_word.lower() if c.isalnum())
            
            # Calculate score 0.0 to 1.0 based on contribution
            shap_val = word_to_shap.get(clean_word, 0.0)
            
            # Normalize score
            score = max(0.0, shap_val / max_val) if shap_val > 0 else 0.0
            
            heatmap.append({
                "word": raw_word,
                "score": round(score, 3)
            })

        return heatmap
