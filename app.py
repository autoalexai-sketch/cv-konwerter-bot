# app.py
from flask import Flask, render_template, request, send_file
import os
import subprocess
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    file = request.files['file']
    if file and file.filename.endswith('.docx'):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{timestamp}.docx')
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{timestamp}.pdf')
        file.save(input_path)
        try:
            subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', app.config['OUTPUT_FOLDER'], input_path], check=True)
            return send_file(output_path, as_attachment=True)
        except:
            return "Błąd konwersji", 500
    return "Nieprawidłowy plik", 400

if __name__ == '__main__':
    app.run(debug=True)
