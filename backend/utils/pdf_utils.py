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


def resize_pdf(data: bytes, quality: str = "medium") -> bytes:
    """Resize/compress PDF by optimizing content and reducing quality"""
    try:
        with pikepdf.open(io.BytesIO(data)) as pdf:
            # Define quality settings
            quality_settings = {
                "high": {"object_stream_mode": pikepdf.ObjectStreamMode.generate},
                "medium": {"object_stream_mode": pikepdf.ObjectStreamMode.generate, "compress_streams": True},
                "low": {"object_stream_mode": pikepdf.ObjectStreamMode.generate, "compress_streams": True, "normalize_content": True}
            }
            
            settings = quality_settings.get(quality, quality_settings["medium"])
            
            # Save with compression settings
            buffer = io.BytesIO()
            pdf.save(buffer, **settings)
            return buffer.getvalue()
            
    except Exception as e:
        logger.error(f"Error resizing PDF: {str(e)}")
        raise


def add_signature_pdf(data: bytes, signature_text: str, position: str = "bottom-right") -> bytes:
    """Add text signature to all pages of PDF"""
    try:
        with pikepdf.open(io.BytesIO(data)) as pdf:
            # Position mapping
            positions = {
                "bottom-right": (450, 50),
                "bottom-left": (50, 50),
                "top-right": (450, 750),
                "top-left": (50, 750),
                "center": (300, 400)
            }
            
            x, y = positions.get(position, positions["bottom-right"])
            
            # Add signature to each page
            for page in pdf.pages:
                # Get or create resources
                if "/Resources" not in page:
                    page.Resources = pdf.make_indirect(pikepdf.Dictionary())
                
                if "/Font" not in page.Resources:
                    page.Resources.Font = pdf.make_indirect(pikepdf.Dictionary())
                
                # Add a basic font
                font_dict = pikepdf.Dictionary({
                    "/Type": pikepdf.Name.Font,
                    "/Subtype": pikepdf.Name.Type1,
                    "/BaseFont": pikepdf.Name.Helvetica
                })
                page.Resources.Font.F1 = pdf.make_indirect(font_dict)
                
                # Create signature content stream
                signature_stream = f"""
                BT
                /F1 10 Tf
                {x} {y} Td
                0.5 0.5 0.5 rg
                ({signature_text}) Tj
                ET
                """
                
                # Add to existing content or create new
                if "/Contents" in page:
                    # Get existing content
                    existing_content = page.Contents
                    if isinstance(existing_content, list):
                        # Multiple content streams
                        new_stream = pikepdf.Stream(pdf, signature_stream.encode())
                        existing_content.append(new_stream)
                    else:
                        # Single content stream, convert to array
                        new_stream = pikepdf.Stream(pdf, signature_stream.encode())
                        page.Contents = [existing_content, new_stream]
                else:
                    # No existing content
                    page.Contents = pikepdf.Stream(pdf, signature_stream.encode())
            
            # Save modified PDF
            buffer = io.BytesIO()
            pdf.save(buffer)
            return buffer.getvalue()
            
    except Exception as e:
        logger.error(f"Error adding signature to PDF: {str(e)}")
        raise


def add_watermark_pdf(data: bytes, watermark_text: str, opacity: float = 0.3) -> bytes:
    """Add watermark text to all pages of PDF"""
    try:
        with pikepdf.open(io.BytesIO(data)) as pdf:
            # Add watermark to each page
            for page in pdf.pages:
                # Get or create resources
                if "/Resources" not in page:
                    page.Resources = pdf.make_indirect(pikepdf.Dictionary())
                
                if "/Font" not in page.Resources:
                    page.Resources.Font = pdf.make_indirect(pikepdf.Dictionary())
                
                # Add a basic font
                font_dict = pikepdf.Dictionary({
                    "/Type": pikepdf.Name.Font,
                    "/Subtype": pikepdf.Name.Type1,
                    "/BaseFont": pikepdf.Name.Helvetica_Bold
                })
                page.Resources.Font.F1 = pdf.make_indirect(font_dict)
                
                # Create watermark content stream (diagonal, centered)
                watermark_stream = f"""
                q
                {opacity} {opacity} {opacity} rg
                {opacity} {opacity} {opacity} RG
                BT
                /F1 48 Tf
                1 0 0 1 300 400 Tm
                45 Tr
                ({watermark_text}) Tj
                ET
                Q
                """
                
                # Add to existing content or create new
                if "/Contents" in page:
                    # Get existing content
                    existing_content = page.Contents
                    if isinstance(existing_content, list):
                        # Add watermark as first element (background)
                        new_stream = pikepdf.Stream(pdf, watermark_stream.encode())
                        existing_content.insert(0, new_stream)
                    else:
                        # Single content stream, convert to array with watermark first
                        new_stream = pikepdf.Stream(pdf, watermark_stream.encode())
                        page.Contents = [new_stream, existing_content]
                else:
                    # No existing content
                    page.Contents = pikepdf.Stream(pdf, watermark_stream.encode())
            
            # Save modified PDF
            buffer = io.BytesIO()
            pdf.save(buffer)
            return buffer.getvalue()
            
    except Exception as e:
        logger.error(f"Error adding watermark to PDF: {str(e)}")
        raise
