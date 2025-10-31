# DocMorph - The All-in-One PDF Toolkit

## Overview
DocMorph is a comprehensive Flask-based PDF manipulation toolkit with a professional dark-themed interface. It provides all essential PDF operations including merge, split, convert, compress, rotate, and encrypt, plus secure file and text sharing capabilities.

## Recent Changes
- **October 31, 2025**: Initial project setup and convert feature enhancement
  - Installed Python 3.11 and all required dependencies
  - Created Flask application with all PDF operation routes
  - Implemented dark-themed UI with Bootstrap 5
  - Added drag-and-drop file upload functionality
  - Configured automatic temporary file cleanup for privacy
  - Fixed convert feature with improved error handling
  - Added comprehensive TXT format support (PDF↔TXT, DOCX↔TXT)

## Project Architecture

### Backend (Flask)
- **app.py**: Main Flask application with all routes
- **Dependencies**:
  - Flask 3.0.0 - Web framework
  - PyPDF2 3.0.1 - PDF manipulation (merge, split, rotate, encrypt)
  - pdf2docx 0.5.6 - PDF to Word conversion
  - python-pptx 0.6.23 - PowerPoint manipulation
  - python-docx 1.1.0 - Word document processing
  - reportlab 4.0.7 - PDF generation
  - Pillow 10.1.0 - Image processing
  - gunicorn 21.2.0 - Production WSGI server

### Frontend
- **Templates** (templates/): Jinja2 HTML templates with dark theme
  - base.html - Base template with navigation
  - index.html - Homepage with feature cards
  - merge.html, split.html, convert.html, compress.html, rotate.html, secure.html, share.html
- **Static Files**:
  - static/css/style.css - Custom dark theme styling
  - static/js/script.js - Drag-and-drop and file handling
- **Libraries**:
  - Bootstrap 5.3.0 - UI framework
  - Font Awesome 6.4.0 - Icons

### Directory Structure
```
.
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
├── static/
│   ├── css/             # Stylesheets
│   ├── js/              # JavaScript files
│   ├── uploads/         # Temporary processed files
│   └── shared/          # Temporary shared files
└── replit.md            # This file
```

## Features
1. **Merge PDFs**: Combine multiple PDF files into one
2. **Split PDFs**: Extract specific pages or page ranges
3. **Convert Files**: Convert between PDF, Word (DOCX), and Text (TXT) formats
   - Supported conversions: PDF→DOCX, PDF→TXT, DOCX→PDF, DOCX→TXT, TXT→PDF, TXT→DOCX
4. **Compress PDFs**: Reduce file size while maintaining quality
5. **Rotate PDFs**: Rotate pages in 90-degree increments
6. **Secure PDFs**: Add password protection
7. **Share Files & Text**: Generate temporary sharing links (24-hour expiry, up to 1GB)

## Security Features
- Automatic file cleanup after 1 hour
- Temporary sharing links with 24-hour expiration
- SESSION_SECRET environment variable for Flask sessions
- Secure filename handling with Werkzeug
- File size limit: 1GB maximum

## User Preferences
None set yet.

## Notes
- All uploaded files are automatically cleaned up after 1 hour
- Shared files expire after 24 hours
- App runs on port 5000
- Dark theme optimized for reduced eye strain
