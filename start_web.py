# Windows Start Script for Web App
# This script sets up the environment and starts the Flask web application

import os
import sys
import platform

# Detect Windows and add LibreOffice to PATH
if platform.system() == 'Windows':
    libreoffice_paths = [
        r"C:\Program Files\LibreOffice\program",
        r"C:\Program Files (x86)\LibreOffice\program",
    ]
    
    for path in libreoffice_paths:
        if os.path.exists(path):
            os.environ['PATH'] = f"{path};{os.environ['PATH']}"
            print(f"✅ Added LibreOffice to PATH: {path}")
            break
    else:
        print("⚠️  LibreOffice not found! Conversion will not work.")
        print("📥 Download LibreOffice: https://www.libreoffice.org/download/")

# Import and run the Flask app
from web_app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🚀 Starting CV Konwerter Web App...")
    print(f"📍 Open in browser: http://localhost:{port}")
    print(f"🌍 Supported languages: 🇵🇱 Polish, 🇬🇧 English, 🇺🇦 Ukrainian")
    print(f"\n⏹️  Press CTRL+C to stop\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)
