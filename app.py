import os
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['COMPRESSED_FOLDER'] = 'compressed'

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['COMPRESSED_FOLDER'], exist_ok=True)

def check_ghostscript():
    try:
        subprocess.run(['gs', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def compress_pdf(input_path, output_path, compression_level):
    ghostscript_cmd = [
        'gs',
        '-sDEVICE=pdfwrite',
        f'-dPDFSETTINGS=/{compression_level}',
        '-dNOPAUSE',
        '-dQUIET',
        '-dBATCH',
        f'-sOutputFile={output_path}',
        input_path
    ]
    
    try:
        subprocess.run(ghostscript_cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        app.logger.error(f"Ghostscript error: {e}")
        return False

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/compress', methods=['POST'])
def compress():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400
    
    compression_level = request.form.get('compression_level', 'ebook')
    if compression_level not in ['screen', 'ebook', 'printer', 'prepress', 'default']:
        compression_level = 'ebook'
    
    # Save original file
    filename = secure_filename(file.filename)
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(original_path)
    
    # Generate output filename
    base, ext = os.path.splitext(filename)
    compressed_filename = f"{base}_compressed{ext}"
    compressed_path = os.path.join(app.config['COMPRESSED_FOLDER'], compressed_filename)
    
    # Compress the PDF
    if not compress_pdf(original_path, compressed_path, compression_level):
        return jsonify({'error': 'Failed to compress PDF'}), 500
    
    # Get file sizes
    original_size = os.path.getsize(original_path)
    compressed_size = os.path.getsize(compressed_path)
    
    return jsonify({
        'original_size': original_size,
        'compressed_size': compressed_size,
        'download_url': f'/download/{compressed_filename}',
        'filename': compressed_filename
    })

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(
        app.config['COMPRESSED_FOLDER'],
        filename,
        as_attachment=True
    )

@app.before_request
def check_ghostscript_installed():
    if request.path == '/' or request.path.startswith('/static'):
        return
    
    if not check_ghostscript():
        return jsonify({
            'error': 'Ghostscript not installed',
            'message': 'Please install Ghostscript to use this service'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
