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
    """Resize/compress PDF with aggressive optimization techniques"""
    try:
        with pikepdf.open(io.BytesIO(data)) as pdf:
            # Apply content optimization based on quality level
            for page in pdf.pages:
                # Remove or compress images based on quality
                if "/Resources" in page and "/XObject" in page.Resources:
                    xobjects = page.Resources.XObject
                    for name in list(xobjects.keys()):
                        xobj = xobjects[name]
                        if "/Subtype" in xobj and xobj.Subtype == pikepdf.Name.Image:
                            # For low quality, remove large images
                            if quality == "low":
                                # Remove images larger than 100KB
                                if hasattr(xobj, "Length") and xobj.Length > 100000:
                                    del xobjects[name]
                            elif quality == "medium":
                                # Reduce image quality by recompressing
                                if "/Filter" in xobj and xobj.Filter == pikepdf.Name.DCTDecode:
                                    # It's a JPEG, we can reduce quality
                                    try:
                                        # Mark for lower quality compression
                                        if hasattr(xobj, "Length") and xobj.Length > 50000:
                                            # Create smaller placeholder or remove
                                            del xobjects[name]
                                    except:
                                        pass
            
            # Define comprehensive quality settings
            quality_settings = {
                "high": {
                    "object_stream_mode": pikepdf.ObjectStreamMode.generate,
                    "compress_streams": True,
                    "stream_decode_level": pikepdf.StreamDecodeLevel.specialized
                },
                "medium": {
                    "object_stream_mode": pikepdf.ObjectStreamMode.generate,
                    "compress_streams": True,
                    "normalize_content": True,
                    "stream_decode_level": pikepdf.StreamDecodeLevel.generalized,
                    "recompress_flate": True
                },
                "low": {
                    "object_stream_mode": pikepdf.ObjectStreamMode.generate,
                    "compress_streams": True,
                    "normalize_content": True,
                    "stream_decode_level": pikepdf.StreamDecodeLevel.all,
                    "recompress_flate": True,
                    "linearize": True
                }
            }
            
            settings = quality_settings.get(quality, quality_settings["medium"])
            
            # Additional optimizations for low quality
            if quality == "low":
                # Remove metadata to save space
                if "/Info" in pdf.Root:
                    try:
                        del pdf.Root.Info
                    except:
                        pass
                
                # Remove optional content groups
                if "/OCProperties" in pdf.Root:
                    try:
                        del pdf.Root.OCProperties
                    except:
                        pass
            
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
    """Add watermark text to all pages of PDF with proper positioning"""
    try:
        with pikepdf.open(io.BytesIO(data)) as pdf:
            # Add watermark to each page
            for page in pdf.pages:
                # Get page dimensions
                if "/MediaBox" in page:
                    media_box = page.MediaBox
                    page_width = float(media_box[2] - media_box[0])
                    page_height = float(media_box[3] - media_box[1])
                else:
                    # Default letter size
                    page_width = 612
                    page_height = 792
                
                # Calculate center position
                center_x = page_width / 2
                center_y = page_height / 2
                
                # Calculate font size based on page size
                font_size = min(page_width, page_height) / 8  # Dynamic font size
                
                # Get or create resources
                if "/Resources" not in page:
                    page.Resources = pdf.make_indirect(pikepdf.Dictionary())
                
                if "/Font" not in page.Resources:
                    page.Resources.Font = pdf.make_indirect(pikepdf.Dictionary())
                
                # Add a bold font for better visibility
                font_dict = pikepdf.Dictionary({
                    "/Type": pikepdf.Name.Font,
                    "/Subtype": pikepdf.Name.Type1,
                    "/BaseFont": pikepdf.Name.Helvetica_Bold
                })
                page.Resources.Font.F1 = pdf.make_indirect(font_dict)
                
                # Create watermark content stream with proper rotation and positioning
                # Use transformation matrix for rotation and positioning
                cos_45 = 0.707  # cos(45°)
                sin_45 = 0.707  # sin(45°)
                
                watermark_stream = f"""
                q
                {opacity} {opacity} {opacity} rg
                {opacity} {opacity} {opacity} RG
                BT
                /F1 {font_size} Tf
                {cos_45} {sin_45} {-sin_45} {cos_45} {center_x} {center_y} Tm
                ({watermark_text}) Tj
                ET
                Q
                """
                
                # Add watermark as background (first in content stream)
                new_stream = pikepdf.Stream(pdf, watermark_stream.encode())
                
                if "/Contents" in page:
                    existing_content = page.Contents
                    if isinstance(existing_content, list):
                        # Add watermark as first element (background)
                        existing_content.insert(0, new_stream)
                    else:
                        # Single content stream, convert to array with watermark first
                        page.Contents = [new_stream, existing_content]
                else:
                    # No existing content
                    page.Contents = new_stream
            
            # Save modified PDF
            buffer = io.BytesIO()
            pdf.save(buffer)
            return buffer.getvalue()
            
    except Exception as e:
        logger.error(f"Error adding watermark to PDF: {str(e)}")
        raise


def extract_pages_pdf(data: bytes, page_numbers: List[int]) -> bytes:
    """Extract specific pages from PDF and create a new PDF with only those pages"""
    try:
        with pikepdf.open(io.BytesIO(data)) as src_pdf:
            total_pages = len(src_pdf.pages)
            
            # Validate page numbers
            invalid_pages = [p for p in page_numbers if p < 1 or p > total_pages]
            if invalid_pages:
                raise ValueError(f"Invalid page numbers {invalid_pages}. PDF has {total_pages} pages (1-{total_pages})")
            
            # Remove duplicates and sort
            unique_pages = sorted(list(set(page_numbers)))
            
            # Create new PDF with selected pages
            new_pdf = pikepdf.new()
            for page_num in unique_pages:
                new_pdf.pages.append(src_pdf.pages[page_num - 1])  # Convert to 0-based index
            
            # Save to buffer
            buffer = io.BytesIO()
            new_pdf.save(buffer)
            return buffer.getvalue()
            
    except Exception as e:
        logger.error(f"Error extracting pages from PDF: {str(e)}")
        raise
