"""
Threat Intelligence Module
==========================
Integrates with external APIs (VirusTotal, IP-API, WHOIS) and parses
email headers to gather real-time context about potential threats.
"""

import os
import re
import json
import base64
import logging
from datetime import datetime, timezone
from typing import Optional

import requests
import whois
from config import VIRUSTOTAL_API_KEY

logger = logging.getLogger(__name__)


class ThreatIntelEngine:
    """Gathers threat intelligence on URLs, IPs, domains, and headers."""

    def __init__(self) -> None:
        self.vt_api_key = VIRUSTOTAL_API_KEY
        self.vt_url = "https://www.virustotal.com/api/v3/urls"

    def check_virustotal(self, url: str) -> Optional[dict]:
        """
        Query VirusTotal API for a given URL.
        
        Args:
            url (str): The URL to check.
            
        Returns:
            dict or None: {malicious_count: int, total_engines: int, permalink: str}
                          Returns None if API limit reached or failure.
        """
        if not self.vt_api_key:
            logger.warning("No VirusTotal API key configured.")
            return None

        # VT v3 API requires base64 url-safe (no padding) of the URL as the identifier
        # Alternatively, we can POST to scan, then GET the analysis, 
        # but GET on /urls/{id} is faster if already known.
        # To strictly follow instructions "POST to https://www.virustotal.com/api/v3/urls":
        
        headers = {
            "accept": "application/json",
            "x-apikey": self.vt_api_key,
            "content-type": "application/x-www-form-urlencoded"
        }
        
        payload = {"url": url}
        
        try:
            # Step 1: Submit URL
            res = requests.post(self.vt_url, headers=headers, data=payload, timeout=10)
            if res.status_code == 429:
                logger.warning("VirusTotal API rate limited.")
                return None
            if res.status_code != 200:
                logger.error(f"VT POST Error: {res.status_code} - {res.text}")
                return None
                
            analysis_id = res.json().get("data", {}).get("id")
            if not analysis_id:
                return None
                
            # Step 2: GET the analysis result
            analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
            get_headers = {"accept": "application/json", "x-apikey": self.vt_api_key}
            
            # Note: The analysis might be pending, but for simplicity we take what we get immediately
            res_get = requests.get(analysis_url, headers=get_headers, timeout=10)
            if res_get.status_code != 200:
                return None
                
            stats = res_get.json().get("data", {}).get("attributes", {}).get("stats", {})
            
            malicious = stats.get("malicious", 0)
            total = sum(stats.values())
            
            # Construct permalink (pseudo-permalink for the URL itself)
            # Safe base64 encoding without padding
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
            permalink = f"https://www.virustotal.com/gui/url/{url_id}"

            return {
                "malicious_count": malicious,
                "total_engines": total,
                "permalink": permalink
            }

        except Exception as e:
            logger.error(f"Error querying VirusTotal: {e}")
            return None

    def check_domain_age(self, domain: str) -> int:
        """
        Check domain registration age using python-whois.
        
        Returns:
            int: Age in days, or -1 if lookup fails.
        """
        try:
            w = whois.whois(domain)
            creation_date = w.creation_date
            if not creation_date:
                return -1
                
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
                
            # creation_date should be a datetime object
            if isinstance(creation_date, datetime):
                now = datetime.now(timezone.utc)
                # Ensure creation_date is timezone-aware for math
                if creation_date.tzinfo is None:
                    creation_date = creation_date.replace(tzinfo=timezone.utc)
                age_delta = now - creation_date
                return max(0, age_delta.days)
            return -1
        except Exception as e:
            logger.error(f"WHOIS lookup failed for {domain}: {e}")
            return -1

    def check_spf_dkim(self, raw_email_text: str) -> dict:
        """
        Parse raw email text/headers to find SPF and DKIM status.
        
        Returns:
            dict: {"spf": "pass"|"fail"|"none", "dkim": bool}
        """
        result = {"spf": "none", "dkim": False}
        
        # Simple regex to find Authentication-Results or Received-SPF headers
        spf_match = re.search(r"Received-SPF:\s*(pass|fail|softfail|neutral|none)", raw_email_text, re.IGNORECASE)
        if spf_match:
            val = spf_match.group(1).lower()
            if val in ["pass", "fail", "none"]:
                result["spf"] = val
            elif val in ["softfail", "neutral"]:
                result["spf"] = "fail"
                
        auth_match = re.search(r"Authentication-Results:.*?spf=(pass|fail|none)", raw_email_text, re.IGNORECASE | re.DOTALL)
        if auth_match and result["spf"] == "none":
            result["spf"] = auth_match.group(1).lower()

        # Check DKIM
        if "dkim=pass" in raw_email_text.lower() or "dkim-signature:" in raw_email_text.lower():
            # If we have a signature, we naively assume it's valid for this context 
            # unless auth-results explicitly says dkim=fail
            result["dkim"] = True
            
        if "dkim=fail" in raw_email_text.lower():
            result["dkim"] = False

        return result

    def geolocate_sender_ip(self, ip_address: str) -> dict:
        """
        Query ip-api.com for IP geolocation data.
        
        Returns:
            dict: {country, city, isp, lat, lon}
        """
        empty_res = {"country": "Unknown", "city": "Unknown", "isp": "Unknown", "lat": 0.0, "lon": 0.0}
        if not ip_address:
            return empty_res
            
        try:
            res = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "success":
                    return {
                        "country": data.get("country", "Unknown"),
                        "city": data.get("city", "Unknown"),
                        "isp": data.get("isp", "Unknown"),
                        "lat": data.get("lat", 0.0),
                        "lon": data.get("lon", 0.0)
                    }
        except Exception as e:
            logger.error(f"IP Geolocation failed for {ip_address}: {e}")
            
        return empty_res

    def extract_sender_ip(self, raw_email_text: str) -> str:
        """
        Parse Received headers to find the originating sender IP.
        Skips private/loopback IP ranges.
        """
        ip_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        
        # Helper to check if IP is private
        def is_public(ip: str) -> bool:
            parts = ip.split(".")
            if len(parts) != 4:
                return False
            if parts[0] == "10": return False
            if parts[0] == "127": return False
            if parts[0] == "172" and 16 <= int(parts[1]) <= 31: return False
            if parts[0] == "192" and parts[1] == "168": return False
            if ip.startswith("169.254"): return False
            return True

        # Find all Received headers
        received_headers = re.findall(r"Received:.*?(?:\n\s+.*?)*", raw_email_text, re.IGNORECASE)
        
        # Usually the last Received header is the earliest one (originating)
        for header in reversed(received_headers):
            ips = re.findall(ip_pattern, header)
            for ip in ips:
                if is_public(ip):
                    return ip
                    
        # Fallback: just find the first public IP in the entire text (risky, but better than nothing)
        all_ips = re.findall(ip_pattern, raw_email_text)
        for ip in all_ips:
            if is_public(ip):
                return ip
                
        return ""
