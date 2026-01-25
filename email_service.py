"""
Email service for sending CV templates
"""

from flask_mail import Mail, Message
from pathlib import Path
import os

mail = Mail()


def init_mail(app):
    """Initialize mail configuration"""
    # Конфигурация для Gmail (можно изменить)
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@cv-konwerter.pl')
    
    mail.init_app(app)
    return mail


def send_premium_cv(recipient_email, cv_path, letter_path, user_name):
    """
    Отправить CV и сопроводительное письмо на email после покупки Premium
    
    Args:
        recipient_email: Email получателя
        cv_path: Путь к файлу CV
        letter_path: Путь к файлу сопроводительного письма
        user_name: Имя пользователя
    """
    try:
        msg = Message(
            subject='🎉 Twoje szablony CV - cv-konwerter.pl',
            recipients=[recipient_email]
        )
        
        # HTML содержимое письма
        msg.html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ background: #667eea; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #999; font-size: 12px; }}
                .checkmark {{ color: #4CAF50; font-size: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Dziękujemy za zakup Premium!</h1>
                </div>
                <div class="content">
                    <p>Cześć <strong>{user_name}</strong>!</p>
                    
                    <p>Gratulacje! Właśnie otrzymałeś dostęp do naszych profesjonalnych szablonów CV.</p>
                    
                    <h3>📎 W załącznikach znajdziesz:</h3>
                    <ul>
                        <li><span class="checkmark">✅</span> CV w stylu Klasycznym (DOCX)</li>
                        <li><span class="checkmark">✅</span> List motywacyjny (DOCX)</li>
                    </ul>
                    
                    <h3>💡 Jak edytować pliki:</h3>
                    <p>Pliki możesz edytować w:</p>
                    <ul>
                        <li>Microsoft Word</li>
                        <li>Google Docs (zalecane - darmowe)</li>
                        <li>LibreOffice Writer</li>
                    </ul>
                    
                    <h3>🚀 Następne kroki:</h3>
                    <ol>
                        <li>Otwórz plik CV w edytorze</li>
                        <li>Wypełnij swoje dane</li>
                        <li>Zapisz jako PDF</li>
                        <li>Wyślij do pracodawcy!</li>
                    </ol>
                    
                    <p style="margin-top: 30px;">
                        <a href="https://cv-konwerter-web-docker.onrender.com" class="button">
                            Wróć na stronę
                        </a>
                    </p>
                    
                    <p style="margin-top: 20px; padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 5px;">
                        <strong>💎 Wskazówka:</strong> Pamiętaj aby dostosować treść CV do oferty pracy, 
                        na którą aplikujesz. Personalizacja zwiększa Twoje szanse!
                    </p>
                    
                    <p style="margin-top: 30px;">Powodzenia w poszukiwaniu pracy! 🍀</p>
                    
                    <p>Pozdrawiamy,<br>
                    <strong>Zespół cv-konwerter.pl</strong></p>
                </div>
                <div class="footer">
                    <p>To wiadomość automatyczna. Nie odpowiadaj na ten email.</p>
                    <p>© 2026 cv-konwerter.pl | Warszawa, Polska</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Текстовая версия
        msg.body = f"""
        Cześć {user_name}!
        
        Dziękujemy za zakup Premium! 🎉
        
        W załącznikach znajdziesz:
        ✅ CV w stylu Klasycznym
        ✅ List motywacyjny
        
        Możesz edytować pliki w Microsoft Word lub Google Docs.
        
        Powodzenia w poszukiwaniu pracy!
        
        Zespół cv-konwerter.pl
        """
        
        # Прикрепление файлов
        if cv_path and Path(cv_path).exists():
            with open(cv_path, 'rb') as f:
                msg.attach(
                    filename=Path(cv_path).name,
                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    data=f.read()
                )
        
        if letter_path and Path(letter_path).exists():
            with open(letter_path, 'rb') as f:
                msg.attach(
                    filename=Path(letter_path).name,
                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    data=f.read()
                )
        
        # Отправка
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False


def send_test_email(recipient_email):
    """Тестовая отправка email"""
    try:
        msg = Message(
            subject='Test email from cv-konwerter.pl',
            recipients=[recipient_email],
            body='This is a test email. Email configuration works! ✅'
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"❌ Test email error: {e}")
        return False
