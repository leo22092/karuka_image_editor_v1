
#!/bin/bash

set -e  # stop on error
set -o pipefail

if [ "$1" == "--fresh" ]; then
    echo "🆕 Creating fresh environment..."

    rm -rf venv
    python3 -m venv venv
    source venv/bin/activate

    pip install --upgrade pip
    pip install -r requirements.txt
fi

echo "🚀 Building Karuka AppImage..."

# -------------------------------
# SAFETY CHECKS
# -------------------------------

if [ ! -f "main.py" ]; then
    echo "❌ Run this from project root (main.py not found)"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "❌ venv not found. Create it first."
    exit 1
fi

# -------------------------------
# CLEAN OLD BUILDS
# -------------------------------

echo "🧹 Cleaning old builds..."
rm -rf AppDir
rm -f *.AppImage

# -------------------------------
# CREATE AppDir STRUCTURE
# -------------------------------

echo "📁 Creating AppDir..."

mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/lib
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

# -------------------------------
# COPY APPLICATION FILES
# -------------------------------

echo "📦 Copying app files..."

cp -r core ui utils main.py AppDir/usr/bin/

# -------------------------------
# COPY PYTHON ENV (SAFE)
# -------------------------------

echo "🐍 Copying Python environment..."

cp -r venv/lib AppDir/usr/
cp venv/bin/python AppDir/usr/bin/

# -------------------------------
# COPY ICON
# -------------------------------

echo "🎨 Setting icon..."

cp icon.png AppDir/karuka.png
cp icon.png AppDir/.DirIcon

# -------------------------------
# CREATE AppRun
# -------------------------------

echo "⚙️ Creating AppRun..."

cat > AppDir/AppRun << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export PYTHONPATH="$HERE/usr/bin:$HERE/usr/lib"
exec "$HERE/usr/bin/python" "$HERE/usr/bin/main.py"
EOF

chmod +x AppDir/AppRun

# -------------------------------
# CREATE DESKTOP FILE
# -------------------------------

echo "🖥️ Creating desktop entry..."

cat > AppDir/karuka.desktop << 'EOF'
[Desktop Entry]
Name=Karuka Image Editor
Exec=AppRun
Icon=karuka
Type=Application
Categories=Graphics;
EOF

# -------------------------------
# CLEANUP (SAFE - ONLY AppDir)
# -------------------------------

echo "🧹 Reducing size..."

rm -rf AppDir/usr/lib/python*/site-packages/pip*
rm -rf AppDir/usr/lib/python*/site-packages/setuptools*
rm -rf AppDir/usr/lib/python*/site-packages/wheel*

find AppDir/usr/lib -type d -name "test" -exec rm -r {} + 2>/dev/null || true
find AppDir/usr/lib -type d -name "tests" -exec rm -r {} + 2>/dev/null || true

find AppDir -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find AppDir -name "*.pyc" -delete

# -------------------------------
# DOWNLOAD APPIMAGETOOL (IF NEEDED)
# -------------------------------

if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "⬇️ Downloading appimagetool..."
    wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool-x86_64.AppImage
fi

# -------------------------------
# BUILD APPIMAGE
# -------------------------------

echo "📦 Building AppImage..."

./appimagetool-x86_64.AppImage AppDir Karuka.AppImage

echo "✅ Done! AppImage created: Karuka.AppImage"

