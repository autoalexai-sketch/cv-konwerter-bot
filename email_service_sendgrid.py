"""
Email service using SendGrid API (works on Render.com)
"""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from pathlib import Path
import os
import base64


def send_premium_cv_sendgrid(recipient_email, cv_path, letter_path, user_name):
    """
    Send CV and cover letter via SendGrid API
    
    Args:
        recipient_email: Recipient email
        cv_path: Path to CV file
        letter_path: Path to cover letter file  
        user_name: User name
    """
    try:
        # HTML content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .checkmark {{ color: #4CAF50; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💎 Twoje Premium CV jest gotowe!</h1>
                </div>
                <div class="content">
                    <p>Cześć <strong>{user_name}</strong>!</p>
                    
                    <p>Gratulacje! Twoje profesjonalne CV i list motywacyjny zostały wygenerowane.</p>
                    
                    <h3>📎 W załącznikach znajdziesz:</h3>
                    <ul>
                        <li><span class="checkmark">✅</span> CV w stylu Klasycznym (DOCX)</li>
                        <li><span class="checkmark">✅</span> List motywacyjny (DOCX)</li>
                    </ul>
                    
                    <p>Powodzenia w poszukiwaniu pracy! 🍀</p>
                    
                    <p>Pozdrawiamy,<br><strong>Zespół cv-konwerter.pl</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create message
        message = Mail(
            from_email=os.environ.get('SENDGRID_FROM_EMAIL', 'cvkonwerterpoland@gmail.com'),
            to_emails=recipient_email,
            subject='💎 Twoje Premium CV jest gotowe!',
            html_content=html_content
        )
        
        # Attach CV file
        if cv_path and Path(cv_path).exists():
            with open(cv_path, 'rb') as f:
                data = f.read()
                encoded_cv = base64.b64encode(data).decode()
                
            attachment_cv = Attachment(
                FileContent(encoded_cv),
                FileName(Path(cv_path).name),
                FileType('application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                Disposition('attachment')
            )
            message.add_attachment(attachment_cv)
        
        # Attach cover letter file
        if letter_path and Path(letter_path).exists():
            with open(letter_path, 'rb') as f:
                data = f.read()
                encoded_letter = base64.b64encode(data).decode()
                
            attachment_letter = Attachment(
                FileContent(encoded_letter),
                FileName(Path(letter_path).name),
                FileType('application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                Disposition('attachment')
            )
            message.add_attachment(attachment_letter)
        
        # Send email via SendGrid
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_api_key:
            print("❌ SENDGRID_API_KEY not set!")
            return False
            
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        print(f"✅ Email sent via SendGrid! Status: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ SendGrid email error: {e}")
        import traceback
        traceback.print_exc()
        return False
