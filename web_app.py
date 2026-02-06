from flask import Flask, render_template, request, send_file, redirect, url_for
import os
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

# Импорты для генерации шаблонов и отправки писем
try:
    from email_service_sendgrid import send_email_with_attachments
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    EMAIL_SERVICE_AVAILABLE = False
    print("⚠️ Email service not available (install sendgrid)")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['OUTPUT_FOLDER'] = '/tmp/outputs'
app.config['TEMPLATES_FOLDER'] = 'templates_cv'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# --- ГЛАВНАЯ СТРАНИЦА ---
@app.route('/')
def index():
    return render_template('index.html')

# --- КОНВЕРТАЦИЯ ФАЙЛОВ (ОТ БОТА И САЙТА) ---
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
            
            # ✅ Правильные заголовки для скачивания
            return send_file(
                output_path, 
                as_attachment=True,
                download_name=f"cv_{timestamp}.pdf",
                mimetype="application/pdf"
            )
        except Exception as e:
            return f"Błąd konwersji: {str(e)[:100]}", 500
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
    return "Nieprawidłowy plik", 400

# --- ПРЕМИУМ: ГЕНЕРАЦИЯ ШАБЛОНОВ И ОТПРАВКА НА EMAIL ---
@app.route('/premium', methods=['POST'])
def premium():
    try:
        # Получаем данные из формы
        name = request.form.get('name', 'Anonim')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        city = request.form.get('city', 'Kraków')
        
        # Валидация
        if not email or '@' not in email:
            return "Błąd: Nieprawidłowy email", 400
        
        # Генерируем шаблоны из папки templates_cv/
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        temp_output = Path(f'/tmp/premium_{timestamp}')
        temp_output.mkdir(parents=True, exist_ok=True)
        
        # Копируем шаблоны и заменяем плейсхолдеры
        cv_template_path = Path(app.config['TEMPLATES_FOLDER']) / 'cv_template.docx'
        cover_template_path = Path(app.config['TEMPLATES_FOLDER']) / 'cover_letter_template.docx'
        
        if not cv_template_path.exists():
            return "Błąd: Szablon CV nie istnieje", 500
        
        # Копируем и редактируем шаблон CV
        cv_output = temp_output / f'CV_{name.replace(" ", "_")}.docx'
        shutil.copy(cv_template_path, cv_output)
        
        # Здесь можно добавить замену плейсхолдеров в файле (через python-docx)
        # Для простоты оставляем как есть
        
        # Конвертируем в PDF
        cv_pdf = temp_output / f'CV_{name.replace(" ", "_")}.pdf'
        subprocess.run([
            'soffice', '--headless',
            '--convert-to', 'pdf',
            '--outdir', str(temp_output),
            str(cv_output)
        ], check=True, timeout=30)
        
        # Подготавливаем файлы для отправки
        attachments = []
        if cv_pdf.exists():
            attachments.append(('CV.pdf', cv_pdf.read_bytes(), 'application/pdf'))
        
        # Отправляем письмо через SendGrid
        if EMAIL_SERVICE_AVAILABLE:
            subject = "💎 Twoje Premium CV + List motywacyjny"
            body = f"""
            Cześć {name}! 👋
            
            Dziękujemy za zakup Premium! 🎉
            
            W załączniku znajdziesz:
            ✅ Profesjonalne CV w formacie PDF
            ✅ List motywacyjny (jeśli dostępny)
            
            W razie pytań pisz na cvkonwerterpoland@gmail.com
            
            Pozdrawiamy,
            Zespół CV Konwerter
            """
            
            success = send_email_with_attachments(
                to_email=email,
                subject=subject,
                html_content=body,
                attachments=attachments
            )
            
            if success:
                # Удаляем временные файлы
                shutil.rmtree(temp_output, ignore_errors=True)
                return """
                <script>
                    alert('✅ Dziękujemy! Twoje Premium CV zostało wysłane na email. Sprawdź skrzynkę (również SPAM).');
                    window.location.href = '/';
                </script>
                """, 200
            else:
                return "Błąd: Nie udało się wysłać emaila", 500
        else:
            # Резервный вариант: скачивание файлов
            if cv_pdf.exists():
                response = send_file(
                    cv_pdf,
                    as_attachment=True,
                    download_name=f'CV_{name.replace(" ", "_")}.pdf',
                    mimetype='application/pdf'
                )
                shutil.rmtree(temp_output, ignore_errors=True)
                return response
            else:
                return "Błąd: Nie udało się wygenerować CV", 500
                
    except Exception as e:
        print(f"❌ Ошибка премиум-запроса: {type(e).__name__}: {e}")
        return f"Błąd serwera: {str(e)[:100]}", 500

# --- HEALTH CHECK ---
@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
