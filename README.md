## Presentation Assistant API

Yüklənən PDF/DOCX fayllarından AI dəstəyi ilə təqdimatlar yaradan, redaktə edən və ixrac edən backend xidmət.

Texnologiyalar: FastAPI, slayd məzmunu üçün Google Gemini, vizuallar üçün (opsional) Hugging Face.

---

### Xüsusiyyətlər

- 🤖 PDF/DOCX-dan AI ilə slaydların yaradılması
- 🧱 Slayd strukturu: Başlıq, Giriş, Əsas slaydlar, Tövsiyələr
- ✏️ Tək slaydın və ya bütün təqdimatın redaktəsi
- 🔀 Slaydların yenidən sıralanması (drag-and-drop üçün uyğun API)
- 🖼️ Hər slayd üçün AI şəkil generasiyası (opsional)
- 📊 Qrafik dəstəyi (bar/line/pie)
- 📤 PPTX və PDF ixracı
- 💾 JSON formatında yadda saxlanma və meta məlumatlar
- 🧩 Brend şablon: `format_new.pptx`

---

### Tələblər

- Python 3.9+
- macOS/Linux/Windows

---

### Qurulum

1) Virtual mühit yaradın və aktivləşdirin

```bash
cd /Users/meh2/Desktop/Phonetics_Project/Mein_Task
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

2) Asılılıqları quraşdırın

```bash
pip install -r requirements.txt
```

3) Mühit dəyişənlərini tənzimləyin

Variant A: `.env` faylı (tövsiyə olunur)
```
GOOGLE_API_KEY=sizin_gemini_api_acariniz
# Opsional:
# HF_API_KEY=sizin_huggingface_api_acariniz
```

Variant B: terminalda export
```bash
export GOOGLE_API_KEY=sizin_gemini_api_acariniz
export HF_API_KEY=sizin_huggingface_api_acariniz   # opsional
```

Qeyd: `.env` artıq `.gitignore`-a daxildir.

---

### Serverin işə salınması

```bash
uvicorn api:app --reload
```

Swagger UI:
```
http://127.0.0.1:8000/docs
```

Sağlamlıq yoxlaması:
```bash
curl http://127.0.0.1:8000/health
```

---

### Tez start (Swagger UI)

1) Açın: `http://127.0.0.1:8000/docs`  
2) `POST /generate` bölməsini genişləndirin  
3) “Try it out” → `.pdf` və ya `.docx` faylı seçin  
4) `slide_count` (məs. 6–10) dəyərini daxil edin  
5) `include_visuals` true/false seçin  
6) `store` dəyərini true qoyun (tövsiyə)  
7) “Execute” → qaytarılan `presentation_id` dəyərini kopyalayın  

Sonra:
- Baxış: `GET /presentations/{presentation_id}`
- PPTX ixrac: `POST /presentations/{presentation_id}/export/pptx`
- PDF ixrac: `POST /presentations/{presentation_id}/export/pdf`
- Tək slaydın yenilənməsi: `POST /presentations/{presentation_id}/slides/{slide_index}`
- Yenidən sıralama: `POST /presentations/{presentation_id}/reorder`
- Bütün şəkillərin generasiyası: `POST /presentations/{presentation_id}/generate-all-images`

---

### Tez start (cURL)

Yarat:
```bash
curl -X POST "http://127.0.0.1:8000/generate" \
  -F "file=@/mütləq/yol/document.docx" \
  -F "slide_count=8" \
  -F "include_visuals=true" \
  -F "store=true"
```

Məlumatı götür:
```bash
curl "http://127.0.0.1:8000/presentations/{presentation_id}"
```

PDF ixrac:
```bash
curl -X POST "http://127.0.0.1:8000/presentations/{presentation_id}/export/pdf" \
  --output presentation.pdf
```

PPTX ixrac:
```bash
curl -X POST "http://127.0.0.1:8000/presentations/{presentation_id}/export/pptx" \
  --output presentation.pptx
```

---

### Endpoint icmalı

- `GET /health` — Xidmət statusu
- `POST /generate` — Fayldan slaydların generasiyası
- `GET /presentations` — Saxlanmış təqdimatların siyahısı
- `GET /presentations/{id}` — Təqdimatın alınması
- `PUT /presentations/{id}` — Bütün slaydların əvəzlənməsi
- `POST /presentations/{id}/slides/{index}` — Tək slaydın yenilənməsi
- `GET /presentations/{id}/slides/{index}` — Tək slaydın alınması
- `POST /presentations/{id}/reorder` — Slaydların yenidən sıralanması
- `POST /presentations/{id}/slides/{index}/image` — Slayd üçün şəkil yaradılması
- `POST /presentations/{id}/generate-all-images` — Bütün əsas slaydlar üçün şəkillər
- `POST /presentations/{id}/export/pptx` — PowerPoint ixracı
- `POST /presentations/{id}/export/pdf` — PDF ixracı
- `DELETE /presentations/{id}` — Silinmə
- `GET /templates` — Şablonların siyahısı

Ətraflı nümunələr: `API_DOCUMENTATION.md`.

---

### Slayd strukturu (AI çıxışı)

- `title` slaydı:
  - `{"type":"title","title":"..." }`
- `intro` slaydı:
  - `{"type":"intro","aim":"...","summary":"..." }`
- `main` slaydı:
  - `{"type":"main","title":"...","point1":"...","point2":"...","point3":"...","point4":"...", "visual":{ ... }}`
- `recommendation` slaydı:
  - `{"type":"recommendation","recommendation1":"...","recommendation2":"...","recommendation3":"...","recommendation4":"...","recommendation5":"..." }`

`visual.type`: `none | image | bar | line | pie`

---

### Layihə strukturu

```
.
├── api.py                     # FastAPI tətbiqi və endpointlər
├── main.py                    # Fayl oxuma (pdf/docx)
├── utils/
│   ├── prompt.py              # Gemini prompt + məzmun generasiyası
│   ├── slide.py               # PPTX generasiyası və JSON parsinq
│   ├── chart.py               # Qrafik köməkçiləri (bar/line/pie)
│   ├── storage.py             # Təhlükəsiz ID-lərlə JSON yaddaş
│   └── pdf_export.py          # ReportLab ilə PDF ixrac
├── presentations_storage/     # Saxlanmış təqdimat JSON faylları
├── format_new.pptx            # Brend şablon (zəruri)
├── requirements.txt           # Asılılıqlar
└── API_DOCUMENTATION.md       # Detallı API sənədi
```

---

### Problemlərin həlli

- Server açılmır:  
  - Kataloq düzgün olmalıdır və bu əmri işlədin: `uvicorn api:app --reload`  
  - Asılılıqları qurun: `pip install -r requirements.txt`

- `/generate` zamanı “unexpected keyword argument”:  
  - Həll edildi: köhnə imzalar üçün geriyə-uyğun çağırışlar var.  
  - Kodu yenilədikdən sonra serveri yenidən başladın.

- “File name too long”:  
  - Həll edildi: `storage.py` fayl adlarını sanitizə edir və uzunluq limitini tətbiq edir.

- “Invalid JSON format”:  
  - Həll edildi: parslayıcı markdown kod bloklarını təmizləyir və JSON-u çıxarır.

- Şəkillər yaranmır:  
  - `.env` faylında `HF_API_KEY` olmalıdır; əks halda vizuallar mətn/qrafikə düşə bilər.

- Şablon xətası:  
  - `format_new.pptx` layihə kök qovluğunda olmalıdır.

---

### Təhlükəsizlik qeydləri

- Real API açarlarını repozitoriyaya əlavə etməyin. `.env` istifadə edin.
- Gemini açarı: `GOOGLE_API_KEY` (məcburidir).
- Hugging Face açarı: `HF_API_KEY` (opsional, şəkil generasiyası üçün).

---

### Lisenziya

Bu layihə demo/daxili istifadə üçün təqdim olunur. İstehsalat üçün uyğun lisenziyanı tətbiq edin.

