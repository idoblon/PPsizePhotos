# 📸 Passport Photo Pro

A modular, web-based tool to generate print-ready passport photo sheets from uploaded images. Supports multiple photos, per-photo copy counts, AI background removal, image enhancement, and multi-page PDF export — all on an A4 layout at 300 DPI.

---

## 🚀 Features

- **Multi-photo upload** — drag & drop or click to upload one or more photos at once
- **Per-photo copy count** — set how many copies of each photo you need (1–54)
- **In-browser cropper** — crop each photo to the correct passport aspect ratio before processing
- **AI background removal** — powered by [remove.bg](https://www.remove.bg/)
- **AI image enhancement** — restored and sharpened via [Cloudinary's gen_restore](https://cloudinary.com/documentation/image_transformations)
- **A4 print layout** — photos are automatically arranged in a grid at 300 DPI
- **Multi-page PDF** — if photos exceed one A4 page, additional pages are created automatically
- **Advanced options** — customize photo width, height, spacing, and border size
- **Modular Architecture** — clean separation of concerns with a dedicated service layer

---

## 🧰 Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Frontend  | HTML, Tailwind CSS, Vanilla JS    |
| Cropping  | Cropper.js                        |
| Backend   | Python 3.8+, Flask (Factory Pattern) |
| Layout    | Pillow (PIL)                      |
| Image AI  | remove.bg API, Cloudinary AI      |
| Email     | EmailJS                           |

---

## 🏗️ Project Structure

The project follows a modular Flask architecture:

```text
backgroundremover/
├── app/
│   ├── __init__.py         # App Factory & initialization
│   ├── config.py           # Centralized configuration
│   ├── exceptions.py       # Custom exception classes
│   ├── routes.py           # Blueprint-based routing
│   └── services/
│       └── image_service.py # Core image processing & layout logic
├── static/
│   ├── css/                # Externalized Styles
│   └── js/                 # Externalized Scripts
├── templates/              # Cleaned HTML templates
├── run.py                  # Direct entry point
├── requirements.txt
└── .env                    # Environment variables
```

---

## 🛠️ Installation

### 1. Clone & Navigate
```bash
git clone https://github.com/your-username/passport-photo-pro.git
cd passport-photo-pro
```

### 2. Environment Setup
```bash
python -m venv venv
# Windows: venv\Scripts\activate | Unix: source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the project root:
```env
REMOVE_BG_API_KEY=your_key
CLOUDINARY_CLOUD_NAME=your_name
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret
```

### 4. Run
```bash
python run.py
```
Visit `http://localhost:5000`

---

## 🖼️ How It Works

1. **Upload**: Drag & drop images. They appear as editable cards.
2. **Crop**: Use the built-in cropper to fix aspect ratios.
3. **Configure**: Set copy counts and advanced layout settings (margins, borders).
4. **Process**: The backend removes backgrounds (Remove.bg), restores quality (Cloudinary), and generates a high-resolution A4 PDF.
5. **Download**: Preview the PDF in-browser and download for printing.

---

## ⚙️ API Reference

### `POST /process`
Main endpoint for generating the PDF sheet.
- **Form Data**: `image_i` (File), `copies_i` (Int), `width`, `height`, `spacing`, `border`.

---

## 📄 License
MIT License.
