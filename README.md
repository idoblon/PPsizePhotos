# 📸 Passport Photo Pro

> **Generate professional, print-ready passport photo sheets in seconds.**  
> A high-performance, modular Flask application that automates the tedious process of preparing passport photos for A4 printing.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web-lightgrey.svg)](https://flask.palletsprojects.com/)
[![A4 Ready](https://img.shields.io/badge/Layout-A4--300DPI-green.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Features

- 🖼️ **Bulk Processing** — Upload and manage multiple photos at once.
- ✂️ **Precision Cropping** — Integrated Cropper.js for perfect passport aspect ratios.
- 🪄 **AI background Removal** — Isolated subjects via [Remove.bg](https://www.remove.bg/).
- ⚡ **AI Enhancement** — Image restoration and sharpening via [Cloudinary AI](https://cloudinary.com/).
- 📐 **Smart Layout Engine** — Automated A4 grid calculation at **300 DPI**.
- 📄 **Multi-page Support** — Seamless overflow handling for large photo sets.
- 🎨 **Premium UI** — Modern glassmorphism design with real-time PDF previews.

---

## 🛡️ "Safe-to-Deploy" Architecture

This project is built with **Resilient Deployment** in mind. The backend automatically detects your configuration and adapts its feature set on the fly.

> [!TIP]
> **No API Keys? No Problem.**  
> If external AI keys (Remove.bg or Cloudinary) are missing, the app will gracefully skip those specific steps and generate your PDF using the original images. It **never crashes** due to missing optional keys.

---

## 🏗️ Project Structure

The codebase follows a professional **Service-Oriented Architecture** (SOA):

```bash
PPsizePhotos/
├── 📂 app/
│   ├── 📁 services/       # Core Engines (AI Pipeline & PDF Engine)
│   ├── 📁 utils/          # Request & Parameter Validation
│   ├── 📄 config.py       # Feature Flags & Environment Logic
│   └── 📄 routes.py       # Blueprint-based Routing
├── 📁 static/             # Frontend Assets (Cropper.js, Tailwind)
├── 📁 templates/          # Responsive Jinja2 Templates
└── 📄 run.py              # Application Entry Point
```

---

## 🚀 Quick Start

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/idoblon/PPsizePhotos.git
cd PPsizePhotos
```

### 2️⃣ Install Dependencies
```bash
python -m venv venv
# Windows: venv\Scripts\activate | Unix: source venv/bin/activate
pip install -r requirements.txt
```

### 3️⃣ Configuration (Optional)
Create a `.env` file to unlock AI enhancements:
```env
REMOVE_BG_API_KEY=your_removebg_key
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### 4️⃣ Fire It Up!
```bash
python run.py
```
Open `http://localhost:5000` in your browser.

---

## ⚙️ How it Works

> [!IMPORTANT]
> **Standardized Grid Specs**  
> We use a professional A4 canvas (2480x3508 pixels) at 300 DPI.

1. **Client Uplink**: Photos are uploaded and cropped in-browser.
2. **Validation Layer**: The backend sanitizes all parameters (Dimensions: 100-2000px, Copies: 1-54).
3. **AI Pipeline**:
   - Subjects are isolated using **Remove.bg**.
   - Quality is restored using Cloudinary **Gen Restore**.
4. **Layout Compilation**: The PDF engine calculates grid positions, handles page breaks, and renders the final high-res document.

---

## 📄 License
Distributed under the MIT License. Created with ❤️ by [idoblon](https://github.com/idoblon).
