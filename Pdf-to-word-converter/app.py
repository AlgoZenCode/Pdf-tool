from flask import Flask, request, send_file, jsonify
import os
import subprocess
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB limit
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.lower().endswith('.pdf')

@app.route('/convert', methods=['POST'])
def convert_pdf_to_word():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF files are allowed'}), 400

    # Get conversion options from frontend
    output_format = request.form.get('outputFormat', 'docx')
    image_quality = request.form.get('imageQuality', 'medium')

    # Generate unique filenames
    file_id = str(uuid.uuid4())
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}.pdf")
    file.save(pdf_path)

    try:
        # Determine output extension
        output_ext = {
            'docx': 'docx',
            'doc': 'doc',
            'odt': 'odt'
        }.get(output_format, 'docx')
        
        output_filename = f"{file_id}.{output_ext}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # LibreOffice conversion command
        cmd = [
            'soffice',
            '--headless',
            '--convert-to', 
            f"{output_ext}:MS Word 2007 XML" if output_ext == 'docx' else output_ext,
            '--outdir', app.config['UPLOAD_FOLDER'],
            pdf_path
        ]
        
        # Add image quality options
        if image_quality == 'high':
            cmd.extend(['--writer', '--image-quality=100'])
        elif image_quality == 'low':
            cmd.extend(['--writer', '--image-quality=50'])
        
        # Run conversion
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            raise Exception(f"Conversion failed: {result.stderr}")

        if not os.path.exists(output_path):
            raise Exception("Conversion failed - no output file created")

        # Send the converted file back to frontend
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{secure_filename(file.filename).rsplit('.', 1)[0]}.{output_ext}"
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Cleanup temporary files
        for f in [pdf_path, output_path]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
