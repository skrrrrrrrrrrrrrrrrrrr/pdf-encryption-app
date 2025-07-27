import io
from typing import List

import pikepdf
from PyPDF2 import PdfReader, PdfWriter


def merge_pdfs(files: List[bytes]) -> bytes:
    writer = PdfWriter()
    for data in files:
        reader = PdfReader(io.BytesIO(data))
        for page in reader.pages:
            writer.add_page(page)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def split_pdf(data: bytes, start: int, end: int) -> bytes:
    reader = PdfReader(io.BytesIO(data))
    writer = PdfWriter()
    pages = reader.pages[start - 1:end]
    for page in pages:
        writer.add_page(page)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def rotate_pdf(data: bytes, angle: int) -> bytes:
    reader = PdfReader(io.BytesIO(data))
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def encrypt_pdf(data: bytes, password: str) -> bytes:
    pdf = pikepdf.Pdf.open(io.BytesIO(data))
    buffer = io.BytesIO()
    pdf.save(buffer, encryption=pikepdf.Encryption(owner=password, user=password, R=4))
    return buffer.getvalue()


def decrypt_pdf(data: bytes, password: str) -> bytes:
    pdf = pikepdf.open(io.BytesIO(data), password=password)
    buffer = io.BytesIO()
    pdf.save(buffer)
    return buffer.getvalue()
