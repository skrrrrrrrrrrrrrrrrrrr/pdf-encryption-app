# PDF Tools - Professional PDF Processing Platform

![PDF Tools Screenshot](https://github.com/user-attachments/assets/5b0ef2e0-ba3e-4b2f-8d4a-8cc0c7d8b5dc)

A modern, secure, and user-friendly web application for processing PDF documents. Built with FastAPI backend and a responsive frontend, this platform offers professional-grade PDF manipulation tools with privacy-first design.

## 🔒 Privacy & Security Features

- **Files processed in memory only** - No files are ever stored on disk
- **Zero data retention** - All uploaded files are automatically discarded after processing
- **Secure processing** - All operations happen server-side with temporary memory allocation
- **CORS protection** - Configurable cross-origin resource sharing
- **Input validation** - Robust file type and size validation
- **Error handling** - Comprehensive error handling with user-friendly messages

## ⚡ Features

### Core PDF Operations
- **📄 Merge PDFs** - Combine multiple PDF files into a single document
- **✂️ Split PDFs** - Extract specific page ranges from documents
- **🔄 Rotate PDFs** - Rotate all pages by 90°, 180°, or 270°
- **🔒 Encrypt PDFs** - Password-protect documents with strong encryption
- **🔓 Decrypt PDFs** - Remove password protection from encrypted files

### User Experience
- **🎨 Modern UI** - Clean, responsive design with intuitive navigation
- **📱 Mobile-friendly** - Optimized for all device sizes
- **🖱️ Drag & Drop** - Easy file upload with drag-and-drop support
- **⏳ Progress Indicators** - Real-time feedback during processing
- **✅ Validation** - Instant file type and size validation
- **🔔 Smart Notifications** - Clear success and error messages

## 🚀 Quick Start

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pdf-encryption-app
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your settings
   ```

4. **Start the backend**
   ```bash
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Serve the frontend**
   ```bash
   cd frontend
   python -m http.server 3000
   ```

6. **Open your browser**
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs

### Production Deployment with Docker

1. **Quick deployment**
   ```bash
   ./deploy.sh
   ```

2. **Manual Docker setup**
   ```bash
   # Build and start services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   
   # Stop services
   docker-compose down
   ```

## 🏗️ Architecture

### Backend (FastAPI)
- **Modular design** - Clean separation of concerns
- **In-memory processing** - No temporary files created
- **Comprehensive validation** - File type, size, and content validation
- **Error handling** - Detailed error responses with user-friendly messages
- **Health checks** - Built-in health monitoring
- **CORS support** - Configurable cross-origin requests

### File Structure
```
pdf-encryption-app/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── utils/
│   │   └── pdf_utils.py     # PDF processing utilities
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example        # Environment variables template
│   └── .env                # Environment variables (create from example)
├── frontend/
│   ├── index.html          # Modern frontend with CDN resources
│   └── index_offline.html  # Self-contained version
├── docker-compose.yml      # Docker services configuration
├── Dockerfile             # Backend container definition
├── nginx.conf             # Nginx reverse proxy configuration
├── deploy.sh              # Deployment script
└── README.md              # This file
```

### Dependencies

#### Backend
- **FastAPI** - Modern web framework for APIs
- **Uvicorn** - ASGI server for FastAPI
- **PyPDF2** - PDF manipulation library
- **pikepdf** - Advanced PDF processing with encryption support
- **python-multipart** - File upload handling
- **python-dotenv** - Environment variable management

#### Frontend
- **Pure HTML/CSS/JavaScript** - No build process required
- **TailwindCSS** - Modern CSS framework (CDN)
- **Alpine.js** - Lightweight JavaScript framework (CDN)
- **Font Awesome** - Icon library (CDN)

## 🔧 Configuration

### Environment Variables

Create `backend/.env` from `backend/.env.example`:

```env
# Maximum file size in bytes (default: 20MB)
MAX_FILE_SIZE=20971520

# CORS allowed origins (comma-separated)
ALLOWED_ORIGINS=*

# Server port (for production deployment)
PORT=8000

# Environment
ENVIRONMENT=development
```

### Production Settings

For production deployment:
- Set `ALLOWED_ORIGINS` to your domain(s)
- Use a reverse proxy (Nginx included)
- Enable HTTPS
- Set appropriate file size limits
- Configure monitoring and logging

## 🌐 Deployment Options

### 1. Docker (Recommended)
```bash
# Using the deployment script
./deploy.sh

# Or manually
docker-compose up -d
```

### 2. Heroku
```bash
# Install Heroku CLI and login
heroku create your-pdf-tools-app

# Set environment variables
heroku config:set MAX_FILE_SIZE=20971520
heroku config:set ALLOWED_ORIGINS=https://your-pdf-tools-app.herokuapp.com

# Deploy
git push heroku main
```

### 3. Railway
```bash
# Install Railway CLI
railway login
railway init
railway up
```

### 4. Render
1. Connect your GitHub repository
2. Set build command: `pip install -r backend/requirements.txt`
3. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables

### 5. DigitalOcean App Platform
1. Create new app from GitHub
2. Configure build and run commands
3. Set environment variables
4. Deploy

## 🔌 API Reference

### Base URL
- Development: `http://localhost:8000`
- Production: `https://your-domain.com/api`

### Endpoints

#### Health Check
```http
GET /health
```
Returns server health status.

#### Privacy Information
```http
GET /privacy
```
Returns privacy policy information.

#### Merge PDFs
```http
POST /merge
Content-Type: multipart/form-data

files: [File, File, ...] (minimum 2 files)
```

#### Split PDF
```http
POST /split
Content-Type: multipart/form-data

file: File
start: int (starting page number)
end: int (ending page number)
```

#### Rotate PDF
```http
POST /rotate
Content-Type: multipart/form-data

file: File
angle: int (90, 180, or 270)
```

#### Encrypt PDF
```http
POST /encrypt
Content-Type: multipart/form-data

file: File
password: string (minimum 4 characters)
```

#### Decrypt PDF
```http
POST /decrypt
Content-Type: multipart/form-data

file: File
password: string
```

## 🧪 Testing

### Manual Testing
1. Start the application
2. Upload test PDF files
3. Try each operation:
   - Merge multiple PDFs
   - Split a PDF by page range
   - Rotate pages
   - Encrypt with password
   - Decrypt encrypted PDF

### File Validation Testing
- Upload non-PDF files (should be rejected)
- Upload files larger than 20MB (should be rejected)
- Test with corrupted PDF files
- Test with password-protected PDFs

## 🔍 Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Ensure you're running from the project root
cd pdf-encryption-app
python -m uvicorn backend.main:app --reload
```

#### CORS errors
```bash
# Check ALLOWED_ORIGINS in backend/.env
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

#### File upload failures
- Check file size limits (MAX_FILE_SIZE)
- Ensure files are valid PDFs
- Check network connectivity

#### Memory issues
- Reduce MAX_FILE_SIZE for constrained environments
- Monitor memory usage during processing

### Logs
```bash
# Docker logs
docker-compose logs -f

# Local development
# Check console output for errors
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📜 License

This project is open source and available under the [MIT License](LICENSE).

## 🔮 Future Enhancements

- [ ] Batch processing for multiple operations
- [ ] PDF metadata editing
- [ ] Digital signature support
- [ ] OCR text extraction
- [ ] PDF compression
- [ ] Watermark addition
- [ ] Page rearrangement
- [ ] Form filling
- [ ] Advanced encryption options
- [ ] API rate limiting
- [ ] User authentication (optional)
- [ ] Processing history (optional)

## 📞 Support

For support, please:
1. Check the troubleshooting section
2. Review the API documentation
3. Open an issue on GitHub
4. Contact the development team

---

**Privacy First**: This application processes all files in memory and never stores user data. Your documents are secure and private.
