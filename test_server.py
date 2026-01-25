"""
Minimal test server for CV Konwerter
Use this to check if Flask works at all
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Server</title>
        <style>
            body {
                font-family: Arial;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            h1 { font-size: 48px; }
            .box {
                background: white;
                color: #333;
                padding: 30px;
                border-radius: 10px;
                margin: 20px auto;
                max-width: 600px;
            }
        </style>
    </head>
    <body>
        <h1>✅ Flask работает!</h1>
        <div class="box">
            <h2>🎉 Сервер запущен успешно!</h2>
            <p>Если вы видите эту страницу - значит Flask установлен правильно.</p>
            <p><strong>Следующий шаг:</strong> Запустите полное приложение командой <code>python start_web.py</code></p>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🧪 ТЕСТОВЫЙ СЕРВЕР CV KONWERTER")
    print("="*60)
    print("📍 URL: http://localhost:3000")
    print("📍 Альт: http://127.0.0.1:3000")
    print("⏹️  CTRL+C для остановки")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=3000, debug=True)
