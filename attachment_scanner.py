"""
Attachment Scanner Module
=========================
Scans parsed email attachments for potentially malicious content
like macros in Office documents or suspicious objects in PDFs.
"""

import os
import tempfile
import logging
import fitz  # PyMuPDF
from oletools.olevba import VBA_Parser, TYPE_OLE, TYPE_OpenXML, TYPE_Word2003_XML, TYPE_MHTML

logger = logging.getLogger(__name__)

class AttachmentScanner:
    """Detects malicious characteristics in common attachment types."""

    def __init__(self) -> None:
        pass

    def scan_pdf(self, file_content: bytes, filename: str) -> dict:
        """Scan a PDF file for suspicious objects (JavaScript, embedded files, launch actions)."""
        result = {
            "filename": filename,
            "type": "PDF",
            "is_suspicious": False,
            "threats_found": []
        }
        try:
            # Load PDF from memory
            doc = fitz.open(stream=file_content, filetype="pdf")
            
            # Check for embedded JS
            if doc.has_annots(): # simplified check as PyMuPDF JS extraction is complex
                # We can check specific objects if we iterate, but as a heuristic:
                for page in doc:
                    if page.first_annot:
                        result["threats_found"].append("Contains Annotations (potential JS/Launch)")
                        result["is_suspicious"] = True
                        break
                        
            # Check for embedded files
            if doc.embedded_file_count > 0:
                result["threats_found"].append("Contains Embedded Files")
                result["is_suspicious"] = True

            doc.close()
        except Exception as e:
            logger.error(f"Error scanning PDF {filename}: {e}")
            result["threats_found"].append("Failed to parse PDF (Corrupt or Encrypted)")
            result["is_suspicious"] = True

        return result

    def scan_office_doc(self, file_content: bytes, filename: str) -> dict:
        """Scan an Office document for malicious VBA macros using oletools."""
        result = {
            "filename": filename,
            "type": "Office",
            "is_suspicious": False,
            "threats_found": []
        }
        
        # oletools often expects a file path for advanced parsing, but VBA_Parser handles bytes
        try:
            vbaparser = VBA_Parser(filename, data=file_content)
            if vbaparser.detect_vba_macros():
                result["is_suspicious"] = True
                result["threats_found"].append("Contains VBA Macros")
                
                # Further analysis to find auto-exec or suspicious keywords
                for (subfilename, stream_path, vba_filename, vba_code) in vbaparser.extract_macros():
                    results = vbaparser.analyze_macros()
                    for kw_type, keyword, description in results:
                        if kw_type in ['AutoExec', 'Suspicious', 'IOC']:
                            result["threats_found"].append(f"{kw_type} keyword found: {keyword}")
            vbaparser.close()
        except Exception as e:
            logger.error(f"Error scanning Office doc {filename}: {e}")
            # If we can't parse it but it's an office file, could be encrypted/corrupt
            pass
            
        # Deduplicate threats
        result["threats_found"] = list(set(result["threats_found"]))
        return result

    def scan_attachment(self, file_content: bytes, filename: str) -> dict:
        """Entry point to scan any attachment based on extension."""
        ext = filename.lower().split('.')[-1] if '.' in filename else ""
        
        if ext == "pdf":
            return self.scan_pdf(file_content, filename)
        elif ext in ["doc", "docx", "xls", "xlsx", "xlsm", "docm", "ppt", "pptx"]:
            return self.scan_office_doc(file_content, filename)
        elif ext in ["exe", "bat", "js", "vbs", "ps1", "scr"]:
            return {
                "filename": filename,
                "type": "Executable/Script",
                "is_suspicious": True,
                "threats_found": ["Dangerous file extension"]
            }
        
        # Safe/Unknown extensions
        return {
            "filename": filename,
            "type": "Unknown/Safe",
            "is_suspicious": False,
            "threats_found": []
        }
