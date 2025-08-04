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
)

load_dotenv()
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024))  # 20MB
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(
    title="PDF Tools API",
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
    return {"status": "healthy", "message": "PDF Tools API is running"}


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
        # Handle specific PDF validation errors
        logger.error(f"PDF validation error during merge: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during merge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error merging PDFs: {str(e)}")


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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during split: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error splitting PDF: {str(e)}")


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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

