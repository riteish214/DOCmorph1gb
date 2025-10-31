import os
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify, url_for
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
from pdf2docx import Converter
from docx import Document
from pptx import Presentation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SHARED_FOLDER'] = 'static/shared'

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'}
shared_links = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def cleanup_old_files():
    upload_folder = Path(app.config['UPLOAD_FOLDER'])
    shared_folder = Path(app.config['SHARED_FOLDER'])
    current_time = time.time()
    
    for folder in [upload_folder, shared_folder]:
        if folder.exists():
            for file_path in folder.iterdir():
                if file_path.is_file() and file_path.name != '.gitkeep':
                    if current_time - file_path.stat().st_mtime > 3600:
                        try:
                            file_path.unlink()
                        except:
                            pass

@app.route('/')
def index():
    cleanup_old_files()
    return render_template('index.html')

@app.route('/merge', methods=['GET', 'POST'])
def merge_pdfs():
    if request.method == 'POST':
        try:
            files = request.files.getlist('files')
            if len(files) < 2:
                return jsonify({'error': 'Please upload at least 2 PDF files'}), 400
            
            pdf_writer = PdfWriter()
            
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    pdf_reader = PdfReader(file.stream)
                    for page in pdf_reader.pages:
                        pdf_writer.add_page(page)
            
            output_filename = f'merged_{int(time.time())}.pdf'
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            return jsonify({
                'success': True,
                'download_url': url_for('download_file', filename=output_filename)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('merge.html')

@app.route('/split', methods=['GET', 'POST'])
def split_pdf():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            page_ranges = request.form.get('pages', '')
            
            if not file or not file.filename or not allowed_file(file.filename):
                return jsonify({'error': 'Please upload a valid PDF file'}), 400
            
            pdf_reader = PdfReader(file.stream)
            total_pages = len(pdf_reader.pages)
            
            if not page_ranges:
                page_ranges = f'1-{total_pages}'
            
            pdf_writer = PdfWriter()
            
            for page_range in page_ranges.split(','):
                page_range = page_range.strip()
                if '-' in page_range:
                    start, end = map(int, page_range.split('-'))
                    for i in range(start - 1, min(end, total_pages)):
                        pdf_writer.add_page(pdf_reader.pages[i])
                else:
                    page_num = int(page_range)
                    if 1 <= page_num <= total_pages:
                        pdf_writer.add_page(pdf_reader.pages[page_num - 1])
            
            output_filename = f'split_{int(time.time())}.pdf'
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            return jsonify({
                'success': True,
                'download_url': url_for('download_file', filename=output_filename),
                'total_pages': total_pages
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('split.html')

@app.route('/convert', methods=['GET', 'POST'])
def convert_file():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            convert_to = request.form.get('convert_to', 'pdf')
            
            if not file or not file.filename:
                return jsonify({'error': 'Please upload a file'}), 400
            
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            temp_input = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_{int(time.time())}.{file_ext}')
            file.save(temp_input)
            
            output_filename = f'converted_{int(time.time())}.{convert_to}'
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            if file_ext == 'pdf' and convert_to == 'docx':
                cv = Converter(temp_input)
                cv.convert(output_path)
                cv.close()
            elif file_ext in ['doc', 'docx'] and convert_to == 'pdf':
                doc = Document(temp_input)
                packet = io.BytesIO()
                can = canvas.Canvas(packet, pagesize=letter)
                y_position = 750
                
                for para in doc.paragraphs:
                    text = para.text
                    if text.strip():
                        can.drawString(50, y_position, text[:100])
                        y_position -= 20
                        if y_position < 50:
                            can.showPage()
                            y_position = 750
                
                can.save()
                packet.seek(0)
                
                with open(output_path, 'wb') as f:
                    f.write(packet.read())
            else:
                os.remove(temp_input)
                return jsonify({'error': 'Conversion not supported'}), 400
            
            os.remove(temp_input)
            
            return jsonify({
                'success': True,
                'download_url': url_for('download_file', filename=output_filename)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('convert.html')

@app.route('/compress', methods=['GET', 'POST'])
def compress_pdf():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            
            if not file or not file.filename or not allowed_file(file.filename):
                return jsonify({'error': 'Please upload a valid PDF file'}), 400
            
            pdf_reader = PdfReader(file.stream)
            pdf_writer = PdfWriter()
            
            for page in pdf_reader.pages:
                page.compress_content_streams()
                pdf_writer.add_page(page)
            
            output_filename = f'compressed_{int(time.time())}.pdf'
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            original_size = len(file.read())
            file.seek(0)
            compressed_size = os.path.getsize(output_path)
            reduction = ((original_size - compressed_size) / original_size) * 100
            
            return jsonify({
                'success': True,
                'download_url': url_for('download_file', filename=output_filename),
                'original_size': original_size,
                'compressed_size': compressed_size,
                'reduction': round(reduction, 2)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('compress.html')

@app.route('/rotate', methods=['GET', 'POST'])
def rotate_pdf():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            rotation = int(request.form.get('rotation', 90))
            
            if not file or not file.filename or not allowed_file(file.filename):
                return jsonify({'error': 'Please upload a valid PDF file'}), 400
            
            pdf_reader = PdfReader(file.stream)
            pdf_writer = PdfWriter()
            
            for page in pdf_reader.pages:
                page.rotate(rotation)
                pdf_writer.add_page(page)
            
            output_filename = f'rotated_{int(time.time())}.pdf'
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            return jsonify({
                'success': True,
                'download_url': url_for('download_file', filename=output_filename)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('rotate.html')

@app.route('/secure', methods=['GET', 'POST'])
def secure_pdf():
    if request.method == 'POST':
        try:
            file = request.files.get('file')
            password = request.form.get('password', '')
            
            if not file or not file.filename or not allowed_file(file.filename):
                return jsonify({'error': 'Please upload a valid PDF file'}), 400
            
            if not password:
                return jsonify({'error': 'Please provide a password'}), 400
            
            pdf_reader = PdfReader(file.stream)
            pdf_writer = PdfWriter()
            
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            pdf_writer.encrypt(password)
            
            output_filename = f'secured_{int(time.time())}.pdf'
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            with open(output_path, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            return jsonify({
                'success': True,
                'download_url': url_for('download_file', filename=output_filename)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('secure.html')

@app.route('/share', methods=['GET', 'POST'])
def share():
    if request.method == 'POST':
        try:
            share_type = request.form.get('share_type', 'file')
            
            if share_type == 'file':
                file = request.files.get('file')
                if not file or not file.filename:
                    return jsonify({'error': 'Please upload a file'}), 400
                
                filename = secure_filename(file.filename)
                unique_id = secrets.token_urlsafe(16)
                file_path = os.path.join(app.config['SHARED_FOLDER'], f'{unique_id}_{filename}')
                file.save(file_path)
                
                share_link = url_for('get_shared', share_id=unique_id, _external=True)
                expiry = datetime.now() + timedelta(hours=24)
                
                shared_links[unique_id] = {
                    'type': 'file',
                    'path': file_path,
                    'filename': filename,
                    'expiry': expiry
                }
            else:
                text_content = request.form.get('text_content', '')
                if not text_content:
                    return jsonify({'error': 'Please provide text content'}), 400
                
                unique_id = secrets.token_urlsafe(16)
                expiry = datetime.now() + timedelta(hours=24)
                
                shared_links[unique_id] = {
                    'type': 'text',
                    'content': text_content,
                    'expiry': expiry
                }
                
                share_link = url_for('get_shared', share_id=unique_id, _external=True)
            
            return jsonify({
                'success': True,
                'share_link': share_link,
                'expiry': expiry.strftime('%Y-%m-%d %H:%M:%S')
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return render_template('share.html')

@app.route('/shared/<share_id>')
def get_shared(share_id):
    if share_id not in shared_links:
        return 'Link not found or expired', 404
    
    shared = shared_links[share_id]
    
    if datetime.now() > shared['expiry']:
        del shared_links[share_id]
        return 'Link expired', 410
    
    if shared['type'] == 'file':
        return send_file(shared['path'], as_attachment=True, download_name=shared['filename'])
    else:
        return render_template('shared_text.html', content=shared['content'])

@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return 'File not found', 404

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SHARED_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
