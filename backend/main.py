import io
import os
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from utils.pdf_utils import (
    merge_pdfs,
    split_pdf,
    rotate_pdf,
    encrypt_pdf,
    decrypt_pdf,
)

load_dotenv()
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024))  # 20MB

app = FastAPI(title="PDF Tools")


def _validate_file(file: UploadFile):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    if file.size is not None and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")


@app.post("/merge")
async def merge(files: List[UploadFile] = File(...)):
    for f in files:
        _validate_file(f)
        data = await f.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
    merged = merge_pdfs([await f.read() for f in files])
    return StreamingResponse(io.BytesIO(merged), media_type="application/pdf")


@app.post("/split")
async def split(file: UploadFile = File(...), start: int = Form(...), end: int = Form(...)):
    _validate_file(file)
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    result = split_pdf(data, start, end)
    return StreamingResponse(io.BytesIO(result), media_type="application/pdf")


@app.post("/rotate")
async def rotate(file: UploadFile = File(...), angle: int = Form(...)):
    _validate_file(file)
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    result = rotate_pdf(data, angle)
    return StreamingResponse(io.BytesIO(result), media_type="application/pdf")


@app.post("/encrypt")
async def encrypt(file: UploadFile = File(...), password: str = Form(...)):
    _validate_file(file)
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    result = encrypt_pdf(data, password)
    return StreamingResponse(io.BytesIO(result), media_type="application/pdf")


@app.post("/decrypt")
async def decrypt(file: UploadFile = File(...), password: str = Form(...)):
    _validate_file(file)
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    result = decrypt_pdf(data, password)
    return StreamingResponse(io.BytesIO(result), media_type="application/pdf")

