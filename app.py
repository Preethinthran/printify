import os
import zipfile
import io
from io import BytesIO
from flask import Flask, render_template, request, redirect, send_file, jsonify, session
from PIL import Image, ImageDraw, ImageFont
from docx2pdf import convert as docx_to_pdf
from fpdf import FPDF
import tempfile
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger  
import uuid

app = Flask(__name__)
app.secret_key = 'supersecretkey123'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/certificate')
def certificate():
    return render_template('certificate.html')

@app.route('/converter')
def converter():
    return render_template('converter.html')

@app.route('/upload_template', methods=['POST'])
def upload_template():
    file = request.files['template']
    if file:
        filename = file.filename
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        img = Image.open(file)
        maxWidth, maxHeight = 2480, 3508
        if img.width > maxWidth or img.height > maxHeight:
            img.thumbnail((maxWidth, maxHeight))
        img.save(save_path)

        return jsonify({'success': True, 'filename': filename})
    return jsonify({'success': False})

@app.route('/generate', methods=['POST'])
def generate_certificates():
    template_name = request.form['template_name']
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], template_name)

    raw_names = request.form['names']
    names = [name.strip() for name in raw_names.replace(',', '\n').split('\n') if name.strip()]

    font_color = request.form['font_color'].lower()
    font_size = int(request.form['font_size'])
    selected_font = request.form['font_style']
    font_path = os.path.join("static", "fonts", selected_font)

    x = int(request.form['x_pos'])
    y = int(request.form['y_pos'])

    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()

    image_paths = []

    for name in names:
        image = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.text((x, y), name, fill=font_color, font=font, anchor='la')

        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"certificate_{name}.png")
        image.save(output_path)
        image_paths.append(output_path)

    image_urls = ["/" + path.replace("\\", "/") for path in image_paths]
    return jsonify({'success': True, 'images': image_urls})

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    image_paths = request.json['images']
    images = [Image.open(path[1:]).convert('RGB') for path in image_paths]

    pdf_buffer = BytesIO()
    images[0].save(pdf_buffer, save_all=True, append_images=images[1:], format='PDF')
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name='certificates.pdf')

@app.route('/convert', methods=['POST'])
def convert_to_pdf():
    uploaded_files = request.files.getlist('files')
    if not uploaded_files:
        return "No files uploaded", 400

    pdf_paths = []
    temp_dir = tempfile.mkdtemp()

    for file in uploaded_files:
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)

        if ext in ['.jpg', '.jpeg', '.png']:
            image = Image.open(file_path).convert('RGB')
            image_pdf_path = os.path.join(temp_dir, filename + ".pdf")
            image.save(image_pdf_path)
            pdf_paths.append(image_pdf_path)

        elif ext in ['.doc', '.docx']:
            word_pdf_path = os.path.join(temp_dir, filename + "_converted.pdf")
            docx_to_pdf(file_path, word_pdf_path)
            if os.path.exists(word_pdf_path):
                pdf_paths.append(word_pdf_path)

        elif ext == '.pdf':
            pdf_paths.append(file_path)

    if not pdf_paths:
        return "No valid files to convert.", 400

    final_pdf_path = os.path.join(temp_dir, "final_merged.pdf")
    merger = PdfMerger()
    for path in pdf_paths:
        merger.append(path)
    merger.write(final_pdf_path)
    merger.close()

    return send_file(final_pdf_path, as_attachment=True, download_name="converted.pdf", mimetype="application/pdf")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)
