import io
import os
import sys
import logging
import time
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.pdf_utils import (
    merge_pdfs,
    split_pdf,
    rotate_pdf,
    encrypt_pdf,
    decrypt_pdf,
    resize_pdf,
    add_signature_pdf,
    add_watermark_pdf,
    extract_pages_pdf,
    pdf_to_images,
    images_to_pdf,
    extract_text_ocr,
)

load_dotenv()
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024))  # 20MB
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(
    title="The PDF Genie API",
    description="Professional PDF processing service - Files are processed in memory and never stored.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validate_file(file: UploadFile):
    """Validate uploaded PDF file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    if file.size is not None and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "The PDF Genie API is running"}


@app.get("/privacy")
async def privacy_info():
    """Privacy information endpoint"""
    return {
        "message": "Files are processed in memory and never stored.",
        "policy": "All uploaded files are processed entirely in memory and are automatically discarded after processing. No files or user data are stored on our servers.",
        "security": "All processing happens server-side with secure, temporary memory allocation."
    }


@app.post("/merge")
async def merge(files: List[UploadFile] = File(...)):
    """Merge multiple PDF files into one with improved performance and error handling"""
    start_time = time.time()
    
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least 2 files are required for merging")
    
    if len(files) > 10:  # Limit to prevent abuse
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed for merging")
    
    try:
        logger.info(f"Starting merge operation for {len(files)} files")
        pdf_data = []
        total_size = 0
        
        for i, f in enumerate(files):
            _validate_file(f)
            data = await f.read()
            file_size = len(data)
            total_size += file_size
            
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {f.filename} is too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
                )
            
            # Check total combined size
            if total_size > MAX_FILE_SIZE * 3:  # Allow up to 3x max size for total
                raise HTTPException(
                    status_code=400, 
                    detail="Combined file size too large. Please reduce the number or size of files."
                )
            
            pdf_data.append(data)
            logger.info(f"Processed file {i+1}/{len(files)}: {f.filename} ({file_size} bytes)")
        
        # Perform merge
        merged = merge_pdfs(pdf_data)
        processing_time = time.time() - start_time
        logger.info(f"Merge completed in {processing_time:.2f} seconds, output size: {len(merged)} bytes")
        
        return StreamingResponse(
            io.BytesIO(merged), 
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=merged.pdf"}
        )
        
    except ValueError as e:
        # Handle specific PDF validation errors with friendly messages
        logger.error(f"PDF validation error during merge: {str(e)}")
        error_msg = str(e)
        if "Invalid PDF" in error_msg:
            error_msg = "One or more uploaded files are corrupted or not valid PDF files. Please check your files and try again."
        elif "password" in error_msg.lower():
            error_msg = "One of the PDF files is password protected. Please decrypt it first or use a different file."
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Unexpected error during merge: {str(e)}")
        friendly_msg = "We couldn't merge your PDF files. This might be due to corrupted files or an internal error. Please try again with different files."
        raise HTTPException(status_code=500, detail=friendly_msg)


@app.post("/split")  
async def split(file: UploadFile = File(...), start: int = Form(...), end: int = Form(...)):
    """Split PDF by page range with improved performance and validation"""
    start_time = time.time()
    _validate_file(file)
    
    try:
        logger.info(f"Starting split operation: pages {start}-{end} from {file.filename}")
        data = await file.read()
        file_size = len(data)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if start < 1 or end < start:
            raise HTTPException(status_code=400, detail="Invalid page range. Start must be >= 1 and end >= start")
        
        result = split_pdf(data, start, end)
        processing_time = time.time() - start_time
        logger.info(f"Split completed in {processing_time:.2f} seconds, output size: {len(result)} bytes")
        
        filename = f"split_pages_{start}-{end}.pdf"
        return StreamingResponse(
            io.BytesIO(result), 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        logger.error(f"PDF validation error during split: {str(e)}")
        error_msg = str(e)
        if "exceeds total pages" in error_msg:
            error_msg = "The page range you specified is beyond the number of pages in your PDF. Please check the page numbers and try again."
        elif "Invalid PDF" in error_msg:
            error_msg = "The uploaded file is corrupted or not a valid PDF. Please try with a different file."
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Unexpected error during split: {str(e)}")
        friendly_msg = "We couldn't split your PDF file. Please check that your file is not corrupted and try again."
        raise HTTPException(status_code=500, detail=friendly_msg)


@app.post("/rotate")
async def rotate(file: UploadFile = File(...), angle: int = Form(...)):
    """Rotate all pages in PDF with improved performance and error handling"""
    start_time = time.time()
    _validate_file(file)
    
    try:
        logger.info(f"Starting rotate operation: {angle}° for {file.filename}")
        data = await file.read()
        file_size = len(data)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if angle not in [90, 180, 270]:
            raise HTTPException(status_code=400, detail="Angle must be 90, 180, or 270 degrees")
        
        result = rotate_pdf(data, angle)
        processing_time = time.time() - start_time
        logger.info(f"Rotate completed in {processing_time:.2f} seconds, output size: {len(result)} bytes")
        
        filename = f"rotated_{angle}deg.pdf"
        return StreamingResponse(
            io.BytesIO(result), 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        logger.error(f"PDF validation error during rotate: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during rotate: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error rotating PDF: {str(e)}")


@app.post("/encrypt")
async def encrypt(file: UploadFile = File(...), password: str = Form(...)):
    """Encrypt PDF with password with improved performance"""
    start_time = time.time()
    _validate_file(file)
    
    if not password or len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters long")
    
    try:
        logger.info(f"Starting encrypt operation for {file.filename}")
        data = await file.read()
        file_size = len(data)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        result = encrypt_pdf(data, password)
        processing_time = time.time() - start_time
        logger.info(f"Encrypt completed in {processing_time:.2f} seconds, output size: {len(result)} bytes")
        
        return StreamingResponse(
            io.BytesIO(result), 
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=encrypted.pdf"}
        )
        
    except ValueError as e:
        logger.error(f"PDF validation error during encrypt: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during encrypt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error encrypting PDF: {str(e)}")


@app.post("/decrypt")
async def decrypt(file: UploadFile = File(...), password: str = Form(...)):
    """Decrypt password-protected PDF with improved error handling"""
    start_time = time.time()
    _validate_file(file)
    
    if not password:
        raise HTTPException(status_code=400, detail="Password is required for decryption")
    
    try:
        logger.info(f"Starting decrypt operation for {file.filename}")
        data = await file.read()
        file_size = len(data)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        result = decrypt_pdf(data, password)
        processing_time = time.time() - start_time
        logger.info(f"Decrypt completed in {processing_time:.2f} seconds, output size: {len(result)} bytes")
        
        return StreamingResponse(
            io.BytesIO(result), 
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=decrypted.pdf"}
        )
        
    except ValueError as e:
        logger.error(f"Password error during decrypt: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during decrypt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error decrypting PDF: {str(e)}")


@app.post("/resize")
async def resize(file: UploadFile = File(...), quality: str = Form(default="medium")):
    """Resize/compress PDF with quality options"""
    start_time = time.time()
    _validate_file(file)
    
    if quality not in ["high", "medium", "low"]:
        raise HTTPException(status_code=400, detail="Quality must be 'high', 'medium', or 'low'")
    
    try:
        logger.info(f"Starting resize operation for {file.filename} with {quality} quality")
        data = await file.read()
        file_size = len(data)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        result = resize_pdf(data, quality)
        processing_time = time.time() - start_time
        original_size = len(data)
        compressed_size = len(result)
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        logger.info(f"Resize completed in {processing_time:.2f} seconds, compressed {compression_ratio:.1f}% (from {original_size} to {compressed_size} bytes)")
        
        filename = f"compressed_{quality}.pdf"
        return StreamingResponse(
            io.BytesIO(result), 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        logger.error(f"PDF validation error during resize: {str(e)}")
        error_msg = str(e)
        if "Invalid PDF" in error_msg:
            error_msg = "The uploaded file is corrupted or not a valid PDF. Please try with a different file."
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Unexpected error during resize: {str(e)}")
        friendly_msg = "We couldn't compress your PDF file. The file might be corrupted or contain unsupported content. Please try with a different file."
        raise HTTPException(status_code=500, detail=friendly_msg)


@app.post("/signature")
async def signature(file: UploadFile = File(...), signature_text: str = Form(...), position: str = Form(default="bottom-right")):
    """Add text signature to PDF"""
    start_time = time.time()
    _validate_file(file)
    
    if not signature_text or len(signature_text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Signature text is required")
    
    if len(signature_text) > 100:
        raise HTTPException(status_code=400, detail="Signature text must be 100 characters or less")
    
    valid_positions = ["bottom-right", "bottom-left", "top-right", "top-left", "center"]
    if position not in valid_positions:
        raise HTTPException(status_code=400, detail=f"Position must be one of: {', '.join(valid_positions)}")
    
    try:
        logger.info(f"Starting signature operation for {file.filename} with text: '{signature_text}' at {position}")
        data = await file.read()
        file_size = len(data)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        result = add_signature_pdf(data, signature_text.strip(), position)
        processing_time = time.time() - start_time
        logger.info(f"Signature completed in {processing_time:.2f} seconds, output size: {len(result)} bytes")
        
        filename = f"signed.pdf"
        return StreamingResponse(
            io.BytesIO(result), 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        logger.error(f"PDF validation error during signature: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during signature: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding signature: {str(e)}")


@app.post("/watermark")
async def watermark(file: UploadFile = File(...), watermark_text: str = Form(...), opacity: float = Form(default=0.3)):
    """Add watermark text to PDF"""
    start_time = time.time()
    _validate_file(file)
    
    if not watermark_text or len(watermark_text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Watermark text is required")
    
    if len(watermark_text) > 50:
        raise HTTPException(status_code=400, detail="Watermark text must be 50 characters or less")
    
    if not 0.1 <= opacity <= 1.0:
        raise HTTPException(status_code=400, detail="Opacity must be between 0.1 and 1.0")
    
    try:
        logger.info(f"Starting watermark operation for {file.filename} with text: '{watermark_text}' at {opacity} opacity")
        data = await file.read()
        file_size = len(data)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        result = add_watermark_pdf(data, watermark_text.strip(), opacity)
        processing_time = time.time() - start_time
        logger.info(f"Watermark completed in {processing_time:.2f} seconds, output size: {len(result)} bytes")
        
        filename = f"watermarked.pdf"
        return StreamingResponse(
            io.BytesIO(result), 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        logger.error(f"PDF validation error during watermark: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during watermark: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding watermark: {str(e)}")


@app.post("/extract")
async def extract_pages(file: UploadFile = File(...), pages: str = Form(...)):
    """Extract specific pages from PDF"""
    start_time = time.time()
    _validate_file(file)
    
    if not pages or not pages.strip():
        raise HTTPException(status_code=400, detail="Page numbers are required")
    
    try:
        # Parse page numbers (comma-separated)
        page_numbers = []
        for page_str in pages.split(','):
            page_str = page_str.strip()
            if '-' in page_str:
                # Range like "2-5"
                start_page, end_page = map(int, page_str.split('-'))
                page_numbers.extend(range(start_page, end_page + 1))
            else:
                # Single page
                page_numbers.append(int(page_str))
        
        if not page_numbers:
            raise HTTPException(status_code=400, detail="No valid page numbers provided")
        
        # Validate page numbers are positive
        if any(p < 1 for p in page_numbers):
            raise HTTPException(status_code=400, detail="Page numbers must be greater than 0")
        
        logger.info(f"Starting extract operation for {file.filename} with pages: {sorted(list(set(page_numbers)))}")
        data = await file.read()
        file_size = len(data)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        result = extract_pages_pdf(data, page_numbers)
        processing_time = time.time() - start_time
        logger.info(f"Extract completed in {processing_time:.2f} seconds, output size: {len(result)} bytes")
        
        # Create descriptive filename
        unique_pages = sorted(list(set(page_numbers)))
        if len(unique_pages) == 1:
            pages_desc = f"page_{unique_pages[0]}"
        elif len(unique_pages) <= 5:
            pages_desc = f"pages_{'_'.join(map(str, unique_pages))}"
        else:
            pages_desc = f"pages_{unique_pages[0]}_to_{unique_pages[-1]}"
        
        filename = f"extracted_{pages_desc}.pdf"
        return StreamingResponse(
            io.BytesIO(result), 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        logger.error(f"PDF validation error during extract: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during extract: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting pages: {str(e)}")


@app.post("/pdf-to-images")
async def pdf_to_images_endpoint(
    file: UploadFile = File(...),
    format: str = Form("png"),
    quality: int = Form(95)
):
    """Convert PDF pages to images and return as ZIP file"""
    start_time = time.time()
    
    _validate_file(file)
    
    if format not in ["png", "jpg", "jpeg"]:
        raise HTTPException(status_code=400, detail="Format must be 'png', 'jpg', or 'jpeg'")
    
    if not (1 <= quality <= 100):
        raise HTTPException(status_code=400, detail="Quality must be between 1 and 100")
    
    try:
        logger.info(f"Starting PDF to images conversion: {file.filename}")
        data = await file.read()
        
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Convert PDF to images
        result = pdf_to_images(data, format, quality)
        processing_time = time.time() - start_time
        logger.info(f"PDF to images conversion completed in {processing_time:.2f} seconds, output size: {len(result)} bytes")
        
        # Create filename
        base_name = file.filename.rsplit('.', 1)[0] if file.filename else "pdf"
        filename = f"{base_name}_images.zip"
        
        return StreamingResponse(
            io.BytesIO(result), 
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        logger.error(f"PDF validation error during conversion: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during PDF to images conversion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error converting PDF to images: {str(e)}")


@app.post("/images-to-pdf")
async def images_to_pdf_endpoint(files: List[UploadFile] = File(...)):
    """Convert multiple images to a single PDF"""
    start_time = time.time()
    
    if len(files) < 1:
        raise HTTPException(status_code=400, detail="At least 1 image file is required")
    
    if len(files) > 50:  # Limit to prevent abuse
        raise HTTPException(status_code=400, detail="Maximum 50 image files allowed")
    
    try:
        logger.info(f"Starting images to PDF conversion for {len(files)} files")
        image_data = []
        filenames = []
        total_size = 0
        
        for i, f in enumerate(files):
            if not f.filename:
                raise HTTPException(status_code=400, detail=f"File {i+1} has no name")
            
            # Check if it's an image file
            if not f.content_type or not f.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail=f"File {f.filename} is not an image")
            
            data = await f.read()
            file_size = len(data)
            total_size += file_size
            
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {f.filename} is too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
                )
            
            # Check total combined size
            if total_size > MAX_FILE_SIZE * 5:  # Allow up to 5x max size for total
                raise HTTPException(
                    status_code=400, 
                    detail="Combined file size too large. Please reduce the number or size of images."
                )
            
            image_data.append(data)
            filenames.append(f.filename)
            logger.info(f"Processed image {i+1}/{len(files)}: {f.filename} ({file_size} bytes)")
        
        # Convert images to PDF
        result = images_to_pdf(image_data, filenames)
        processing_time = time.time() - start_time
        logger.info(f"Images to PDF conversion completed in {processing_time:.2f} seconds, output size: {len(result)} bytes")
        
        return StreamingResponse(
            io.BytesIO(result), 
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=images_to_pdf.pdf"}
        )
        
    except ValueError as e:
        logger.error(f"Image validation error during conversion: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during images to PDF conversion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error converting images to PDF: {str(e)}")


@app.post("/extract-text")
async def extract_text_endpoint(file: UploadFile = File(...)):
    """Extract text from PDF using OCR"""
    start_time = time.time()
    
    _validate_file(file)
    
    try:
        logger.info(f"Starting text extraction from: {file.filename}")
        data = await file.read()
        
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Extract text from PDF
        extracted_text = extract_text_ocr(data)
        processing_time = time.time() - start_time
        logger.info(f"Text extraction completed in {processing_time:.2f} seconds")
        
        return JSONResponse({
            "text": extracted_text,
            "filename": file.filename,
            "processing_time": round(processing_time, 2)
        })
        
    except ValueError as e:
        logger.error(f"PDF validation error during text extraction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during text extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

