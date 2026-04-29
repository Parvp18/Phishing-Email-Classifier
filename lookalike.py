"""
Lookalike Domain Detector Module
================================
Detects typosquatting and visual homograph attacks by comparing
domains against a hardcoded list of highly-targeted brands.
"""

import Levenshtein
import re

TOP_BRANDS = [
    "paypal", "amazon", "google", "microsoft", "apple", "netflix", "facebook",
    "instagram", "twitter", "linkedin", "dropbox", "docusign", "chase", "wellsfargo",
    "bankofamerica", "citibank", "irs", "fedex", "ups", "dhl", "yahoo", "outlook",
    "office365", "steam", "ebay", "walmart", "target", "coinbase", "binance", "kraken"
]

class LookalikeDomainDetector:
    """Detects lookalike domains targeting popular brands."""

    def __init__(self) -> None:
        pass

    def check(self, domain: str) -> dict:
        """
        Check a domain for typosquatting/lookalike patterns.
        
        Args:
            domain (str): The raw domain string (e.g., 'www.paypa1.com')
            
        Returns:
            dict: {is_lookalike: bool, lookalike_of: str, similarity: float}
        """
        if not domain:
            return {"is_lookalike": False}

        domain = domain.lower()
        
        # Strip common subdomains and the TLD
        # For 'www.paypa1.com' -> 'paypa1'
        if domain.startswith("www."):
            domain = domain[4:]
            
        parts = domain.split(".")
        if len(parts) >= 2:
            # We assume the stem is the second-to-last part (e.g., in a.b.com -> b)
            # This is naive but works for standard domains
            input_stem = parts[-2]
        else:
            input_stem = domain

        # Helper to normalize character substitutions (homoglyphs)
        def normalize_subs(s: str) -> str:
            s = s.replace('0', 'o')
            s = s.replace('1', 'l') # Alternatively 'i', but 'l' is common
            s = s.replace('3', 'e')
            s = s.replace('@', 'a')
            return s
            
        normalized_stem = normalize_subs(input_stem)

        for brand in TOP_BRANDS:
            # Check normalized exact match (e.g., paypa1 -> paypal == paypal)
            if normalized_stem == brand and input_stem != brand:
                return {
                    "is_lookalike": True,
                    "lookalike_of": brand,
                    "similarity": 1.0
                }
                
            # Check Levenshtein ratio on original stem
            ratio = Levenshtein.ratio(input_stem, brand)
            if ratio > 0.75 and input_stem != brand:
                return {
                    "is_lookalike": True,
                    "lookalike_of": brand,
                    "similarity": round(ratio, 2)
                }
                
            # Check Levenshtein ratio on normalized stem
            ratio_norm = Levenshtein.ratio(normalized_stem, brand)
            if ratio_norm > 0.75 and normalized_stem != brand:
                 return {
                    "is_lookalike": True,
                    "lookalike_of": brand,
                    "similarity": round(ratio_norm, 2)
                }

        return {"is_lookalike": False}
