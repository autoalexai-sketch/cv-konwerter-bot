from flask import Flask, render_template, request, send_file, jsonify, session, redirect, url_for
import os
import subprocess
from pathlib import Path
from werkzeug.utils import secure_filename
import tempfile
import shutil
from datetime import datetime
import sys
import json

# Import database models
from models import db, User, CV, Payment
from email_service import mail, init_mail  # Keep for Flask-Mail fallback
from email_service_sendgrid import send_premium_cv_sendgrid
from templates_cv.cv_generator import CVGenerator

app = Flask(__name__, 
            template_folder='web/templates',
            static_folder='web/static')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///cv_konwerter.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
init_mail(app)

# Create tables
with app.app_context():
    db.create_all()

# Initialize CV Generator
cv_generator = CVGenerator()

# Add translations folder to static files
@app.route('/static/translations/<filename>')
def serve_translation(filename):
    """Serve translation JSON files"""
    translations_path = Path('web/translations')
    return send_file(
        translations_path / filename,
        mimetype='application/json'
    )

# Configuration
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
ALLOWED_EXTENSIONS = {'doc', 'docx'}
UPLOAD_FOLDER = Path('web/static/uploads')
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_docx_to_pdf(input_path: Path, output_path: Path) -> bool:
    """
    Конвертирует DOCX в PDF используя LibreOffice
    """
    try:
        print(f"=== НАЧАЛО КОНВЕРТАЦИИ ===", flush=True)
        print(f"Input file: {input_path}", flush=True)
        print(f"Output file: {output_path}", flush=True)
        
        # Создаём временную директорию для вывода
        temp_dir = output_path.parent
        
        # LibreOffice команда
        cmd = [
            'soffice',
            '--headless',
            '--invisible',
            '--nodefault',
            '--nofirststartwizard',
            '--nolockcheck',
            '--nologo',
            '--norestore',
            '--convert-to', 'pdf',
            '--outdir', str(temp_dir),
            str(input_path)
        ]
        
        print(f"Команда: {' '.join(cmd)}", flush=True)
        
        # Запускаем конвертацию с таймаутом 30 секунд
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, 'HOME': '/tmp'}
        )
        
        print(f"Return code: {result.returncode}", flush=True)
        print(f"STDOUT: {result.stdout}", flush=True)
        print(f"STDERR: {result.stderr}", flush=True)
        
        if result.returncode != 0:
            print(f"❌ LibreOffice error: {result.stderr}", flush=True)
            return False
        
        # LibreOffice создаёт файл с тем же именем, но расширением .pdf
        expected_pdf = temp_dir / f"{input_path.stem}.pdf"
        
        print(f"Ожидаемый PDF: {expected_pdf}", flush=True)
        print(f"Файл существует: {expected_pdf.exists()}", flush=True)
        
        if expected_pdf.exists():
            print(f"✅ PDF создан успешно!", flush=True)
            if expected_pdf != output_path:
                shutil.move(str(expected_pdf), str(output_path))
            return True
        
        print(f"❌ PDF файл не создан", flush=True)
        return False
        
    except subprocess.TimeoutExpired:
        print("❌ LibreOffice conversion timeout (30 секунд)", flush=True)
        return False
    except FileNotFoundError as e:
        print(f"❌ soffice не найден: {e}", flush=True)
        return False
    except Exception as e:
        print(f"❌ Conversion error: {e}", flush=True)
        return False

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    """Конвертация DOCX в PDF"""
    
    print("=" * 50, flush=True)
    print("🔄 НОВЫЙ ЗАПРОС НА КОНВЕРТАЦИЮ", flush=True)
    print("=" * 50, flush=True)
    
    # Проверяем наличие файла
    if 'file' not in request.files:
        print("❌ Файл не найден в запросе", flush=True)
        return jsonify({'error': 'Brak pliku'}), 400
    
    file = request.files['file']
    
    # Проверяем имя файла
    if file.filename == '':
        print("❌ Имя файла пустое", flush=True)
        return jsonify({'error': 'Nie wybrano pliku'}), 400
    
    print(f"📄 Загружен файл: {file.filename}", flush=True)
    
    # Проверяем расширение
    if not allowed_file(file.filename):
        print(f"❌ Неправильное расширение файла: {file.filename}", flush=True)
        return jsonify({'error': 'Dozwolone tylko pliki .doc i .docx'}), 400
    
    try:
        # Создаём временную директорию
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Сохраняем загруженный файл
            filename = secure_filename(file.filename)
            input_path = temp_path / filename
            file.save(str(input_path))
            
            # Проверяем размер файла
            file_size = input_path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                return jsonify({'error': 'Plik jest za duży (max 15 MB)'}), 400
            
            # Создаём путь для PDF
            output_filename = input_path.stem + '.pdf'
            output_path = temp_path / output_filename
            
            # Конвертируем
            print(f"Converting {input_path} to {output_path}")
            success = convert_docx_to_pdf(input_path, output_path)
            
            if not success or not output_path.exists():
                return jsonify({'error': 'Nie udało się skonwertować pliku'}), 500
            
            # Отправляем PDF
            return send_file(
                str(output_path),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=output_filename
            )
    
    except Exception as e:
        print(f"Error during conversion: {e}")
        return jsonify({'error': 'Wystąpił błąd serwera'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return 'OK', 200

@app.route('/check-libreoffice')
def check_libreoffice():
    """Проверка наличия LibreOffice"""
    try:
        result = subprocess.run(
            ['soffice', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return jsonify({
                'status': 'OK',
                'version': result.stdout.strip(),
                'message': 'LibreOffice установлен и работает'
            })
        else:
            return jsonify({
                'status': 'ERROR',
                'message': 'LibreOffice найден, но не отвечает',
                'stderr': result.stderr
            }), 500
    except FileNotFoundError:
        return jsonify({
            'status': 'ERROR',
            'message': 'LibreOffice НЕ УСТАНОВЛЕН (soffice not found)'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'message': f'Ошибка проверки: {str(e)}'
        }), 500

@app.route('/premium')
def premium():
    """Premium page (placeholder for now)"""
    return jsonify({
        'message': 'Premium feature coming soon!',
        'price': '39 PLN'
    })

@app.route('/premium/form')
def premium_form():
    """Форма для ввода данных CV (после оплаты)"""
    # TODO: проверка оплаты
    email = request.args.get('email', '')
    return render_template('premium_form.html', email=email)

@app.route('/premium/generate', methods=['POST'])
def premium_generate():
    """Генерация CV и отправка на email"""
    try:
        data = request.json
        
        # Валидация
        required_fields = ['email', 'imie', 'nazwisko', 'telefon', 'miasto']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Pole {field} jest wymagane'}), 400
        
        # Получение или создание пользователя
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            user = User(email=data['email'], is_premium=True)
            db.session.add(user)
            db.session.commit()
        
        # Сохранение CV в базу
        template = data.get('template', 'nowoczesny')  # По умолчанию nowoczesny
        cv = CV(
            user_id=user.id,
            imie=data['imie'],
            nazwisko=data['nazwisko'],
            telefon=data['telefon'],
            adres=data.get('adres', ''),
            kod_pocztowy=data.get('kod_pocztowy', ''),
            miasto=data['miasto'],
            stanowisko=data.get('stanowisko', ''),
            o_sobie=data.get('o_sobie', ''),
            doswiadczenie=json.dumps(data.get('doswiadczenie', [])),
            wyksztalcenie=json.dumps(data.get('wyksztalcenie', [])),
            umiejetnosci=json.dumps(data.get('umiejetnosci', [])),
            jezyki=json.dumps(data.get('jezyki', [])),
            zainteresowania=json.dumps(data.get('zainteresowania', [])),
            template=template
        )
        db.session.add(cv)
        db.session.commit()
        
        # Генерация файлов
        cv_data = cv.to_dict()
        
        print(f"🔄 Генерация CV для {cv_data['imie']} {cv_data['nazwisko']} (szablon: {template})...", flush=True)
        
        # Выбор метода генерации в зависимости от шаблона
        if template == 'nowoczesny':
            cv_path = cv_generator.generate_nowoczesny(cv_data)
        else:
            cv_path = cv_generator.generate_klasyczny(cv_data)
        
        print(f"✅ CV сгенерировано: {cv_path}", flush=True)
        
        print(f"🔄 Генерация List motywacyjny...", flush=True)
        letter_path = cv_generator.generate_list_motywacyjny({}, cv_data)
        print(f"✅ List motywacyjny сгенерован: {letter_path}", flush=True)
        
        # Отправка на email
        user_name = f"{cv_data['imie']} {cv_data['nazwisko']}"
        print(f"📧 Отправка email на {cv_data['email']}...", flush=True)
        
        email_sent = send_premium_cv_sendgrid(
            recipient_email=cv_data['email'],
            cv_path=str(cv_path),
            letter_path=str(letter_path),
            user_name=user_name
        )
        
        if email_sent:
            print(f"✅ Email отправлен успешно!", flush=True)
            return jsonify({
                'success': True,
                'message': 'CV wygenerowane i wysłane na email!',
                'email': cv_data['email']
            })
        else:
            print(f"⚠️ Email не отправлен, но файлы готовы", flush=True)
            # Даже если email не отправился, даём ссылки на скачивание
            return jsonify({
                'success': True,
                'message': 'CV wygenerowane! (Email może dotrzeć później)',
                'cv_path': cv_path.name,
                'letter_path': letter_path.name
            })
    
    except Exception as e:
        print(f"❌ Error generating CV: {e}", flush=True)
        return jsonify({'error': 'Wystąpił błąd podczas generowania CV'}), 500

@app.route('/premium/mock-payment', methods=['POST'])
def mock_payment():
    """Mock оплаты для тестирования (УБРАТЬ В ПРОДАКШЕНЕ!)"""
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email jest wymagany'}), 400
        
        # Создание пользователя
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, is_premium=True)
            db.session.add(user)
            db.session.flush()  # Получаем user.id до commit
        else:
            user.is_premium = True
        
        # Создание mock платежа
        payment = Payment(
            user_id=user.id,  # Теперь user.id существует
            session_id=f"mock_{datetime.utcnow().timestamp()}",
            order_id=f"ORDER_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            amount=3900,
            status='completed',
            completed_at=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()  # Сохраняем всё вместе
        
        print(f"✅ Mock payment created for {email}", flush=True)
        
        return jsonify({
            'success': True,
            'message': 'Płatność zakończona sukcesem (TEST)',
            'redirect_url': f'/premium/form?email={email}'
        })
    
    except Exception as e:
        print(f"❌ Mock payment error: {e}", flush=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
