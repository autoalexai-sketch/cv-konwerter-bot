from flask import Flask, render_template, request, send_file, jsonify
import os
import subprocess
from datetime import datetime
from pathlib import Path

try:
    from email_service_sendgrid import send_premium_cv_sendgrid
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    EMAIL_SERVICE_AVAILABLE = False
    print("⚠️ Email service not available")

app = Flask(__name__, template_folder='web/templates')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['OUTPUT_FOLDER'] = '/tmp/outputs'
app.config['TEMPLATES_FOLDER'] = 'templates_cv'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


# ============ ЮРИДИЧЕСКИЕ ДОКУМЕНТЫ ============

@app.route('/polityka-prywatnosci')
def privacy_policy():
    """Политика конфиденциальности (RODO/GDPR)"""
    return render_template('polityka-prywatnosci.html')


@app.route('/regulamin')
def terms_of_service():
    """Условия использования / Регламент"""
    return render_template('regulamin.html')


@app.route('/polityka-cookies')
def cookies_policy():
    """Политика использования cookies"""
    return render_template('polityka-cookies.html')


@app.route('/zasady-subskrypcji')
def subscription_terms():
    """Правила подписки Premium"""
    return render_template('zasady-subskrypcji.html')

# ============ КОНЕЦ ЮРИДИЧЕСКИХ ДОКУМЕНТОВ ============


@app.route('/convert', methods=['POST'])
def convert():
    """Конвертация DOCX в PDF"""
    file = request.files.get('file')
    if file and file.filename.lower().endswith(('.docx', '.doc')):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Очищаем имя файла от спецсимволов
        safe_filename = file.filename.replace(' ', '_').replace('(', '').replace(')', '')
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{timestamp}_{safe_filename}')
        
        file.save(input_path)
        try:
            # Конвертация
            subprocess.run([
                'soffice', '--headless', 
                '-env:UserInstallation=file:///tmp/.libreoffice', 
                '--convert-to', 'pdf', 
                '--outdir', app.config['OUTPUT_FOLDER'], 
                input_path
            ], check=True, timeout=30)
            
            # LibreOffice создаёт файл с именем без расширения + .pdf
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            expected_pdf = os.path.join(app.config['OUTPUT_FOLDER'], f'{base_name}.pdf')
            
            # Проверяем что файл создан
            if not os.path.exists(expected_pdf):
                # Ищем любой PDF в папке с таким timestamp
                pdf_files = [f for f in os.listdir(app.config['OUTPUT_FOLDER']) 
                            if f.startswith(timestamp) and f.endswith('.pdf')]
                if pdf_files:
                    expected_pdf = os.path.join(app.config['OUTPUT_FOLDER'], pdf_files[0])
                    base_name = os.path.splitext(pdf_files[0])[0]
                else:
                    return jsonify({'success': False, 'error': 'Nie znaleziono pliku PDF'}), 500
            
            return jsonify({
                'success': True,
                'filename': f"cv_{timestamp}.pdf",
                'download_url': f'/download/{base_name}.pdf'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': f"Błąd konwersji: {str(e)[:100]}"}), 500
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
    return jsonify({'success': False, 'error': 'Nieprawidłowy plik'}), 400

@app.route('/premium', methods=['POST'])
def premium():
    """Обработка заказа Premium шаблонов CV"""
    try:
        name = request.form.get('name', 'Anonim')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        city = request.form.get('city', 'Kraków')
        
        print(f"📧 Premium request: {name}, {email}, {city}")
        
        if not email or '@' not in email:
            return jsonify({'success': False, 'error': 'Nieprawidłowy email'}), 400
        
        cv_path = Path(app.config['TEMPLATES_FOLDER']) / 'CV_Kowalski_Jan_Klasyczny.docx'
        letter_path = Path(app.config['TEMPLATES_FOLDER']) / 'List_Motywacyjny_Kowalski_Jan.docx'
        
        if not cv_path.exists():
            return jsonify({'success': False, 'error': 'Szablon CV nie istnieje'}), 500
        
        if EMAIL_SERVICE_AVAILABLE:
            success = send_premium_cv_sendgrid(
                recipient_email=email,
                cv_path=str(cv_path),
                letter_path=str(letter_path) if letter_path.exists() else None,
                user_name=name
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '✅ Dziękujemy! Twoje Premium CV zostało wysłane na email. Sprawdź skrzynkę (również SPAM).'
                })
            else:
                return jsonify({'success': False, 'error': 'Nie udało się wysłać emaila'}), 500
        else:
            if cv_path.exists():
                return send_file(
                    cv_path,
                    as_attachment=True,
                    download_name=f'CV_{name.replace(" ", "_")}.docx',
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
            else:
                return jsonify({'success': False, 'error': 'Nie udało się znaleźć CV'}), 500
                
    except Exception as e:
        print(f"❌ Premium error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f"Błąd serwera: {str(e)[:100]}"}), 500


@app.route('/health')
def health():
    """Health check для мониторинга"""
    return "OK", 200


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
