<div align="center">

# 📷 Passport Photo Pro

**A smart, AI-powered web application that transforms any portrait into a professional passport photo sheet — ready to print.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.1-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Pillow](https://img.shields.io/badge/Pillow-11.1.0-3C7ABF?style=flat-square&logo=python&logoColor=white)](https://python-pillow.org/)
[![Vercel](https://img.shields.io/badge/Deployed_on-Vercel-000000?style=flat-square&logo=vercel&logoColor=white)](https://vercel.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## ✨ What It Does

Passport Photo Pro takes one or more portrait photos, runs them through an **AI-powered processing pipeline**, and outputs a **print-ready A4 PDF sheet** — all in your browser without any photo-editing software.

### 🔄 Processing Pipeline

```
Upload Photo → Background Removal → AI Enhancement → Grid Layout → A4 PDF
```

1. **Background Removal** — Uses the [Remove.bg](https://www.remove.bg/) API for professional-grade cutouts. Automatically falls back to **local AI** (via `rembg` + ONNX Runtime) if the API is unavailable or quota is exceeded.
2. **AI Enhancement** — Uses [Cloudinary's](https://cloudinary.com/) `gen_restore` transformation to automatically improve photo clarity and quality.
3. **PDF Sheet Generation** — Arranges photos in an optimized grid on a high-resolution A4 canvas (2480 × 3508 px @ 300 DPI), with support for multiple pages and custom copy counts.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🖼️ **Multi-Photo Upload** | Upload and process multiple passport photos in a single session |
| ✂️ **In-Browser Cropping** | Crop and adjust each photo before processing using [Cropper.js](https://fengyuanchen.github.io/cropperjs/) |
| 🤖 **Dual AI Background Removal** | Remove.bg API (primary) with automatic local AI fallback |
| ✨ **AI Enhancement** | Cloudinary-powered quality restoration and upscaling |
| 📄 **Print-Ready PDF** | 300 DPI A4 sheets, multi-page support, custom copies per photo |
| ⚙️ **Advanced Layout Controls** | Customize photo width, height, spacing, and border thickness |
| 📱 **Responsive UI** | Clean dark-mode interface that works on mobile and desktop |
| 🔌 **Graceful Degradation** | Runs fully offline without any API keys (local AI fallback) |
| ☁️ **Serverless Ready** | Deployed and configured for Vercel with Python 3.12 runtime |

---

## 🏗️ Project Structure

```
PPsizePhotos/
│
├── index.py                  # Application entry point (Vercel handler)
├── vercel.json               # Vercel deployment configuration
├── requirements.txt          # Python dependencies
├── .env                      # Local environment variables (not committed)
│
├── app/
│   ├── __init__.py           # Flask app factory (create_app)
│   ├── config.py             # Configuration classes (Dev/Prod)
│   ├── routes.py             # URL routing and request handling
│   ├── exceptions.py         # Custom exception hierarchy
│   │
│   ├── services/
│   │   ├── image_service.py  # AI processing pipeline (removal + enhancement)
│   │   └── pdf_generator.py  # A4 PDF sheet generation logic
│   │
│   └── utils/
│       └── validators.py     # Request validation and sanitization
│
├── templates/
│   └── index.html            # Single-page frontend (Tailwind CSS + Cropper.js)
│
└── static/
    ├── css/main.css          # Custom styles and overrides
    └── js/app.js             # Frontend logic (upload, crop, submit, preview)
```

---

## ⚡ Getting Started

### Prerequisites

- **Python 3.10+**
- `pip` for package management
- *(Optional)* [Remove.bg API key](https://www.remove.bg/api) for professional background removal
- *(Optional)* [Cloudinary account](https://cloudinary.com/) for AI enhancement

### 1. Clone & Set Up

```bash
git clone https://github.com/your-username/PPsizePhotos.git
cd PPsizePhotos

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Optional — enables professional background removal
REMOVE_BG_API_KEY=your_remove_bg_key_here

# Optional — enables AI photo enhancement
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_SECRET_KEY=your_api_secret

# Set to 'development' for debug mode
FLASK_ENV=development
```

> **Note:** The app works without any API keys. Background removal will fall back to the local `rembg` model automatically.

### 3. Run Locally

```bash
python index.py
```

Open your browser and navigate to **[http://localhost:5000](http://localhost:5000)**.

---

## 🌐 Deployment (Vercel)

This project is configured for one-command deployment on Vercel.

```bash
npm install -g vercel   # Install Vercel CLI (one-time)
vercel                  # Deploy
```

Set your environment variables in the Vercel project dashboard under **Settings → Environment Variables**.

The `vercel.json` routes all traffic through `index.py` using the `@vercel/python` runtime with a 60-second function timeout.

---

## 🔧 API Reference

### `GET /`
Renders the main application UI.

### `GET /status`
Diagnostic endpoint. Returns the current state of all configured services.

```json
{
  "services": {
    "remove_bg_api": { "enabled": true, "key_present": true },
    "local_ai": { "rembg_installed": true, "onnx_installed": true },
    "cloudinary": { "enabled": true, ... }
  },
  "environment": "production"
}
```

### `POST /process`
Main processing endpoint. Accepts `multipart/form-data`.

| Field | Type | Default | Description |
|---|---|---|---|
| `image_0` | File | — | First image file (JPG, PNG, WEBP) |
| `image_N` | File | — | Additional images (indexed from 0) |
| `copies_N` | int | `6` | Number of copies for image N (1–54) |
| `width` | int | `390` | Photo width in pixels (100–2000) |
| `height` | int | `480` | Photo height in pixels (100–2000) |
| `spacing` | int | `10` | Vertical spacing between rows (0–100) |
| `border` | int | `2` | Border thickness in pixels (0–20) |

**Returns:** A downloadable `passport-sheet.pdf` binary, or a JSON error object.

---

## 🧩 Architecture

The application uses a **pipeline pattern** for extensible image processing:

```python
# Each step implements the ProcessStep ABC
class ImageService:
    steps = [BackgroundRemovalStep(), EnhancementStep()]

    def process_single_image(img_bytes):
        for step in self.steps:
            img = step.process(img)
        return img
```

New processing steps can be added by implementing the `ProcessStep` abstract class and appending to the pipeline — no other code changes needed.

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `Flask 3.1` | Web framework and routing |
| `Pillow 11` | Image resizing, compositing, PDF export |
| `rembg 2.0` | Local AI background removal (u2netp model) |
| `onnxruntime` | ML inference engine for rembg |
| `cloudinary` | AI image enhancement via cloud API |
| `python-dotenv` | Environment variable loading |
| `requests` | HTTP calls to Remove.bg and Cloudinary |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
  <sub>Built with ❤️ using Flask, Pillow, and a sprinkle of AI.</sub>
</div>
