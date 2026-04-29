"""
Report Generator Module
=======================
Generates downloadable PDF reports from scan results using WeasyPrint
and Jinja2 templates.
"""

import os
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception as e:
    WEASYPRINT_AVAILABLE = False
    print(f"WeasyPrint not available (PDF generation disabled). Reason: {e}")

from config import REPORTS_FOLDER

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates PDF reports for PhishGuard scan results."""

    def __init__(self, template_dir: str = "templates"):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template_name = "report_template.html"

    def generate_pdf(self, scan_result: dict, scan_id: str = None) -> bytes:
        """
        Generate a PDF from a scan result dictionary.
        
        Args:
            scan_result (dict): The result dictionary from Predictor or DB.
            scan_id (str): Optional ID to save the file as.
            
        Returns:
            bytes: The raw PDF bytes.
        """
        if not WEASYPRINT_AVAILABLE:
            logger.error("WeasyPrint is not installed or missing OS dependencies.")
            return b"PDF Generation failed due to missing WeasyPrint dependencies."

        try:
            template = self.env.get_template(self.template_name)
            
            # Prepare context for Jinja
            # Format dates, round numbers
            context = {
                "scan": scan_result,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "is_phishing": scan_result.get("label") == "PHISHING",
            }
            
            html_out = template.render(context)
            
            # Generate PDF
            pdf_bytes = HTML(string=html_out, base_url=os.path.abspath(".")).write_pdf()
            
            # Save copy to disk
            if scan_id:
                filepath = os.path.join(REPORTS_FOLDER, f"{scan_id}.pdf")
                with open(filepath, "wb") as f:
                    f.write(pdf_bytes)
                    
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return b"PDF Generation Error"
