import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

async def send_email(subject, to_email, template, smtp_server, smtp_port, smtp_user, smtp_password):
    # Create the email content from the template
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject

    with open(template, 'r') as file:
        template_content = file.read()
    
    msg.attach(MIMEText(template_content, 'html'))

    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

# Example usage
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_email(
        subject="Subject Here",
        to_email="recipient@example.com",
        template="template.html",
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        smtp_user="your_email@gmail.com",
        smtp_password="your_password"
    ))
