# PDF Tools Website

This repository contains a minimal implementation of a PDF editing website. The backend is built with **FastAPI** and processes PDF files entirely in memory. The frontend is a simple HTML page using Tailwind CSS.

## Features
- Merge PDFs
- Split PDFs (range selection)
- Rotate PDFs
- Encrypt and decrypt PDFs

## Setup

### Backend
1. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt
   ```
2. Copy `.env.example` to `.env` and adjust settings if needed.
3. Run the server:
   ```bash
   uvicorn backend.main:app --reload
   ```

### Frontend
Open `frontend/index.html` in a browser. Adjust API URL if serving backend on a different host.

## Deployment
The application can be deployed to any platform that supports Python web services, such as AWS, GCP, or Vercel (via serverless functions). Ensure environment variables from `.env` are configured in the deployment settings.
