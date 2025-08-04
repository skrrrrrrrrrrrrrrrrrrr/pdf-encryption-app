import io
import logging
from typing import List

import pikepdf

# Set up logging
logger = logging.getLogger(__name__)


def merge_pdfs(files: List[bytes]) -> bytes:
    """Merge multiple PDF files into one using pikepdf for better performance and reliability"""
    try:
        # Create a new PDF
        merged_pdf = pikepdf.new()
        
        # Process each file
        for i, data in enumerate(files):
            try:
                # Open each PDF
                with pikepdf.open(io.BytesIO(data)) as src_pdf:
                    # Copy all pages to the merged PDF
                    for page in src_pdf.pages:
                        merged_pdf.pages.append(page)
            except Exception as e:
                logger.error(f"Error processing file {i+1} during merge: {str(e)}")
                raise ValueError(f"Invalid PDF file {i+1}: {str(e)}")
        
        # Save to buffer
        buffer = io.BytesIO()
        merged_pdf.save(buffer)
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Error merging PDFs: {str(e)}")
        raise


def split_pdf(data: bytes, start: int, end: int) -> bytes:
    """Split PDF by page range using pikepdf for better performance"""
    try:
        with pikepdf.open(io.BytesIO(data)) as src_pdf:
            # Validate page range
            total_pages = len(src_pdf.pages)
            if start > total_pages:
                raise ValueError(f"Start page {start} exceeds total pages ({total_pages})")
            if end > total_pages:
                raise ValueError(f"End page {end} exceeds total pages ({total_pages})")
            
            # Create new PDF with selected pages
            new_pdf = pikepdf.new()
            for i in range(start - 1, min(end, total_pages)):
                new_pdf.pages.append(src_pdf.pages[i])
            
            # Save to buffer
            buffer = io.BytesIO()
            new_pdf.save(buffer)
            return buffer.getvalue()
            
    except Exception as e:
        logger.error(f"Error splitting PDF: {str(e)}")
        raise


def rotate_pdf(data: bytes, angle: int) -> bytes:
    """Rotate all pages in PDF using pikepdf for better performance"""
    try:
        with pikepdf.open(io.BytesIO(data)) as src_pdf:
            # Rotate all pages in the source PDF directly
            for page in src_pdf.pages:
                current_rotation = page.get("/Rotate", 0)
                new_rotation = (current_rotation + angle) % 360
                page.Rotate = new_rotation
            
            # Save to buffer
            buffer = io.BytesIO()
            src_pdf.save(buffer)
            return buffer.getvalue()
            
    except Exception as e:
        logger.error(f"Error rotating PDF: {str(e)}")
        raise


def encrypt_pdf(data: bytes, password: str) -> bytes:
    """Encrypt PDF with password using pikepdf"""
    try:
        with pikepdf.open(io.BytesIO(data)) as pdf:
            # Save with encryption
            buffer = io.BytesIO()
            pdf.save(
                buffer, 
                encryption=pikepdf.Encryption(
                    owner=password, 
                    user=password, 
                    R=4,
                    allow=pikepdf.Permissions(modify_annotation=True)
                )
            )
            return buffer.getvalue()
            
    except Exception as e:
        logger.error(f"Error encrypting PDF: {str(e)}")
        raise


def decrypt_pdf(data: bytes, password: str) -> bytes:
    """Decrypt password-protected PDF using pikepdf"""
    try:
        with pikepdf.open(io.BytesIO(data), password=password) as pdf:
            # Save without encryption
            buffer = io.BytesIO()
            pdf.save(buffer)
            return buffer.getvalue()
            
    except Exception as e:
        logger.error(f"Error decrypting PDF: {str(e)}")
        if "password" in str(e).lower():
            raise ValueError("Incorrect password provided")
        raise
