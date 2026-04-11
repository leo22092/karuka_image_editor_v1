# 🖼️ Image Editor (v1)

A simple desktop image editor built with Python and Tkinter.

---

## 🚀 Features

- 📏 Resize images (with size + dimension control)
- ✂️ Crop using interactive selection
- 🔄 Rotate (left / right)
- 🖼️ Format conversion (JPG, PNG, etc.)
- 🎯 Smart compression (target file size)
- 🎨 Basic background removal (white → transparent)
- 🤖 AI background removal (optional via rembg)

---

## 🧱 Project Structure
image_editor/
├── core/ # Image processing logic
├── ui/ # Tkinter UI
├── utils/ # Helper functions
├── main.py # Entry point
---

## ⚙️ Installation

### 1. Clone project

```bash
git clone <your-repo-url>
cd image_editor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
⚠️ Notes
First run of AI background removal downloads a model (~100MB)
Output images are saved in project directory
Works best on Linux
⚠️ Notes
First run of AI background removal downloads a model (~100MB)
Output images are saved in project directory
Works best on Linux
