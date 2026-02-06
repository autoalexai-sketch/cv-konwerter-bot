from flask import Flask, render_template, request, send_file
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Импорты для отправки писем
try:
    from email_service_sendgrid import send_premium_cv_sendgrid
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    EMAIL_SERVICE_AVAILABLE = False
    print("⚠️ Email service not available")

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

# --- ПРЕМИУМ: ОТПРАВКА ГОТОВЫХ ШАБЛОНОВ НА EMAIL ---
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
        
        # Пути к готовым шаблонам
        cv_path = Path(app.config['TEMPLATES_FOLDER']) / 'CV_Kowalski_Jan_Klasyczny.docx'
        letter_path = Path(app.config['TEMPLATES_FOLDER']) / 'List_Motywacyjny_Kowalski_Jan.docx'
        
        # Проверяем существование файлов
        if not cv_path.exists():
            return "Błąd: Szablon CV nie istnieje", 500
        
        # Отправляем письмо через существующую функцию
        if EMAIL_SERVICE_AVAILABLE:
            success = send_premium_cv_sendgrid(
                recipient_email=email,
                cv_path=str(cv_path),
                letter_path=str(letter_path) if letter_path.exists() else None,
                user_name=name
            )
            
            if success:
                return """
                <script>
                    alert('✅ Dziękujemy! Twoje Premium CV zostało wysłane na email. Sprawdź skrzynkę (również SPAM).');
                    window.location.href = '/';
                </script>
                """, 200
            else:
                return "Błąd: Nie udało się wysłać emaila", 500
        else:
            # Резервный вариант: скачивание файла
            if cv_path.exists():
                return send_file(
                    cv_path,
                    as_attachment=True,
                    download_name=f'CV_{name.replace(" ", "_")}.docx',
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
            else:
                return "Błąd: Nie udało się znaleźć CV", 500
                
    except Exception as e:
        print(f"❌ Ошибка премиум-запроса: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return f"Błąd serwera: {str(e)[:100]}", 500

# --- HEALTH CHECK ---
@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
