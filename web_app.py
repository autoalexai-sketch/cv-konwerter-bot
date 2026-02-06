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

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['OUTPUT_FOLDER'] = '/tmp/outputs'
app.config['TEMPLATES_FOLDER'] = 'templates_cv'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

# --- КОНВЕРТАЦИЯ ФАЙЛОВ (ВОЗВРАЩАЕМ ИМЯ ФАЙЛА) ---
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
            output_filename = f"cv_{timestamp}.pdf"
            
            # ✅ Возвращаем информацию о файле (не сам файл!)
            return jsonify({
                'success': True,
                'filename': output_filename,
                'download_url': f'/download/{timestamp}_{os.path.splitext(file.filename)[0]}.pdf'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': f"Błąd konwersji: {str(e)[:100]}"}), 500
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
    return jsonify({'success': False, 'error': 'Nieprawidłowy plik'}), 400

# --- ЭНДПОИНТ ДЛЯ СКАЧИВАНИЯ ФАЙЛА ---
@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"cv_{filename}",
            mimetype="application/pdf"
        )
    return "Plik nie istnieje", 404

# --- ПРЕМИУМ: ОТПРАВКА ШАБЛОНОВ НА EMAIL (С ОТЛАДКОЙ) ---
@app.route('/premium', methods=['POST'])
def premium():
    try:
        name = request.form.get('name', 'Anonim')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        city = request.form.get('city', 'Kraków')
        
        print(f"📧 Получен премиум-запрос: {name}, {email}, {city}")
        
        if not email or '@' not in email:
            print("❌ Ошибка: Неправильный email")
            return jsonify({'success': False, 'error': 'Nieprawidłowy email'}), 400
        
        cv_path = Path(app.config['TEMPLATES_FOLDER']) / 'CV_Kowalski_Jan_Klasyczny.docx'
        letter_path = Path(app.config['TEMPLATES_FOLDER']) / 'List_Motywacyjny_Kowalski_Jan.docx'
        
        print(f"📄 Путь к шаблону резюме: {cv_path}")
        print(f"📄 Путь к шаблону письма: {letter_path}")
        
        if not cv_path.exists():
            print("❌ Ошибка: Шаблон резюме не найден")
            return jsonify({'success': False, 'error': 'Szablon CV nie istnieje'}), 500
        
        if EMAIL_SERVICE_AVAILABLE:
            print(f"📤 Отправка письма через SendGrid на {email}")
            success = send_premium_cv_sendgrid(
                recipient_email=email,
                cv_path=str(cv_path),
                letter_path=str(letter_path) if letter_path.exists() else None,
                user_name=name
            )
            
            if success:
                print("✅ Письмо успешно отправлено!")
                return jsonify({
                    'success': True,
                    'message': '✅ Dziękujemy! Twoje Premium CV zostało wysłane na email. Sprawdź skrzynkę (również SPAM).'
                })
            else:
                print("❌ Ошибка: Не удалось отправить письмо")
                return jsonify({'success': False, 'error': 'Nie udało się wysłać emaila'}), 500
        else:
            print("⚠️ Email service недоступен, скачивание файла")
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
        print(f"❌ Ошибка премиум-запроса: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f"Błąd serwera: {str(e)[:100]}"}), 500

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
