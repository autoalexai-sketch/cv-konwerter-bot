#!/bin/bash
# Build script for Render.com

echo "🔧 Installing system dependencies..."
apt-get update
apt-get install -y libreoffice-writer libreoffice-core fonts-liberation fonts-dejavu

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build completed!"
