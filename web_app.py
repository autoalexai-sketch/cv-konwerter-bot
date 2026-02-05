from flask import Flask, render_template, request, send_file
import os
import subprocess
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['OUTPUT_FOLDER'] = '/tmp/outputs'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    file = request.files.get('file')
    if file and file.filename.lower().endswith(('.docx', '.doc')):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{timestamp}_{file.filename}')
        file.save(input_path)
        try:
            subprocess.run([
                'soffice', '--headless', 
                '-env:UserInstallation=file:///tmp/.libreoffice', 
                '--convert-to', 'pdf', 
                '--outdir', app.config['OUTPUT_FOLDER'], 
                input_path
            ], check=True, timeout=30)
            
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{timestamp}_{os.path.splitext(file.filename)[0]}.pdf')
            
            # 🔑 КРИТИЧЕСКИ ВАЖНО: правильные заголовки для скачивания
            return send_file(
                output_path, 
                as_attachment=True,
                download_name=f"cv_{timestamp}.pdf",
                mimetype="application/pdf"
            )
        except Exception as e:
            return f"Błąd konwersji: {str(e)[:100]}", 500
        finally:
            # Удаляем временные файлы (соответствие RODO)
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
    return "Nieprawidłowy plik", 400

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
