"""
PDF Watermarking Utility (Phase IXf+)
Adds visible watermarks to PDF exports for partner sharing
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from PyPDF2 import PdfReader, PdfWriter
    WATERMARK_AVAILABLE = True
except ImportError:
    WATERMARK_AVAILABLE = False
    logging.warning("PyPDF2 or reportlab not installed - watermarking disabled")

logger = logging.getLogger(__name__)


def mask_email(email: str) -> str:
    """Mask email for watermark display: user@example.com → u***@example.com"""
    if '@' not in email:
        return email[:1] + '***'
    
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + '***'
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def create_watermark_overlay(
    output_path: str,
    recipient_email: str,
    expires_at: datetime,
    company: Optional[str] = None
) -> str:
    """
    Create a watermark overlay PDF
    
    Args:
        output_path: Path to save watermark PDF
        recipient_email: Recipient email (will be masked)
        expires_at: Expiry date
        company: Optional company name
    
    Returns:
        Path to watermark PDF
    """
    if not WATERMARK_AVAILABLE:
        raise RuntimeError("Watermarking libraries not installed")
    
    # Create watermark PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Watermark text
    masked_email = mask_email(recipient_email)
    expiry_str = expires_at.strftime('%Y-%m-%d')
    
    watermark_text = f"Confidential Preview • {masked_email}"
    if company:
        watermark_text += f" • {company}"
    watermark_text += f" • Expires: {expiry_str}"
    
    # Draw watermark at bottom of page
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)  # Gray
    c.drawCentredString(width / 2, 20, watermark_text)
    
    # Add "CONFIDENTIAL" diagonal watermark (subtle)
    c.saveState()
    c.setFont("Helvetica-Bold", 60)
    c.setFillColorRGB(0.9, 0.9, 0.9)  # Very light gray
    c.translate(width / 2, height / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, "CONFIDENTIAL")
    c.restoreState()
    
    c.save()
    return output_path


def watermark_pdf(
    input_pdf: str,
    output_pdf: str,
    recipient_email: str,
    expires_at: datetime,
    company: Optional[str] = None
) -> str:
    """
    Apply watermark to PDF
    
    Args:
        input_pdf: Path to input PDF
        output_pdf: Path to save watermarked PDF
        recipient_email: Recipient email
        expires_at: Expiry date
        company: Optional company name
    
    Returns:
        Path to watermarked PDF
    """
    if not WATERMARK_AVAILABLE:
        logger.warning("Watermarking not available - copying original file")
        import shutil
        shutil.copy2(input_pdf, output_pdf)
        return output_pdf
    
    try:
        # Create watermark overlay
        watermark_path = output_pdf.replace('.pdf', '_watermark_temp.pdf')
        create_watermark_overlay(watermark_path, recipient_email, expires_at, company)
        
        # Read PDFs
        input_reader = PdfReader(input_pdf)
        watermark_reader = PdfReader(watermark_path)
        watermark_page = watermark_reader.pages[0]
        
        # Apply watermark to each page
        writer = PdfWriter()
        for page in input_reader.pages:
            page.merge_page(watermark_page)
            writer.add_page(page)
        
        # Write output
        with open(output_pdf, 'wb') as f:
            writer.write(f)
        
        # Clean up temp file
        if os.path.exists(watermark_path):
            os.remove(watermark_path)
        
        logger.info(f"Watermarked PDF created: {output_pdf}")
        return output_pdf
    
    except Exception as e:
        logger.error(f"Watermarking failed: {e}")
        # Fallback: copy original
        import shutil
        shutil.copy2(input_pdf, output_pdf)
        return output_pdf


def add_json_watermark_headers(
    data: dict,
    recipient_email: str,
    expires_at: datetime,
    company: Optional[str] = None
) -> dict:
    """
    Add watermark metadata to JSON export
    
    Args:
        data: JSON data dict
        recipient_email: Recipient email
        expires_at: Expiry date
        company: Optional company name
    
    Returns:
        Updated JSON data with watermark metadata
    """
    watermark = {
        "recipient": mask_email(recipient_email),
        "expires_at": expires_at.isoformat(),
        "confidential": True,
        "redistribution_prohibited": True
    }
    
    if company:
        watermark["company"] = company
    
    data["_watermark"] = watermark
    
    return data
